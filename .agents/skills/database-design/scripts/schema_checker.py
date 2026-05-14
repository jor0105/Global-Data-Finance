#!/usr/bin/env python3
"""Schema Checker - heuristic database design triage.

Validates schema-like and migration-like files for common database design risks.

Usage:
    python schema_checker.py <project_path>

Non-goals:
    - prove actual runtime performance
    - validate complete RLS correctness
    - replace contextual review
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[attr-defined]
except (AttributeError, OSError):
    pass


EXCLUDED_PARTS = ('node_modules', '.git', 'dist', 'build', '__pycache__')
TEXT_SUFFIXES = {'.prisma', '.sql', '.py', '.ts', '.js'}
SCHEMA_PATTERNS = (
    '**/prisma/schema.prisma',
    '**/schema/*.sql',
    '**/schema/*.ts',
    '**/schema/*.js',
    '**/schema/*.py',
    '**/drizzle/*.ts',
    '**/models.py',
    '**/*schema*.sql',
)
MIGRATION_PATTERNS = (
    '**/migrations/**/*.sql',
    '**/migrations/**/*.ts',
    '**/migrations/**/*.js',
    '**/migrations/**/*.py',
    '**/*migration*.sql',
)

MONEY_NAME_RE = re.compile(
    r'(price|amount|total|balance|cost|value|rate)', re.I
)
BOOLEAN_NAME_RE = re.compile(
    r'(^is_|^has_|enabled$|active$|disabled$|archived$|verified$|deleted$)',
    re.I,
)
TIME_NAME_RE = re.compile(r'(_at$|_date$|date$|time$|timestamp$|_time$)', re.I)
OPAQUE_STRING_OK_RE = re.compile(
    r'(phone|postal|zip|cep|cpf|cnpj|sku|document|external|slug|code)',
    re.I,
)


def iter_candidate_files(project_path: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in SCHEMA_PATTERNS + MIGRATION_PATTERNS:
        files.extend(project_path.glob(pattern))

    deduped: list[Path] = []
    seen: set[Path] = set()
    for file_path in files:
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS for part in file_path.parts):
            continue
        if file_path in seen:
            continue
        seen.add(file_path)
        deduped.append(file_path)
    return sorted(deduped)


def classify_file(file_path: Path) -> str:
    name = file_path.name.lower()
    suffix = file_path.suffix.lower()
    parts = {part.lower() for part in file_path.parts}

    if suffix == '.prisma':
        return 'prisma_schema'
    if 'migrations' in parts or 'migration' in name:
        return 'migration'
    if suffix == '.sql':
        return 'sql_schema'
    if 'drizzle' in parts:
        return 'drizzle_schema'
    if name == 'models.py' or 'models' in parts:
        return 'sqlalchemy_model'
    return 'schema_source'


def normalize_sql_type(raw_type: str) -> str:
    lowered = raw_type.lower().strip()
    lowered = re.sub(r'\s+', ' ', lowered)
    return lowered


def looks_postgres_like(content: str, file_path: Path) -> bool:
    signals = (
        'timestamptz',
        'generated always as identity',
        'jsonb',
        'using gin',
        '::',
        'ilike',
        'returning ',
        'gen_random_uuid',
        'uuid_generate_v7',
    )
    lowered = content.lower()
    if any(signal in lowered for signal in signals):
        return True
    path_text = str(file_path).lower()
    return 'postgres' in path_text or 'supabase' in path_text


def line_number_for_pattern(
    content: str, pattern: str, *, flags: int = re.I
) -> int | None:
    match = re.search(pattern, content, flags)
    if not match:
        return None
    return content[: match.start()].count('\n') + 1


def add_finding(
    record: dict[str, object],
    seen: set[tuple[str, str, str]],
    *,
    summary: str,
    severity: str,
    category: str,
    evidence: str,
    recommendation: str,
    line: int | None = None,
) -> None:
    dedupe_key = (summary, category, evidence)
    if dedupe_key in seen:
        return
    seen.add(dedupe_key)
    record['issues'].append(summary)
    record['findings'].append(
        {
            'summary': summary,
            'severity': severity,
            'category': category,
            'evidence': evidence,
            'recommendation': recommendation,
            'line': line,
        }
    )


def split_columns(raw_columns: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in raw_columns:
        if char == '(':
            depth += 1
        elif char == ')' and depth > 0:
            depth -= 1
        if char == ',' and depth == 0:
            piece = ''.join(current).strip()
            if piece:
                parts.append(piece)
            current = []
            continue
        current.append(char)
    tail = ''.join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def parse_sql_table_blocks(content: str) -> list[dict[str, object]]:
    tables: list[dict[str, object]] = []
    for match in re.finditer(
        r'create\s+table\s+([\"`\[]?[\w.]+[\"`\]]?)\s*\((.*?)\);',
        content,
        re.I | re.S,
    ):
        table_name = match.group(1).strip('"`[]')
        body = match.group(2)
        columns: list[dict[str, str]] = []
        has_primary_key = False
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(',')
            if not line or line.startswith('--'):
                continue
            lowered = line.lower()
            if lowered.startswith(
                (
                    'constraint ',
                    'primary key',
                    'foreign key',
                    'unique ',
                    'check ',
                )
            ):
                if 'primary key' in lowered:
                    has_primary_key = True
                continue
            column_match = re.match(
                r'^\"?([A-Za-z_][\w$]*)\"?\s+([A-Za-z_][\w]*(?:\s*\([^)]*\))?(?:\s+with(?:out)?\s+time\s+zone)?)',
                line,
                re.I,
            )
            if not column_match:
                continue
            column_name = column_match.group(1)
            raw_type = column_match.group(2)
            if 'primary key' in lowered:
                has_primary_key = True
            columns.append(
                {
                    'name': column_name,
                    'type': normalize_sql_type(raw_type),
                    'line': line,
                }
            )
        tables.append(
            {
                'name': table_name,
                'body': body,
                'columns': columns,
                'has_primary_key': has_primary_key,
            }
        )
    return tables


def extract_sql_indexes(content: str) -> list[dict[str, object]]:
    indexes: list[dict[str, object]] = []
    for match in re.finditer(
        r'create\s+(?:unique\s+)?index\s+[\w\".]+\s+on\s+([\"`\[]?[\w.]+[\"`\]]?)'
        r'(?:\s+using\s+\w+)?\s*\((.*?)\)',
        content,
        re.I | re.S,
    ):
        table_name = match.group(1).strip('"`[]')
        column_list = [
            re.sub(r'\s+(asc|desc)\b', '', piece.strip(), flags=re.I).strip(
                '"`[]'
            )
            for piece in split_columns(match.group(2))
        ]
        indexes.append({'table': table_name, 'columns': column_list})
    return indexes


def extract_prisma_models(content: str) -> list[dict[str, object]]:
    models: list[dict[str, object]] = []
    for match in re.finditer(r'model\s+(\w+)\s*{(.*?)}', content, re.S):
        model_name = match.group(1)
        body = match.group(2)
        fields: list[dict[str, str]] = []
        has_primary_key = False
        indexed_columns: set[str] = set()
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line or line.startswith('//'):
                continue
            if line.startswith('@@index'):
                index_match = re.search(r'\[([^\]]+)\]', line)
                if index_match:
                    for piece in split_columns(index_match.group(1)):
                        indexed_columns.add(piece.strip().strip('"'))
                continue
            if line.startswith('@@unique'):
                continue
            field_match = re.match(r'^(\w+)\s+([^\s]+)(.*)$', line)
            if not field_match:
                continue
            field_name = field_match.group(1)
            field_type = field_match.group(2)
            remainder = field_match.group(3)
            if '@id' in remainder:
                has_primary_key = True
            if '@unique' in remainder:
                indexed_columns.add(field_name)
            fields.append(
                {
                    'name': field_name,
                    'type': field_type,
                    'raw': line,
                }
            )
        models.append(
            {
                'name': model_name,
                'body': body,
                'fields': fields,
                'has_primary_key': has_primary_key,
                'indexed_columns': indexed_columns,
            }
        )
    return models


def check_data_type_semantics(
    record: dict[str, object],
    seen: set[tuple[str, str, str]],
    *,
    column_name: str,
    raw_type: str,
    evidence: str,
    line_number: int | None,
) -> None:
    normalized = normalize_sql_type(raw_type)
    column_lower = column_name.lower()

    string_like = any(
        token in normalized for token in ('string', 'text', 'varchar', 'char')
    )
    float_like = any(
        token in normalized for token in ('float', 'real', 'double')
    )
    timestamp_without_tz = normalized == 'timestamp' or normalized.startswith(
        'timestamp '
    )
    temporal_string_like = string_like

    if MONEY_NAME_RE.search(column_name):
        if string_like:
            add_finding(
                record,
                seen,
                summary=f'{column_name}: numeric business value stored as string-like type',
                severity='high',
                category='schema/data-type',
                evidence=evidence,
                recommendation='Use numeric/decimal or integer-in-smallest-unit for arithmetic values.',
                line=line_number,
            )
        elif float_like:
            add_finding(
                record,
                seen,
                summary=f'{column_name}: monetary-looking field stored as floating-point type',
                severity='high',
                category='schema/data-type',
                evidence=evidence,
                recommendation='Use numeric/decimal for money or exact rates to avoid rounding drift.',
                line=line_number,
            )

    if BOOLEAN_NAME_RE.search(column_lower) and string_like:
        add_finding(
            record,
            seen,
            summary=f'{column_name}: boolean-looking field stored as string-like type',
            severity='medium',
            category='schema/data-type',
            evidence=evidence,
            recommendation='Use a boolean or constrained enum instead of free-form text.',
            line=line_number,
        )

    if TIME_NAME_RE.search(column_lower):
        if temporal_string_like:
            add_finding(
                record,
                seen,
                summary=f'{column_name}: temporal-looking field stored as string-like type',
                severity='medium',
                category='schema/data-type',
                evidence=evidence,
                recommendation='Use a native date/time type so comparisons, ranges and parsing stay reliable.',
                line=line_number,
            )
        elif timestamp_without_tz and column_lower.endswith('_at'):
            add_finding(
                record,
                seen,
                summary=f'{column_name}: timestamp field may be missing timezone semantics',
                severity='low',
                category='schema/data-type',
                evidence=evidence,
                recommendation='Confirm whether an absolute instant should use a timezone-aware timestamp type.',
                line=line_number,
            )

    if (
        column_lower == 'id'
        and string_like
        and not OPAQUE_STRING_OK_RE.search(column_lower)
    ):
        id_signals = (
            'uuid',
            'ulid',
            'cuid',
            'ksuid',
            'gen_random_uuid',
            'uuid_generate_v7',
        )
        if not any(signal in evidence.lower() for signal in id_signals):
            add_finding(
                record,
                seen,
                summary='id: primary identifier appears to be arbitrary string-like type',
                severity='low',
                category='schema/data-type',
                evidence=evidence,
                recommendation='Confirm that the opaque string identifier is intentional and documented.',
                line=line_number,
            )


def analyze_prisma_schema(file_path: Path, content: str) -> dict[str, object]:
    record: dict[str, object] = {
        'file': file_path.name,
        'path': str(file_path),
        'type': 'prisma_schema',
        'issues': [],
        'findings': [],
    }
    seen: set[tuple[str, str, str]] = set()
    models = extract_prisma_models(content)

    for model in models:
        model_name = str(model['name'])
        if not model['has_primary_key']:
            add_finding(
                record,
                seen,
                summary=f'{model_name}: model may be missing an explicit primary key',
                severity='high',
                category='schema/pk',
                evidence=f'model {model_name} without @id',
                recommendation='Define an explicit primary key before relying on relations, ownership or indexing.',
                line=line_number_for_pattern(
                    content, rf'model\s+{re.escape(model_name)}\b'
                ),
            )

        if model_name and model_name[0].islower():
            add_finding(
                record,
                seen,
                summary=f'{model_name}: model name is not PascalCase',
                severity='low',
                category='style/naming',
                evidence=f'model {model_name}',
                recommendation='Use PascalCase for model names to match common Prisma conventions.',
                line=line_number_for_pattern(
                    content, rf'model\s+{re.escape(model_name)}\b'
                ),
            )

        indexed_columns = set(model['indexed_columns'])
        for field in model['fields']:
            field_name = str(field['name'])
            field_type = str(field['type'])
            raw_line = str(field['raw'])
            line_no = line_number_for_pattern(
                content, rf'^\s*{re.escape(field_name)}\s+', flags=re.I | re.M
            )
            check_data_type_semantics(
                record,
                seen,
                column_name=field_name,
                raw_type=field_type,
                evidence=raw_line,
                line_number=line_no,
            )

            lowered_name = field_name.lower()
            if (
                (lowered_name.endswith('id') or lowered_name.endswith('_id'))
                and field_name != 'id'
                and field_name not in indexed_columns
            ):
                add_finding(
                    record,
                    seen,
                    summary=f'{model_name}.{field_name}: foreign-key-looking field lacks obvious index',
                    severity='medium',
                    category='schema/index',
                    evidence=raw_line,
                    recommendation='Confirm an @@index/@@unique exists for frequent FK lookup, joins and cascades.',
                    line=line_no,
                )

    return record


def analyze_sql_like_file(
    file_path: Path, content: str, file_type: str
) -> dict[str, object]:
    record: dict[str, object] = {
        'file': file_path.name,
        'path': str(file_path),
        'type': file_type,
        'issues': [],
        'findings': [],
    }
    seen: set[tuple[str, str, str]] = set()
    tables = parse_sql_table_blocks(content)
    indexes = extract_sql_indexes(content)
    indexes_by_table: dict[str, list[list[str]]] = {}
    for item in indexes:
        indexes_by_table.setdefault(str(item['table']), []).append(
            list(item['columns'])
        )

    for table in tables:
        table_name = str(table['name'])
        table_line = line_number_for_pattern(
            content, rf'create\s+table\s+{re.escape(table_name)}\b'
        )
        if not table['has_primary_key']:
            add_finding(
                record,
                seen,
                summary=f'{table_name}: table may be missing an explicit primary key',
                severity='high',
                category='schema/pk',
                evidence=f'CREATE TABLE {table_name}',
                recommendation='Add a primary key before layering ownership, joins and migrations on top.',
                line=table_line,
            )

        indexed_columns = indexes_by_table.get(table_name, [])
        for column in table['columns']:
            column_name = str(column['name'])
            raw_type = str(column['type'])
            raw_line = str(column['line'])
            line_no = line_number_for_pattern(
                content,
                rf'^\s*\"?{re.escape(column_name)}\"?\s+',
                flags=re.I | re.M,
            )
            check_data_type_semantics(
                record,
                seen,
                column_name=column_name,
                raw_type=raw_type,
                evidence=raw_line,
                line_number=line_no,
            )

            lowered_line = raw_line.lower()
            if ' references ' in lowered_line:
                column_has_index = any(
                    column_name in index_columns
                    for index_columns in indexed_columns
                )
                if not column_has_index:
                    add_finding(
                        record,
                        seen,
                        summary=f'{table_name}.{column_name}: foreign key lacks obvious supporting index',
                        severity='medium',
                        category='schema/index',
                        evidence=raw_line,
                        recommendation='Add an index for FK lookup, joins and cascading operations when this path is active.',
                        line=line_no,
                    )

    if file_type == 'migration':
        destructive_patterns = {
            r'\bdrop\s+column\b': 'Dropping a column is destructive and often needs phased rollout.',
            r'\bdrop\s+table\b': 'Dropping a table is destructive and often needs a delayed cleanup window.',
        }
        for pattern, recommendation in destructive_patterns.items():
            if re.search(pattern, content, re.I):
                add_finding(
                    record,
                    seen,
                    summary='Migration contains explicit destructive operation',
                    severity='high',
                    category='migration/risk',
                    evidence=re.search(pattern, content, re.I).group(0),  # type: ignore[union-attr]
                    recommendation=recommendation,
                    line=line_number_for_pattern(content, pattern),
                )

        if re.search(
            r'alter\s+table.+alter\s+column.+set\s+not\s+null',
            content,
            re.I | re.S,
        ):
            add_finding(
                record,
                seen,
                summary='Migration enforces NOT NULL in-place',
                severity='medium',
                category='migration/risk',
                evidence='ALTER COLUMN ... SET NOT NULL',
                recommendation='Confirm the column was backfilled and validated before enforcing NOT NULL.',
                line=line_number_for_pattern(
                    content,
                    r'alter\s+table.+alter\s+column.+set\s+not\s+null',
                    flags=re.I | re.S,
                ),
            )

        if re.search(r'\brename\s+column\b|\brename\s+to\b', content, re.I):
            add_finding(
                record,
                seen,
                summary='Migration performs rename in a single step',
                severity='medium',
                category='migration/compatibility',
                evidence='RENAME COLUMN/TO',
                recommendation='Confirm callers, backfill and rollback implications before relying on a one-step rename.',
                line=line_number_for_pattern(
                    content, r'\brename\s+column\b|\brename\s+to\b'
                ),
            )

        if looks_postgres_like(content, file_path):
            for match in re.finditer(
                r'create\s+(?:unique\s+)?index\b(?!\s+concurrently)',
                content,
                re.I,
            ):
                add_finding(
                    record,
                    seen,
                    summary='Postgres-like migration creates index without CONCURRENTLY marker',
                    severity='medium',
                    category='migration/index-build',
                    evidence=match.group(0),
                    recommendation='Confirm blocking index creation is acceptable or use CONCURRENTLY when the runtime path is hot.',
                    line=content[: match.start()].count('\n') + 1,
                )

    analyze_generic_code_patterns(record, seen, file_path, content)
    return record


def extract_code_field_candidates(line: str) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []

    sql_like = re.match(
        r'^\s*"?([A-Za-z_][\w$]*)"?\s+([A-Za-z_][\w]*(?:\s*\([^)]*\))?(?:\s+with(?:out)?\s+time\s+zone)?)',
        line,
        re.I,
    )
    if sql_like:
        candidates.append((sql_like.group(1), sql_like.group(2)))

    sqlalchemy = re.match(
        r'^\s*([A-Za-z_][\w$]*)\s*=\s*Column\(\s*([A-Za-z_][\w]*(?:\([^)]*\))?)',
        line,
        re.I,
    )
    if sqlalchemy:
        candidates.append((sqlalchemy.group(1), sqlalchemy.group(2)))

    drizzle = re.match(
        r'^\s*([A-Za-z_][\w$]*)\s*:\s*([A-Za-z_][\w$]*)\(',
        line,
        re.I,
    )
    if drizzle:
        candidates.append((drizzle.group(1), drizzle.group(2)))

    named_function = re.search(
        r"([A-Za-z_][\w$]*)\(\s*['\"]([A-Za-z_][\w$]*)['\"]",
        line,
        re.I,
    )
    if named_function:
        candidates.append((named_function.group(2), named_function.group(1)))

    return candidates


def analyze_generic_code_patterns(
    record: dict[str, object],
    seen: set[tuple[str, str, str]],
    file_path: Path,
    content: str,
) -> None:
    if file_path.suffix.lower() in {'.prisma', '.sql'}:
        return

    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith(('//', '--', '#')):
            continue
        for field_name, field_type in extract_code_field_candidates(line):
            check_data_type_semantics(
                record,
                seen,
                column_name=field_name,
                raw_type=field_type,
                evidence=line,
                line_number=line_number,
            )


def analyze_file(file_path: Path) -> dict[str, object]:
    file_type = classify_file(file_path)
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except OSError as exc:
        return {
            'file': file_path.name,
            'path': str(file_path),
            'type': file_type,
            'issues': [f'Read error: {exc}'],
            'findings': [
                {
                    'summary': 'File could not be read',
                    'severity': 'high',
                    'category': 'parser/io',
                    'evidence': str(exc),
                    'recommendation': 'Fix file access or encoding before relying on this review.',
                    'line': None,
                }
            ],
        }

    if file_type == 'prisma_schema':
        return analyze_prisma_schema(file_path, content)
    return analyze_sql_like_file(file_path, content, file_type)


def build_summary(records: list[dict[str, object]]) -> dict[str, object]:
    severity_counter: Counter[str] = Counter()
    category_counter: Counter[str] = Counter()
    type_counter: Counter[str] = Counter()
    for record in records:
        type_counter.update([str(record['type'])])
        for finding in record.get('findings', []):
            if not isinstance(finding, dict):
                continue
            severity_counter.update([str(finding.get('severity', 'unknown'))])
            category_counter.update([str(finding.get('category', 'unknown'))])
    return {
        'files_by_type': dict(type_counter),
        'findings_by_severity': dict(severity_counter),
        'findings_by_category': dict(category_counter),
    }


def print_console_summary(
    project_path: Path, records: list[dict[str, object]]
) -> None:
    print(f'\n{"=" * 60}')
    print('[SCHEMA CHECKER] Database design triage')
    print(f'{"=" * 60}')
    print(f'Project: {project_path}')
    print(f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('-' * 60)
    print(f'Files checked: {len(records)}')

    if not records:
        print('No schema or migration candidates found.')
        return

    for record in records:
        findings = record.get('findings', [])
        if not findings:
            continue
        print(f'\n{record["file"]} ({record["type"]}):')
        for finding in findings[:5]:
            if not isinstance(finding, dict):
                continue
            severity = str(finding.get('severity', 'unknown')).upper()
            category = str(finding.get('category', 'unknown'))
            summary = str(finding.get('summary', ''))
            print(f'  - [{severity}] {category}: {summary}')
        if len(findings) > 5:
            print(f'  ... and {len(findings) - 5} more findings')


def main() -> int:
    project_path = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    candidate_files = iter_candidate_files(project_path)
    records = [analyze_file(file_path) for file_path in candidate_files]
    total_findings = sum(len(record.get('findings', [])) for record in records)
    summary = build_summary(records)

    severe_findings = 0
    for record in records:
        for finding in record.get('findings', []):
            if isinstance(finding, dict) and finding.get('severity') in {
                'high',
                'critical',
            }:
                severe_findings += 1

    passed = severe_findings == 0
    print_console_summary(project_path, records)

    output = {
        'script': 'schema_checker',
        'project': str(project_path),
        'schemas_checked': len(candidate_files),
        'issues_found': total_findings,
        'passed': passed,
        'issues': records,
        'summary': summary,
    }

    if not candidate_files:
        output['message'] = 'No schema files found'

    print('\n' + json.dumps(output, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

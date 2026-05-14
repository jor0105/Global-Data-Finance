#!/usr/bin/env python3
"""API Validator - heuristic checks for API contracts and handlers.

This script is intentionally conservative: it highlights likely issues and
project-wide patterns, but it does not replace contextual review.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[attr-defined]
except (AttributeError, OSError):
    pass


EXCLUDED_PARTS = ('node_modules', '.git', 'dist', 'build', '__pycache__')
VALID_HTTP_METHODS = {
    'get',
    'post',
    'put',
    'patch',
    'delete',
    'options',
    'head',
}
MUTATING_METHODS = {'post', 'put', 'patch', 'delete'}
API_PATTERNS = (
    '**/*api*.ts',
    '**/*api*.js',
    '**/*api*.py',
    '**/routes/*.ts',
    '**/routes/*.js',
    '**/routes/*.py',
    '**/routers/*.ts',
    '**/routers/*.py',
    '**/controllers/*.ts',
    '**/controllers/*.js',
    '**/controllers/*.py',
    '**/endpoints/*.ts',
    '**/endpoints/*.py',
    '**/*.openapi.json',
    '**/*.openapi.yaml',
    '**/*.openapi.yml',
    '**/swagger.json',
    '**/swagger.yaml',
    '**/swagger.yml',
    '**/openapi.json',
    '**/openapi.yaml',
    '**/openapi.yml',
)


def iter_api_files(project_path: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in API_PATTERNS:
        files.extend(project_path.glob(pattern))

    deduped: list[Path] = []
    seen: set[Path] = set()
    for file_path in files:
        if any(part in EXCLUDED_PARTS for part in file_path.parts):
            continue
        if file_path in seen:
            continue
        seen.add(file_path)
        deduped.append(file_path)
    return sorted(deduped)


def has_any_pattern(
    content: str,
    patterns: Iterable[str],
    *,
    ignore_case: bool = False,
) -> bool:
    flags = re.I if ignore_case else 0
    return any(re.search(pattern, content, flags) for pattern in patterns)


def add_issue(issues: list[str], level: str, message: str) -> None:
    issues.append(f'{level} {message}')


def detect_path_params(path: str) -> list[str]:
    return re.findall(r'{([^}/]+)}', path)


def operation_name_hints(path: str, details: dict[str, object]) -> str:
    pieces = [path]
    summary = details.get('summary')
    if isinstance(summary, str):
        pieces.append(summary)
    description = details.get('description')
    if isinstance(description, str):
        pieces.append(description)
    return ' '.join(pieces).lower()


def extract_parameter_names(parameters: object) -> set[str]:
    names: set[str] = set()
    if not isinstance(parameters, list):
        return names
    for item in parameters:
        if not isinstance(item, dict):
            continue
        name = item.get('name')
        if isinstance(name, str):
            names.add(name)
    return names


def has_security(details: dict[str, object], spec: dict[str, object]) -> bool:
    if 'security' in details:
        return True
    top_level_security = spec.get('security')
    if isinstance(top_level_security, list) and top_level_security:
        return True
    components = spec.get('components')
    if isinstance(components, dict):
        schemes = components.get('securitySchemes')
        if isinstance(schemes, dict) and schemes:
            return True
    return False


def response_codes(details: dict[str, object]) -> set[str]:
    responses = details.get('responses')
    if not isinstance(responses, dict):
        return set()
    return {str(code) for code in responses}


def has_response_header(
    responses: object,
    response_code: str,
    header_name: str,
) -> bool:
    if not isinstance(responses, dict):
        return False
    response = responses.get(response_code)
    if not isinstance(response, dict):
        return False
    headers = response.get('headers')
    if not isinstance(headers, dict):
        return False
    return header_name in headers


def check_openapi_text(file_path: Path, content: str) -> dict[str, object]:
    issues: list[str] = []
    passed: list[str] = []

    if re.search(r'^\s*(openapi|swagger)\s*:', content, re.M):
        passed.append('[OK] OpenAPI/Swagger version defined')
    else:
        add_issue(issues, '[X]', 'No OpenAPI version found')

    if re.search(r'^\s*paths\s*:', content, re.M):
        passed.append('[OK] Paths section exists')
    else:
        add_issue(issues, '[X]', 'No paths defined')

    if re.search(r'^\s*(components|definitions)\s*:', content, re.M):
        passed.append('[OK] Schema components defined')

    if re.search(r'^\s*securitySchemes\s*:', content, re.M):
        passed.append('[OK] Security schemes declared')
    else:
        add_issue(
            issues, '[!]', 'No security schemes found in text-based spec'
        )

    if re.search(r'Idempotency-Key', content):
        passed.append('[OK] Idempotency header documented')

    if re.search(r'ETag|If-Match|If-None-Match', content):
        passed.append('[OK] Cache/concurrency headers documented')

    if re.search(r'\b202\b|Accepted', content):
        passed.append('[OK] Async operation markers documented')

    if re.search(r'Deprecation|Sunset|deprecated', content):
        passed.append('[OK] Lifecycle/deprecation markers documented')

    if re.search(r'webhooks\s*:|callback', content, re.I):
        passed.append('[OK] Webhook/callback markers documented')

    return {
        'file': str(file_path),
        'passed': passed,
        'issues': issues,
        'type': 'openapi',
    }


def check_openapi_json(file_path: Path, content: str) -> dict[str, object]:
    issues: list[str] = []
    passed: list[str] = []

    try:
        spec = json.loads(content)
    except (json.JSONDecodeError, ValueError) as exc:
        add_issue(issues, '[X]', f'Parse error: {exc}')
        return {
            'file': str(file_path),
            'passed': passed,
            'issues': issues,
            'type': 'openapi',
        }

    if 'openapi' in spec or 'swagger' in spec:
        passed.append('[OK] OpenAPI version defined')
    else:
        add_issue(issues, '[X]', 'No OpenAPI version defined')

    info = spec.get('info', {})
    if isinstance(info, dict):
        if 'title' in info:
            passed.append('[OK] API title defined')
        else:
            add_issue(issues, '[!]', 'API title missing')
        if 'version' in info:
            passed.append('[OK] API version defined')
        else:
            add_issue(issues, '[!]', 'API version missing')
        if 'description' not in info:
            add_issue(issues, '[!]', 'API description missing')

    components = spec.get('components')
    if isinstance(components, dict):
        schemas = components.get('schemas')
        if isinstance(schemas, dict) and schemas:
            passed.append('[OK] Schema components defined')
        schemes = components.get('securitySchemes')
        if isinstance(schemes, dict) and schemes:
            passed.append('[OK] Security schemes declared')
        else:
            add_issue(issues, '[!]', 'No security schemes declared')

    if isinstance(spec.get('webhooks'), dict):
        passed.append('[OK] Webhooks section defined')

    paths = spec.get('paths', {})
    if not isinstance(paths, dict) or not paths:
        add_issue(issues, '[X]', 'No paths defined')
        return {
            'file': str(file_path),
            'passed': passed,
            'issues': issues,
            'type': 'openapi',
        }

    passed.append(f'[OK] {len(paths)} endpoints defined')

    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue

        path_params = detect_path_params(path)
        path_level_params = extract_parameter_names(methods.get('parameters'))

        for method, details in methods.items():
            if method not in VALID_HTTP_METHODS or not isinstance(
                details, dict
            ):
                continue

            label = f'{method.upper()} {path}'
            hints = operation_name_hints(path, details)
            codes = response_codes(details)
            op_params = path_level_params | extract_parameter_names(
                details.get('parameters')
            )

            if 'responses' not in details:
                add_issue(issues, '[X]', f'{label}: No responses defined')
            if 'summary' not in details and 'description' not in details:
                add_issue(issues, '[!]', f'{label}: No summary/description')
            if not has_security(details, spec):
                add_issue(issues, '[!]', f'{label}: No security marker found')
            if not any(code.startswith(('4', 'default')) for code in codes):
                add_issue(
                    issues,
                    '[!]',
                    f'{label}: No explicit client/default error response',
                )

            if method == 'post' and not codes.intersection(
                {'200', '201', '202', '204'}
            ):
                add_issue(
                    issues,
                    '[!]',
                    f'{label}: POST lacks 200/201/202/204 response',
                )
            if method in {'put', 'patch', 'delete'} and not codes.intersection(
                {'200', '202', '204'}
            ):
                add_issue(
                    issues,
                    '[!]',
                    f'{label}: Mutating operation lacks 200/202/204 response',
                )

            for param_name in path_params:
                if param_name not in op_params:
                    add_issue(
                        issues,
                        '[X]',
                        f'{label}: Missing path parameter declaration for {{{param_name}}}',
                    )

            if (
                method in MUTATING_METHODS
                and method != 'delete'
                and 'requestBody' not in details
            ):
                add_issue(
                    issues,
                    '[!]',
                    f'{label}: Mutating operation without requestBody',
                )

            if method == 'post' and re.search(
                r'(create|payment|charge|transfer|export|job|stream|key)',
                hints,
            ):
                idempotency_names = {name.lower() for name in op_params}
                if 'idempotency-key' in idempotency_names:
                    passed.append(
                        f'[OK] {label}: Idempotency header documented'
                    )
                elif '202' not in codes:
                    add_issue(
                        issues,
                        '[!]',
                        f'{label}: Critical-looking POST without Idempotency-Key or async 202 contract',
                    )

            if method in {'put', 'patch', 'delete'}:
                responses = details.get('responses')
                if (
                    has_response_header(responses, '200', 'ETag')
                    or '412' in codes
                ):
                    passed.append(
                        f'[OK] {label}: Concurrency/precondition markers documented'
                    )
                elif re.search(
                    r'(watchlist|portfolio|workspace|report|settings|profile)',
                    hints,
                ):
                    add_issue(
                        issues,
                        '[!]',
                        f'{label}: Mutable resource without obvious ETag/412 precondition markers',
                    )

            if re.search(
                r'(export|import|generate|sync|backfill|report)', hints
            ):
                if '202' in codes:
                    passed.append(
                        f'[OK] {label}: Async 202 contract documented'
                    )
                elif method == 'post':
                    add_issue(
                        issues,
                        '[!]',
                        f'{label}: Long-running looking POST without 202 Accepted contract',
                    )

            if re.search(r'webhook', hints):
                signature_names = {name.lower() for name in op_params}
                if any(
                    name in signature_names
                    for name in {
                        'x-signature',
                        'x-webhook-signature',
                        'authorization',
                    }
                ):
                    passed.append(
                        f'[OK] {label}: Webhook signature/auth header documented'
                    )
                else:
                    add_issue(
                        issues,
                        '[!]',
                        f'{label}: Webhook without obvious signature/auth header',
                    )

            if details.get('deprecated') is True:
                passed.append(f'[OK] {label}: Deprecated marker present')

    return {
        'file': str(file_path),
        'passed': passed,
        'issues': issues,
        'type': 'openapi',
    }


def check_openapi_spec(file_path: Path) -> dict[str, object]:
    try:
        content = file_path.read_text(encoding='utf-8')
    except OSError as exc:
        return {
            'file': str(file_path),
            'passed': [],
            'issues': [f'[X] Read error: {exc}'],
            'type': 'openapi',
        }

    if file_path.suffix == '.json':
        return check_openapi_json(file_path, content)

    return check_openapi_text(file_path, content)


def check_api_code(file_path: Path) -> dict[str, object]:
    issues: list[str] = []
    passed: list[str] = []

    try:
        content = file_path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as exc:
        return {
            'file': str(file_path),
            'passed': passed,
            'issues': [f'[X] Read error: {exc}'],
            'type': 'code',
        }

    error_boundary_patterns = (
        r'@app\.exception_handler',
        r'setErrorHandler',
        r'errorHandler',
        r'exception_handler',
        r'TRPCError',
        r'formatError',
        r'problem\s*detail',
        r'problem\+json',
    )
    if has_any_pattern(content, error_boundary_patterns, ignore_case=True):
        passed.append('[OK] Structured error boundary detected')
    else:
        add_issue(issues, '[!]', 'No structured error boundary detected')

    local_try_catch_patterns = (
        r'try\s*{',
        r'try:',
        r'\.catch\(',
        r'except\s+',
        r'catch\s*\(',
    )
    if has_any_pattern(content, local_try_catch_patterns):
        add_issue(
            issues,
            '[!]',
            'Route-local try/catch detected; confirm business errors are centralized and sanitized',
        )

    status_patterns = (
        r'status\s*\(\s*\d{3}\s*\)',
        r'statusCode\s*[=:]\s*\d{3}',
        r'HttpStatus\.',
        r'status_code\s*=\s*\d{3}',
        r'\.status\(\d{3}\)',
        r'res\.status\(',
        r'TRPCError\(\s*{\s*code:\s*"',
    )
    if has_any_pattern(content, status_patterns):
        passed.append('[OK] Explicit status or framework error codes used')
    else:
        add_issue(
            issues,
            '[!]',
            'No explicit status or framework error codes detected',
        )

    validation_patterns = (
        r'validate',
        r'schema',
        r'zod',
        r'joi',
        r'yup',
        r'pydantic',
        r'marshmallow',
        r'@Body\(',
        r'@Query\(',
        r'TypedDict',
    )
    if has_any_pattern(content, validation_patterns, ignore_case=True):
        passed.append('[OK] Input validation detected')
    else:
        add_issue(issues, '[!]', 'No input validation detected')

    auth_patterns = (
        r'auth',
        r'jwt',
        r'bearer',
        r'token',
        r'middleware',
        r'guard',
        r'@Authenticated',
        r'protectedProcedure',
        r'Depends\(',
        r'current_user',
        r'session',
        r'api[_-]?key',
    )
    has_auth = has_any_pattern(content, auth_patterns, ignore_case=True)
    if has_auth:
        passed.append('[OK] Authentication/authorization markers detected')
    else:
        add_issue(
            issues, '[!]', 'No authentication/authorization markers detected'
        )

    rate_patterns = (r'rateLimit', r'throttle', r'rate.?limit', r'Retry-After')
    if has_any_pattern(content, rate_patterns, ignore_case=True):
        passed.append('[OK] Rate limiting markers detected')

    envelope_patterns = (
        r'"data"\s*:',
        r'"meta"\s*:',
        r'"type"\s*:',
        r'"title"\s*:',
        r'"detail"\s*:',
        r'extensions\s*:',
        r'problem\+json',
    )
    if has_any_pattern(content, envelope_patterns):
        passed.append('[OK] Structured response markers detected')
    else:
        add_issue(
            issues, '[!]', 'No obvious structured response markers detected'
        )

    query_contract_patterns = (
        r'\bpage\b',
        r'\bper_page\b',
        r'\bcursor\b',
        r'\bsort\b',
        r'filter\[',
        r'\binclude\b',
        r'fields\[',
    )
    if has_any_pattern(content, query_contract_patterns):
        passed.append('[OK] Query/pagination contract markers detected')

    idempotency_patterns = (
        r'Idempotency-Key',
        r'idempotenc',
        r'upsert',
        r'deduplic',
    )
    if has_any_pattern(content, idempotency_patterns, ignore_case=True):
        passed.append('[OK] Idempotency or deduplication markers detected')

    concurrency_patterns = (
        r'ETag',
        r'If-Match',
        r'If-None-Match',
        r'Precondition',
        r'\b412\b',
        r'\b304\b',
        r'\bversion\b',
        r'optimistic',
    )
    has_concurrency = has_any_pattern(
        content, concurrency_patterns, ignore_case=True
    )
    if has_concurrency:
        passed.append('[OK] Cache/concurrency markers detected')

    async_patterns = (
        r'\b202\b',
        r'Accepted',
        r'\bjob\b',
        r'\bqueue\b',
        r'enqueue',
        r'background',
        r'celery',
        r'asyncio\.create_task',
        r'SSE',
        r'EventSource',
        r'stream',
    )
    has_async = has_any_pattern(content, async_patterns, ignore_case=True)
    if has_async:
        passed.append('[OK] Async/streaming markers detected')

    lifecycle_patterns = (
        r'\bdeprecated\b',
        r'\bDeprecation\b',
        r'\bSunset\b',
        r'/v\d+/',
        r'version',
    )
    if has_any_pattern(content, lifecycle_patterns, ignore_case=True):
        passed.append('[OK] Lifecycle/versioning markers detected')

    webhook_patterns = (
        r'webhook',
        r'signature',
        r'hmac',
        r'event[_-]?id',
        r'timestamp',
        r'replay',
    )
    mentions_webhook = has_any_pattern(
        content, (r'webhook',), ignore_case=True
    )
    if has_any_pattern(content, webhook_patterns, ignore_case=True):
        passed.append('[OK] Webhook-related markers detected')
    elif mentions_webhook:
        add_issue(
            issues,
            '[!]',
            'Webhook mentioned without obvious signature/replay/dedup markers',
        )

    if has_auth and has_any_pattern(
        content,
        (r'req\.body\.userId', r'input\.userId', r"body\[['\"]user_id['\"]\]"),
        ignore_case=True,
    ):
        add_issue(
            issues,
            '[!]',
            'Client-controlled user identity marker detected; confirm authz comes from token/session context',
        )

    if has_any_pattern(
        content,
        (r'ownerId\s*:\s*input\.userId', r'owner_id\s*[:=]\s*.*user_id'),
        ignore_case=True,
    ):
        add_issue(
            issues,
            '[X]',
            'Ownership appears tied to client-provided user id; this is a common BOLA anti-pattern',
        )

    if has_any_pattern(
        content,
        (r"Access-Control-Allow-Origin\s*[:=]\s*['\"]\*['\"]",),
        ignore_case=True,
    ):
        if has_any_pattern(
            content,
            (r'Allow-Credentials\s*[:=]\s*true', r'credentials\s*:\s*true'),
            ignore_case=True,
        ):
            add_issue(
                issues,
                '[X]',
                'Wildcard CORS appears combined with credentials',
            )
        else:
            add_issue(
                issues,
                '[!]',
                'Wildcard CORS marker detected; confirm proxy/topology does not make this unnecessary',
            )

    if has_any_pattern(
        content,
        (
            r'throw new Error\(',
            r'raise Exception\(',
            r'detail\s*=\s*str\(',
            r'traceback',
        ),
        ignore_case=True,
    ):
        add_issue(
            issues,
            '[!]',
            'Raw exception/detail markers detected; confirm errors are sanitized',
        )

    mutating_route_patterns = (
        r'\bPATCH\b',
        r'\bPUT\b',
        r'\bDELETE\b',
        r'\.patch\(',
        r'\.put\(',
        r'\.delete\(',
        r'@router\.patch',
        r'@router\.put',
        r'@router\.delete',
    )
    if (
        has_any_pattern(content, mutating_route_patterns)
        and not has_concurrency
    ):
        add_issue(
            issues,
            '[!]',
            'Mutating route detected without obvious ETag/version/precondition markers; confirm lost updates are acceptable',
        )

    long_running_patterns = (
        r'export',
        r'report',
        r'backfill',
        r'generate',
        r'provider',
        r'stream',
    )
    if (
        has_any_pattern(content, long_running_patterns, ignore_case=True)
        and not has_async
    ):
        add_issue(
            issues,
            '[!]',
            'Long-running looking flow without obvious async/job/streaming markers',
        )

    return {
        'file': str(file_path),
        'passed': passed,
        'issues': issues,
        'type': 'code',
    }


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else '.')

    print('\n' + '=' * 60)
    print('  API VALIDATOR - Heuristic API Review')
    print('=' * 60 + '\n')

    api_files = iter_api_files(target)
    if not api_files:
        print('[!] No API files found.')
        print(
            '   Looking for: routes/, routers/, controllers/, api/, openapi.json/yaml'
        )
        return 0

    results = []
    for file_path in api_files[:25]:
        lower_name = file_path.name.lower()
        if 'openapi' in lower_name or 'swagger' in lower_name:
            results.append(check_openapi_spec(file_path))
        else:
            results.append(check_api_code(file_path))

    total_critical = 0
    total_warnings = 0
    total_passed = 0

    for result in results:
        print(f'\n[FILE] {result["file"]} [{result["type"]}]')
        for item in result['passed']:
            print(f'   {item}')
            total_passed += 1
        for item in result['issues']:
            print(f'   {item}')
            if item.startswith('[X]'):
                total_critical += 1
            elif item.startswith('[!]'):
                total_warnings += 1

    print('\n' + '=' * 60)
    print(
        f'[RESULTS] {total_passed} passed, {total_warnings} warnings, '
        f'{total_critical} critical issues'
    )
    print('=' * 60)

    if total_critical == 0:
        print('[OK] Heuristic validation completed')
        return 0

    print('[X] Fix critical issues before declaring the API healthy')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())

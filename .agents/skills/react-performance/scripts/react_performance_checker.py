#!/usr/bin/env python3
"""Static React performance triage for React and Next.js codebases."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SOURCE_EXTENSIONS = {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'}
SKIP_DIRS = {
    '.git',
    '.next',
    '.turbo',
    'coverage',
    'dist',
    'build',
    'node_modules',
}
NEXT_CONFIG_FILES = {
    'next.config.js',
    'next.config.mjs',
    'next.config.ts',
}
FETCH_HINTS = (
    'fetch(',
    'axios.',
    'api.get(',
    'api.post(',
    'client.get(',
    'client.post(',
)
HEAVY_MODULE_HINTS = (
    'chart.js',
    'echarts',
    'framer-motion',
    'monaco-editor',
    'react-markdown',
    'recharts',
    'three',
)


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    file: str
    line: int
    message: str
    recommendation: str
    reference: str


def detect_framework(target: Path) -> str:
    search_start = target if target.is_dir() else target.parent
    for current in [search_start, *search_start.parents]:
        if any(
            (current / filename).exists() for filename in NEXT_CONFIG_FILES
        ):
            return 'next'
        package_json = current / 'package.json'
        if not package_json.exists():
            continue
        try:
            package = json.loads(package_json.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            continue
        deps = {
            **package.get('dependencies', {}),
            **package.get('devDependencies', {}),
        }
        if 'next' in deps:
            return 'next'
    return 'react'


def iter_source_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        if target.suffix in SOURCE_EXTENSIONS:
            yield target
        return

    for path in target.rglob('*'):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix not in SOURCE_EXTENSIONS:
            continue
        yield path


def line_number(text: str, offset: int) -> int:
    return text.count('\n', 0, offset) + 1


def relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def scan_sequential_awaits(content: str, rel_path: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = content.splitlines()
    reported: set[int] = set()
    for index, line in enumerate(lines):
        if 'await ' not in line or 'Promise.all' in line:
            continue
        if index + 1 >= len(lines):
            continue

        next_index = index + 1
        while next_index < len(lines):
            candidate = lines[next_index].strip()
            if not candidate or candidate.startswith('//'):
                next_index += 1
                continue
            break

        if next_index >= len(lines):
            continue

        next_line = lines[next_index]
        if 'await ' not in next_line or 'Promise.all' in next_line:
            continue
        if next_index in reported:
            continue

        reported.add(next_index)
        findings.append(
            Finding(
                rule='sequential-awaits',
                severity='HIGH',
                file=rel_path,
                line=index + 1,
                message='Independent async work appears to be awaited in sequence.',
                recommendation='If these operations do not depend on one another, start them together and await them with Promise.all().',
                reference='references/loading-waterfalls-and-cache.md',
            )
        )
    return findings


def scan_use_effect_fetch(content: str, rel_path: str) -> list[Finding]:
    findings: list[Finding] = []
    for match in re.finditer(r'\buseEffect\s*\(', content):
        window = content[match.start() : match.start() + 600]
        if not any(hint in window for hint in FETCH_HINTS):
            continue
        findings.append(
            Finding(
                rule='fetch-in-use-effect',
                severity='MEDIUM',
                file=rel_path,
                line=line_number(content, match.start()),
                message='Fetching appears to start from useEffect, which often delays useful work until after paint.',
                recommendation='Consider starting the work earlier via router loaders, server rendering, suspense-friendly caches, or an explicit data layer when the stack supports it.',
                reference='references/loading-waterfalls-and-cache.md',
            )
        )
        break
    return findings


def scan_heavy_browser_imports(content: str, rel_path: str) -> list[Finding]:
    findings: list[Finding] = []
    for match in re.finditer(
        r"^\s*import\s+.+?\s+from\s+['\"](?P<module>[^'\"]+)['\"]",
        content,
        re.M,
    ):
        module_name = match.group('module')
        if not any(hint in module_name for hint in HEAVY_MODULE_HINTS):
            continue
        findings.append(
            Finding(
                rule='heavy-browser-import',
                severity='MEDIUM',
                file=rel_path,
                line=line_number(content, match.start()),
                message=f'Potentially heavy browser dependency imported eagerly: {module_name}.',
                recommendation='Keep heavy dependencies behind route, leaf, or interaction boundaries. Prefer lazy loading or moving non-interactive work off the client when possible.',
                reference='references/bundle-and-browser-js.md',
            )
        )
    return findings


def scan_next_boundaries(content: str, rel_path: str) -> list[Finding]:
    findings: list[Finding] = []
    use_client_match = re.search(r'^\s*["\']use client["\'];?', content, re.M)
    if use_client_match:
        import_count = len(
            re.findall(
                r"^\s*import\s+.+?\s+from\s+['\"][^'\"]+['\"]",
                content,
                re.M,
            )
        )
        if import_count >= 12 or len(content.splitlines()) >= 250:
            findings.append(
                Finding(
                    rule='wide-use-client-boundary',
                    severity='MEDIUM',
                    file=rel_path,
                    line=line_number(content, use_client_match.start()),
                    message='"use client" sits on a large or import-heavy module.',
                    recommendation='Push "use client" down to the smallest interactive leaf you can keep practical, then lazy-load or split heavy dependencies under that leaf.',
                    reference='references/next-app-router-boundaries.md',
                )
            )

    image_match = re.search(r'<img\b', content)
    if image_match and 'next/image' not in content:
        findings.append(
            Finding(
                rule='next-img-tag',
                severity='LOW',
                file=rel_path,
                line=line_number(content, image_match.start()),
                message='Raw <img> tag found in a Next.js scan.',
                recommendation='If this image is user-facing and performance-sensitive, consider next/image or another explicit optimization path.',
                reference='references/next-app-router-boundaries.md',
            )
        )
    return findings


def scan_file(path: Path, root: Path, framework: str) -> list[Finding]:
    try:
        content = path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return []

    rel_path = relative_path(path, root)
    findings: list[Finding] = []
    findings.extend(scan_sequential_awaits(content, rel_path))
    findings.extend(scan_use_effect_fetch(content, rel_path))
    findings.extend(scan_heavy_browser_imports(content, rel_path))
    if framework == 'next':
        findings.extend(scan_next_boundaries(content, rel_path))
    return findings


def summarize(findings: list[Finding]) -> dict[str, int]:
    summary = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for finding in findings:
        summary[finding.severity] = summary.get(finding.severity, 0) + 1
    return summary


def render_text_report(
    findings: list[Finding], framework: str, target: Path
) -> str:
    lines = [
        '=' * 68,
        'REACT PERFORMANCE CHECKER',
        '=' * 68,
        f'Target: {target}',
        f'Framework mode: {framework}',
        '',
    ]

    if not findings:
        lines.append(
            '[SUCCESS] No high-signal findings detected by static triage.'
        )
        return '\n'.join(lines)

    for finding in findings:
        lines.extend(
            [
                f'[{finding.severity}] {finding.file}:{finding.line}',
                f'  Rule: {finding.rule}',
                f'  Issue: {finding.message}',
                f'  Recommendation: {finding.recommendation}',
                f'  Reference: {finding.reference}',
                '',
            ]
        )

    summary = summarize(findings)
    lines.extend(
        [
            '-' * 68,
            'Summary:',
            f'  HIGH: {summary["HIGH"]}',
            f'  MEDIUM: {summary["MEDIUM"]}',
            f'  LOW: {summary["LOW"]}',
        ]
    )
    return '\n'.join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Static React performance triage for React and Next.js projects.'
    )
    parser.add_argument(
        'path', help='Project directory or source file to scan.'
    )
    parser.add_argument(
        '--framework',
        choices=('auto', 'react', 'next'),
        default='auto',
        help="Framework mode. 'auto' detects Next.js and falls back to React.",
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Emit a JSON payload instead of the text report.',
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f'Path not found: {target}', file=sys.stderr)
        return 1

    framework = (
        detect_framework(target)
        if args.framework == 'auto'
        else args.framework
    )
    root = target if target.is_dir() else target.parent
    findings: list[Finding] = []
    for source_file in iter_source_files(target):
        findings.extend(scan_file(source_file, root, framework))

    findings.sort(key=lambda item: (item.file, item.line, item.rule))

    if args.json:
        payload = {
            'status': 'ok',
            'framework': framework,
            'target': str(target),
            'summary': summarize(findings),
            'findings': [asdict(finding) for finding in findings],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(render_text_report(findings, framework, target))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

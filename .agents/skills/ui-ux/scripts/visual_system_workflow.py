#!/usr/bin/env python3
"""Automated UI/UX visual-system workflow.

Wraps the lower-level search and design-system scripts so the skill can keep a
single operational entrypoint without relying on a slash-command workflow file.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable

from core import (
    AVAILABLE_STACKS,
    CSV_CONFIG,
    MAX_RESULTS,
    search,
    search_stack,
)
from design_system import generate_design_system
from search import format_output

DEFAULT_STACK = 'html-tailwind'
MODE_DEFAULT_DOMAINS = {
    'standalone': ['style', 'color', 'typography'],
    'support': ['color', 'typography', 'ux'],
}
CHART_HINTS = ('dashboard', 'analytics', 'metrics', 'chart', 'graph', 'trend')
LANDING_HINTS = ('landing', 'hero', 'pricing', 'testimonial', 'marketing')


def _dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def infer_domains(
    query: str, mode: str, explicit_domains: list[str]
) -> list[str]:
    if explicit_domains:
        return _dedupe(explicit_domains)

    query_lower = query.lower()
    inferred = list(MODE_DEFAULT_DOMAINS[mode])

    if any(token in query_lower for token in CHART_HINTS):
        inferred.append('chart')
    if mode == 'standalone' and any(
        token in query_lower for token in LANDING_HINTS
    ):
        inferred.append('landing')

    return _dedupe(inferred)


def build_persist_summary(project_name: str | None, page: str | None) -> str:
    slug_source = project_name or 'default'
    project_slug = slug_source.lower().replace(' ', '-')
    lines = [
        'Persistence',
        f'- design-system/{project_slug}/MASTER.md',
    ]
    if page:
        page_slug = page.lower().replace(' ', '-')
        lines.append(f'- design-system/{project_slug}/pages/{page_slug}.md')
    return '\n'.join(lines)


def render_markdown_report(
    *,
    mode: str,
    query: str,
    stack: str,
    design_system: str,
    domain_reports: list[tuple[str, str]],
    stack_report: str | None,
    persist_summary: str | None,
) -> str:
    lines = [
        '# UI/UX Automation',
        '',
        f'- **Mode:** {mode}',
        f'- **Query:** {query}',
        f'- **Stack:** {stack}',
        '',
        '## Design System',
        '',
        design_system,
        '',
    ]

    if persist_summary:
        lines.extend(['## Persistence', '', persist_summary, ''])

    if domain_reports:
        lines.append('## Supplemental Domains')
        lines.append('')
        for domain, report in domain_reports:
            lines.append(f'### {domain}')
            lines.append('')
            lines.append(report)
            lines.append('')

    if stack_report:
        lines.extend(['## Stack Guidance', '', stack_report, ''])

    return '\n'.join(lines).strip() + '\n'


def render_ascii_report(
    *,
    mode: str,
    query: str,
    stack: str,
    design_system: str,
    domain_reports: list[tuple[str, str]],
    stack_report: str | None,
    persist_summary: str | None,
) -> str:
    divider = '=' * 72
    parts = [
        divider,
        'UI/UX AUTOMATION',
        divider,
        f'Mode: {mode}',
        f'Query: {query}',
        f'Stack: {stack}',
        '',
        design_system.strip(),
    ]

    if persist_summary:
        parts.extend(['', divider, persist_summary.strip()])

    if domain_reports:
        parts.extend(['', divider, 'SUPPLEMENTAL DOMAINS'])
        for domain, report in domain_reports:
            parts.extend(['', f'[{domain}]', report.strip()])

    if stack_report:
        parts.extend(['', divider, 'STACK GUIDANCE', stack_report.strip()])

    parts.append(divider)
    return '\n'.join(parts) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Run the UI/UX automation flow.'
    )
    parser.add_argument('query', help='High-level product/style query')
    parser.add_argument(
        '--mode',
        choices=['standalone', 'support'],
        default='standalone',
        help='Standalone visual-system work or support for another skill',
    )
    parser.add_argument(
        '--project-name',
        '-p',
        default=None,
        help='Project name for generated output and persistence',
    )
    parser.add_argument(
        '--format',
        '-f',
        choices=['ascii', 'markdown'],
        default='markdown',
        help='Output format for the combined report',
    )
    parser.add_argument(
        '--persist',
        action='store_true',
        help='Persist the generated design system to design-system/<project>/',
    )
    parser.add_argument(
        '--page',
        default=None,
        help='Optional page override name when persisting',
    )
    parser.add_argument(
        '--output-dir',
        '-o',
        default=None,
        help='Optional output directory for persisted files',
    )
    parser.add_argument(
        '--stack',
        choices=AVAILABLE_STACKS,
        default=DEFAULT_STACK,
        help=f'Stack guidance target (default: {DEFAULT_STACK})',
    )
    parser.add_argument(
        '--domain',
        dest='domains',
        action='append',
        choices=sorted(CSV_CONFIG.keys()),
        help='Supplemental search domain. Repeat to include multiple domains.',
    )
    parser.add_argument(
        '--no-stack-guidance',
        action='store_true',
        help='Skip stack guidance even when stack is known',
    )
    parser.add_argument(
        '--max-results',
        '-n',
        type=int,
        default=MAX_RESULTS,
        help=f'Max supplemental results per domain (default: {MAX_RESULTS})',
    )

    args = parser.parse_args()

    design_system = generate_design_system(
        args.query,
        project_name=args.project_name,
        output_format=args.format,
        persist=args.persist,
        page=args.page,
        output_dir=args.output_dir,
    )

    selected_domains = infer_domains(args.query, args.mode, args.domains or [])
    domain_reports: list[tuple[str, str]] = []
    for domain in selected_domains:
        result = search(args.query, domain, args.max_results)
        if result.get('count', 0) > 0:
            domain_reports.append((domain, format_output(result)))

    stack_report = None
    if not args.no_stack_guidance:
        stack_result = search_stack(args.query, args.stack, args.max_results)
        if stack_result.get('count', 0) > 0:
            stack_report = format_output(stack_result)

    persist_summary = None
    if args.persist:
        persist_summary = build_persist_summary(args.project_name, args.page)

    if args.format == 'markdown':
        report = render_markdown_report(
            mode=args.mode,
            query=args.query,
            stack=args.stack,
            design_system=design_system,
            domain_reports=domain_reports,
            stack_report=stack_report,
            persist_summary=persist_summary,
        )
    else:
        report = render_ascii_report(
            mode=args.mode,
            query=args.query,
            stack=args.stack,
            design_system=design_system,
            domain_reports=domain_reports,
            stack_report=stack_report,
            persist_summary=persist_summary,
        )

    print(report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

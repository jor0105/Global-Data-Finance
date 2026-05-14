#!/usr/bin/env python3
"""Sync or check .github/instructions mirrors from .agents/rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = REPO_ROOT / '.agents' / 'rules'
INSTRUCTIONS_DIR = REPO_ROOT / '.github' / 'instructions'

RULE_MIRRORS = {
    'GLOBAL_RULE.md': 'GLOBAL_RULE.instructions.md',
}


def collect_sources() -> dict[str, str]:
    rendered: dict[str, str] = {}
    for source_name, target_name in RULE_MIRRORS.items():
        source_path = RULES_DIR / source_name
        if not source_path.exists():
            raise ValueError(f"missing source rule '{source_name}'")
        rendered[target_name] = source_path.read_text(encoding='utf-8')
    return rendered


def detect_unexpected_files() -> tuple[list[str], list[str]]:
    expected_sources = set(RULE_MIRRORS)
    expected_targets = set(RULE_MIRRORS.values())

    unexpected_sources = sorted(
        path.name
        for path in RULES_DIR.glob('*.md')
        if path.name not in expected_sources
    )
    unexpected_targets = sorted(
        path.name
        for path in INSTRUCTIONS_DIR.glob('*.instructions.md')
        if path.name not in expected_targets
    )
    return unexpected_sources, unexpected_targets


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Sync .github/instructions from canonical .agents/rules files.'
    )
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    rendered = collect_sources()
    INSTRUCTIONS_DIR.mkdir(parents=True, exist_ok=True)

    stale: list[str] = []
    updated: list[str] = []

    for target_name, content in rendered.items():
        output_path = INSTRUCTIONS_DIR / target_name
        current = (
            output_path.read_text(encoding='utf-8')
            if output_path.exists()
            else None
        )
        if current != content:
            stale.append(str(output_path.relative_to(REPO_ROOT)))
            if not args.check:
                output_path.write_text(content, encoding='utf-8')
                updated.append(str(output_path.relative_to(REPO_ROOT)))

    unexpected_sources, unexpected_targets = detect_unexpected_files()

    status = 'ok'
    if stale or unexpected_sources or unexpected_targets:
        status = 'stale' if args.check else 'updated'

    payload = {
        'status': status,
        'checked': len(rendered),
        'stale': stale,
        'updated': updated,
        'unexpected_sources': unexpected_sources,
        'unexpected_targets': unexpected_targets,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    has_drift = bool(stale or unexpected_sources or unexpected_targets)
    return 0 if not has_drift or not args.check else 1


if __name__ == '__main__':
    raise SystemExit(main())

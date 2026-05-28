#!/usr/bin/env python3
"""Sync local OpenCode, Kilo, Codex, and Claude Code agent mirrors from .agents/agents."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / '.agents' / 'agents'
OPENCODE_CONFIG_PATH = REPO_ROOT / 'opencode.json'
KILO_CONFIG_PATH = REPO_ROOT / 'kilo.jsonc'
CODEX_SYNC_SCRIPT = REPO_ROOT / '.agents' / 'scripts' / 'sync-codex-agents.py'
CLAUDE_AGENTS_DIR = REPO_ROOT / '.claude' / 'agents'


def sanitize_json_like(text: str) -> str:
    return re.sub(r',\s*([\]}])', r'\1', text)


def read_json_file(path: Path) -> dict[str, object]:
    return json.loads(sanitize_json_like(path.read_text(encoding='utf-8')))


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = re.match(r'---\n(.*?)\n---\n(.*)\Z', text, re.S)
    if not match:
        raise ValueError('missing frontmatter')

    metadata: dict[str, object] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith((' ', '\t')) or ':' not in line:
            continue
        key, raw_value = line.split(':', 1)
        value = raw_value.strip()
        if value.startswith('[') and value.endswith(']'):
            inner = value[1:-1].strip()
            metadata[key.strip()] = [
                item.strip().strip('"\'')
                for item in inner.split(',')
                if item.strip()
            ]
        else:
            metadata[key.strip()] = value.strip('"\'')
    return metadata, match.group(2)


def collect_agents_data() -> dict[str, dict[str, object]]:
    configs: dict[str, dict[str, object]] = {}

    for path in sorted(AGENT_DIR.glob('*.agent.md')):
        agent_name = path.name.replace('.agent.md', '')
        source_text = path.read_text(encoding='utf-8')
        metadata, _body = parse_frontmatter(source_text)

        manifest_path = AGENT_DIR / f'{agent_name}.manifest.json'
        allowed_agents: list[str] = []
        if manifest_path.exists():
            manifest = read_json_file(manifest_path)
            sidecars = manifest.get('allowed_sidecars', [])
            next_steps = [
                step
                for step in manifest.get('allowed_next_steps', [])
                if step not in ('user', 'end', 'blocked')
            ]
            seen: set[str] = set()
            for item in [*sidecars, *next_steps]:
                if (
                    isinstance(item, str)
                    and item != agent_name
                    and item not in seen
                ):
                    allowed_agents.append(item)
                    seen.add(item)

        if not allowed_agents:
            raw_agents = metadata.get('agents', [])
            if isinstance(raw_agents, list):
                allowed_agents = [
                    item for item in raw_agents if isinstance(item, str)
                ]

        configs[agent_name] = {
            'description': metadata.get('description', ''),
            'mode': metadata.get('mode', 'all'),
            'prompt': f'{{file:.agents/agents/{agent_name}.agent.md}}',
            'agents': allowed_agents,
        }

    return configs


def sync_json_config(
    path: Path,
    agents_config: dict[str, dict[str, object]],
    *,
    check: bool,
) -> tuple[list[str], list[str]]:
    config = read_json_file(path)
    agent_section = config.get('agent')
    if not isinstance(agent_section, dict):
        agent_section = {}
        config['agent'] = agent_section

    for stale_name in sorted(set(agent_section) - set(agents_config)):
        del agent_section[stale_name]

    for agent_name, payload in agents_config.items():
        current = agent_section.get(agent_name)
        if not isinstance(current, dict):
            current = {}
            agent_section[agent_name] = current

        current['description'] = payload['description']
        current['mode'] = payload['mode']
        current['prompt'] = payload['prompt']

        agents = payload['agents']
        if agents:
            current['agents'] = agents
        else:
            current.pop('agents', None)

    rendered = json.dumps(config, ensure_ascii=False, indent=2) + '\n'
    current_text = path.read_text(encoding='utf-8')
    if current_text == rendered:
        return [], []

    rel = str(path.relative_to(REPO_ROOT))
    if check:
        return [rel], []

    path.write_text(rendered, encoding='utf-8')
    return [rel], [rel]


def render_claude_agent(agent_name: str, description: str, body: str) -> str:
    front = f'---\nname: {agent_name}\ndescription: {description}\n---\n'
    return front + body


def sync_claude_agents(
    agents_config: dict[str, dict[str, object]],
    *,
    check: bool,
) -> tuple[list[str], list[str]]:
    CLAUDE_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    updated: list[str] = []

    rendered: dict[str, str] = {}
    for agent_name, payload in agents_config.items():
        source_path = AGENT_DIR / f'{agent_name}.agent.md'
        source_text = source_path.read_text(encoding='utf-8')
        _, body = parse_frontmatter(source_text)
        description = str(payload.get('description', ''))
        rendered[f'{agent_name}.md'] = render_claude_agent(
            agent_name, description, body
        )

    for name, content in rendered.items():
        output_path = CLAUDE_AGENTS_DIR / name
        current = (
            output_path.read_text(encoding='utf-8')
            if output_path.exists()
            else None
        )
        if current != content:
            rel = str(output_path.relative_to(REPO_ROOT))
            stale.append(rel)
            if not check:
                output_path.write_text(content, encoding='utf-8')
                updated.append(rel)

    expected = set(rendered)
    for path in sorted(CLAUDE_AGENTS_DIR.iterdir()):
        if path.is_file() and path.name not in expected:
            rel = str(path.relative_to(REPO_ROOT))
            stale.append(rel)
            if not check:
                path.unlink()
                updated.append(rel)

    return stale, updated


def run_codex_sync(*, check: bool) -> tuple[list[str], list[str]]:
    cmd = [sys.executable, str(CODEX_SYNC_SCRIPT)]
    if check:
        cmd.append('--check')

    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    stdout = proc.stdout.strip()
    if not stdout:
        raise RuntimeError('sync-codex-agents.py produced no output')

    payload = json.loads(stdout)
    stale = payload.get('stale', [])
    updated = payload.get('updated', [])
    if proc.returncode not in (0, 1):
        raise RuntimeError(
            proc.stderr.strip() or 'sync-codex-agents.py failed'
        )
    return stale, updated


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Sync local OpenCode, Kilo, Codex, and Claude Code agent mirrors from .agents/agents.'
    )
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    agents_config = collect_agents_data()
    opencode_stale, opencode_updated = sync_json_config(
        OPENCODE_CONFIG_PATH,
        agents_config,
        check=args.check,
    )
    kilo_stale, kilo_updated = sync_json_config(
        KILO_CONFIG_PATH,
        agents_config,
        check=args.check,
    )
    codex_stale, codex_updated = run_codex_sync(check=args.check)
    claude_stale, claude_updated = sync_claude_agents(
        agents_config, check=args.check
    )

    stale = opencode_stale + kilo_stale + codex_stale + claude_stale
    updated = opencode_updated + kilo_updated + codex_updated + claude_updated

    payload = {
        'status': 'ok'
        if not stale
        else ('stale' if args.check else 'updated'),
        'checked': len(agents_config) + 3,
        'stale': stale,
        'updated': updated,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not stale or not args.check else 1


if __name__ == '__main__':
    raise SystemExit(main())

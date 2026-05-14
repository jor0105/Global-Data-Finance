#!/usr/bin/env python3
"""Valida agents, manifests e protocol skills do fluxo de review."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
AGENTS_ROOT = REPO_ROOT / '.agents'
AGENT_DIR = AGENTS_ROOT / 'agents'
SKILLS_ROOT = AGENTS_ROOT / 'skills'
LINT_AND_VALIDATE_SKILL_DIR = SKILLS_ROOT / 'lint-and-validate'
AGENT_MANIFEST_SCHEMA = AGENT_DIR / 'agent-manifest.schema.json'

EXPECTED_AGENTS = {
    'coordinator',
    'developer-engineer',
    'planner',
    'reviewer',
    'security-engineer',
    'tester',
}

REQUIRED_AGENT_SECTIONS = [
    'Identity',
    'Can Do',
    'Cannot Do',
    'Routing Checklist',
    'Escalation Checklist',
    'Done When',
]

LEGACY_AGENT_SECTIONS = [
    'Skill Routing',
    'Escalation',
    'Activation Rule',
    'Required Inputs',
    'Preflight',
    'Context Policy',
    'Phase Machine',
    'Failure Branches',
    'Success Exit',
    'Stop Conditions',
    'Hard Boundaries',
]

REQUIRED_SKILL_SECTIONS = [
    'Use When',
    'Do Not Use When',
    'Required Inputs',
    'Phase Machine',
    'If Step Fails',
    'Exit Conditions',
    'Expected Handoff',
]

SKILL_PATH_RE = re.compile(r'\.agents/skills/[A-Za-z0-9._\-/]+/SKILL\.md')
SCRIPT_PATH_RE = re.compile(r'\.agents/skills/[A-Za-z0-9._\-/]+\.(?:py|sh)')
SESSION_PATH_RE = re.compile(r'\.agents/sessions/[A-Za-z0-9._<>\-/]+')
HEADING_RE = re.compile(r'^##\s+(.+?)\s*$', re.MULTILINE)
REQUIRED_AGENT_SKILL_METADATA = ['name', 'description']
ALLOWED_AGENT_SKILL_METADATA = {'name', 'description'}
PROTOCOL_SKILLS = {
    'review-closeout',
    'review-item',
    'review-session',
}
VALIDATION_SCOPE = 'agents-manifests-review-protocol-skills'

EXPECTED_ARTIFACT_ASSETS = {
    'review-session': [
        (
            SKILLS_ROOT
            / 'review-session'
            / 'templates'
            / 'review-session.template.md'
        ),
        (
            SKILLS_ROOT
            / 'review-session'
            / 'schemas'
            / 'review-session.schema.json'
        ),
    ],
    'review-plan': [
        (
            SKILLS_ROOT
            / 'review-session'
            / 'templates'
            / 'review-plan.template.md'
        ),
        (
            SKILLS_ROOT
            / 'review-session'
            / 'schemas'
            / 'review-plan.schema.json'
        ),
    ],
    'finding': [
        SKILLS_ROOT / 'review-item' / 'templates' / 'finding.template.md',
        SKILLS_ROOT / 'review-item' / 'schemas' / 'finding.schema.json',
    ],
    'gate-report': [
        LINT_AND_VALIDATE_SKILL_DIR / 'templates' / 'gate-report.template.md',
        LINT_AND_VALIDATE_SKILL_DIR / 'schemas' / 'gate-report.schema.json',
    ],
    'security-handoff': [
        (
            SKILLS_ROOT
            / 'review-item'
            / 'templates'
            / 'security-handoff.template.md'
        ),
        (
            SKILLS_ROOT
            / 'review-item'
            / 'schemas'
            / 'security-handoff.schema.json'
        ),
    ],
    'verdict': [
        SKILLS_ROOT / 'review-closeout' / 'templates' / 'verdict.template.md',
        SKILLS_ROOT / 'review-closeout' / 'schemas' / 'verdict.schema.json',
    ],
    'review-summary': [
        SKILLS_ROOT
        / 'review-closeout'
        / 'templates'
        / 'review-summary.template.md',
    ],
}

EXPECTED_VERIFY_ASSETS = [
    LINT_AND_VALIDATE_SKILL_DIR / 'scripts' / 'ai-verify.py',
    LINT_AND_VALIDATE_SKILL_DIR / 'schemas' / 'ai-verify.schema.json',
    LINT_AND_VALIDATE_SKILL_DIR / 'assets' / 'verification-profiles.json',
    LINT_AND_VALIDATE_SKILL_DIR / 'assets' / 'path-rules.json',
    LINT_AND_VALIDATE_SKILL_DIR / 'assets' / 'escalation-rules.json',
    AGENTS_ROOT / 'fixtures' / 'verification-runtime' / 'passed.json',
    AGENTS_ROOT / 'fixtures' / 'verification-runtime' / 'failed.json',
    AGENTS_ROOT
    / 'fixtures'
    / 'verification-runtime'
    / 'external_failure.json',
    AGENTS_ROOT / 'fixtures' / 'verification-runtime' / 'skipped.json',
]

SPECIAL_NEXT_STEPS = {'end', 'blocked', 'user'}
CHECKLIST_ACTION_TYPES = {
    'open_skill',
    'delegate_agent',
    'no_skill',
    'escalate_agent',
    'block_for_user',
}
ROUTING_ACTION_TYPES = {'open_skill', 'delegate_agent', 'no_skill'}
ESCALATION_ACTION_TYPES = {
    'open_skill',
    'escalate_agent',
    'no_skill',
    'block_for_user',
}

PROHIBITED_GLOBAL_RULE_PATTERNS = [
    re.compile(r'Double quotes', re.IGNORECASE),
    re.compile(r'Semicolons', re.IGNORECASE),
    re.compile(r'2-space indentation', re.IGNORECASE),
    re.compile(r'Import order', re.IGNORECASE),
    re.compile(r'Use @/ imports', re.IGNORECASE),
    re.compile(r'UI copy is pt-BR', re.IGNORECASE),
    re.compile(r'\bKISS\b', re.IGNORECASE),
    re.compile(r'\bYAGNI\b', re.IGNORECASE),
    re.compile(r'Clean Code', re.IGNORECASE),
    re.compile(r'\bSOLID\b', re.IGNORECASE),
]

PROHIBITED_PROTOCOL_SKILL_PHRASES = [
    'The owning agent needs this focused internal workflow.',
    'A direct implementation, review, or validation step is enough.',
    'The request belongs to a different owner or broader coordination flow.',
]


def extract_frontmatter(text: str) -> str:
    if not text.startswith('---\n'):
        return ''
    parts = text.split('---\n', 2)
    if len(parts) < 3:
        return ''
    return parts[1]


def parse_metadata_value(raw_value: str) -> object:
    raw_value = raw_value.strip().strip('"\'')
    if raw_value.startswith('[') and raw_value.endswith(']'):
        inner = raw_value[1:-1].strip()
        if not inner:
            return []
        return [
            item.strip().strip('"\'')
            for item in inner.split(',')
            if item.strip()
        ]
    return raw_value


def parse_frontmatter_metadata(text: str) -> dict[str, object]:
    frontmatter = extract_frontmatter(text)
    metadata: dict[str, object] = {}
    for line in frontmatter.splitlines():
        if not line.strip() or line.startswith((' ', '\t')) or ':' not in line:
            continue
        key, raw_value = line.split(':', 1)
        metadata[key.strip()] = parse_metadata_value(raw_value)
    return metadata


def parse_frontmatter_agents(text: str) -> list[str]:
    frontmatter = extract_frontmatter(text)
    match = re.search(r'agents:\s*\[(.*?)\]', frontmatter, re.DOTALL)
    if not match:
        return []
    raw = match.group(1)
    entries = []
    for chunk in raw.replace('\n', ' ').split(','):
        value = chunk.strip()
        if value:
            entries.append(value)
    return entries


def missing_sections(text: str, required: list[str]) -> list[str]:
    headings = set(HEADING_RE.findall(text))
    return [section for section in required if section not in headings]


def find_present_sections(text: str, candidates: list[str]) -> list[str]:
    headings = set(HEADING_RE.findall(text))
    return [section for section in candidates if section in headings]


def validate_session_reference(ref: str) -> bool:
    if ref == '.agents/sessions/<review-id>':
        return True
    if ref == '.agents/sessions/.../artifacts':
        return True
    if ref == '.agents/sessions/.../views':
        return True
    if ref.startswith('.agents/sessions/review-'):
        return True
    if '/artifacts/' in ref:
        return ref.endswith('.json') or ref.endswith('/')
    if '/views/' in ref:
        return ref.endswith('.md') or ref.endswith('/')
    return False


def collect_paths(text: str, pattern: re.Pattern[str]) -> set[str]:
    return set(pattern.findall(text))


def load_json(path: Path, errors: list[str]) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        errors.append(f'missing json file: {path}')
        return None
    except json.JSONDecodeError as exc:
        errors.append(f'{path}: invalid json ({exc})')
        return None

    if not isinstance(payload, dict):
        errors.append(f'{path}: root payload must be an object')
        return None
    return payload


def validate_string_list(
    path: Path,
    payload: dict[str, object],
    field: str,
    *,
    required_non_empty: bool,
    errors: list[str],
) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list):
        errors.append(f"{path}: field '{field}' must be a list")
        return []

    parsed: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(
                f"{path}: field '{field}' must contain non-empty strings"
            )
            continue
        parsed.append(item.strip())

    if len(parsed) != len(set(parsed)):
        errors.append(f"{path}: field '{field}' must not contain duplicates")

    if required_non_empty and not parsed:
        errors.append(f"{path}: field '{field}' must not be empty")

    return parsed


def extract_section_body(text: str, heading: str) -> str | None:
    pattern = re.compile(rf'^##\s+{re.escape(heading)}\s*$', re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        return None

    start = match.end()
    next_heading = re.search(r'^##\s+.+\s*$', text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def render_checklist_action(action: dict[str, str]) -> str:
    action_type = action['type']
    target = action.get('target')
    if action_type == 'open_skill':
        return f'abra `{target}`.'
    if action_type == 'delegate_agent':
        return f'delegue para `{target}`.'
    if action_type == 'escalate_agent':
        return f'escale para `{target}`.'
    if action_type == 'block_for_user':
        return 'bloqueie para `user`.'
    return 'siga sem abrir skill adicional.'


def render_checklist_section(
    checklist: list[dict[str, object]],
    section_kind: str,
) -> str:
    lines: list[str] = []
    for index, entry in enumerate(checklist, start=1):
        question = str(entry['question'])
        action = entry['action']
        assert isinstance(action, dict)
        action_text = render_checklist_action(action)
        reason = str(action['reason'])
        lines.extend(
            [
                f'{index}. Pergunta: {question}',
                f'   Se sim: {action_text} Motivo: {reason}',
                '   Se nao: siga para a proxima pergunta.',
                '',
            ]
        )

    fallback_line = (
        'Se todas forem nao, siga sem abrir skill adicional.'
        if section_kind == 'routing_checklist'
        else 'Se todas forem nao, permaneca owner atual.'
    )
    lines.append(fallback_line)
    return '\n'.join(lines).strip()


def validate_checklist(
    manifest_path: Path,
    payload: dict[str, object],
    field: str,
    preferred_skills: list[str],
    allowed_sidecars: list[str],
    allowed_next_steps: list[str],
    errors: list[str],
) -> list[dict[str, object]]:
    raw_value = payload.get(field)
    if not isinstance(raw_value, list):
        errors.append(f"{manifest_path}: field '{field}' must be a list")
        return []
    if not raw_value:
        errors.append(f"{manifest_path}: field '{field}' must not be empty")
        return []

    expected_action_types = (
        ROUTING_ACTION_TYPES
        if field == 'routing_checklist'
        else ESCALATION_ACTION_TYPES
    )

    seen_ids: set[str] = set()
    parsed: list[dict[str, object]] = []
    for index, raw_entry in enumerate(raw_value):
        label = f"{manifest_path}: field '{field}' item {index}"
        if not isinstance(raw_entry, dict):
            errors.append(f'{label}: checklist item must be an object')
            continue

        item_id = raw_entry.get('id')
        question = raw_entry.get('question')
        action = raw_entry.get('action')

        if not isinstance(item_id, str) or not item_id.strip():
            errors.append(f'{label}: id must be a non-empty string')
            continue
        item_id = item_id.strip()
        if item_id in seen_ids:
            errors.append(f"{label}: duplicate checklist id '{item_id}'")
        seen_ids.add(item_id)

        if not isinstance(question, str) or len(question.strip()) < 12:
            errors.append(f'{label}: question must be a meaningful string')
            continue

        if not isinstance(action, dict):
            errors.append(f'{label}: action must be an object')
            continue

        action_type = action.get('type')
        target = action.get('target')
        reason = action.get('reason')

        if action_type not in CHECKLIST_ACTION_TYPES:
            errors.append(f"{label}: unknown action type '{action_type}'")
            continue
        if action_type not in expected_action_types:
            errors.append(
                f"{label}: action type '{action_type}' is not allowed in '{field}'"
            )

        if not isinstance(reason, str) or len(reason.strip()) < 8:
            errors.append(
                f'{label}: action reason must be a meaningful string'
            )
            continue

        if action_type == 'open_skill':
            if not isinstance(target, str) or not target.strip():
                errors.append(
                    f'{label}: open_skill action requires a target skill'
                )
            elif target not in preferred_skills:
                errors.append(
                    f"{label}: target skill '{target}' must exist in preferred_skills"
                )
        elif action_type in {'delegate_agent', 'escalate_agent'}:
            if not isinstance(target, str) or not target.strip():
                errors.append(
                    f'{label}: {action_type} action requires a target agent or next step'
                )
            elif (
                target not in allowed_sidecars
                and target not in allowed_next_steps
            ):
                errors.append(
                    f"{label}: target '{target}' must exist in allowed_sidecars or allowed_next_steps"
                )
        elif action_type == 'block_for_user':
            if target != 'user':
                errors.append(f"{label}: block_for_user target must be 'user'")
            if 'user' not in allowed_next_steps:
                errors.append(
                    f"{label}: block_for_user requires 'user' in allowed_next_steps"
                )
        elif target not in (None, ''):
            errors.append(
                f'{label}: no_skill action must not declare a target'
            )

        parsed.append(
            {
                'id': item_id,
                'question': question.strip(),
                'action': {
                    'type': str(action_type),
                    **(
                        {'target': str(target)}
                        if isinstance(target, str) and target
                        else {}
                    ),
                    'reason': reason.strip(),
                },
            }
        )

    return parsed


def validate_agent_skill_metadata(
    skill_file: Path, text: str, errors: list[str]
) -> None:
    metadata = parse_frontmatter_metadata(text)
    missing = [
        key for key in REQUIRED_AGENT_SKILL_METADATA if key not in metadata
    ]
    if missing:
        errors.append(
            f'{skill_file}: missing agent-only skill metadata {missing}'
        )
        return

    expected_name = skill_file.parent.name
    if metadata.get('name') != expected_name:
        errors.append(
            f"{skill_file}: metadata name should be '{expected_name}', got '{metadata.get('name')}'"
        )

    extras = sorted(set(metadata) - ALLOWED_AGENT_SKILL_METADATA)
    if extras:
        errors.append(
            f'{skill_file}: frontmatter de skill deve seguir o contrato mínimo de skill-governance; remova {extras}'
        )

    lowered = text.lower()
    for phrase in PROHIBITED_PROTOCOL_SKILL_PHRASES:
        if phrase.lower() in lowered:
            errors.append(
                f"{skill_file}: contains generic placeholder phrase '{phrase}'"
            )


def validate_manifest_schema(errors: list[str]) -> dict[str, object] | None:
    schema = load_json(AGENT_MANIFEST_SCHEMA, errors)
    if schema is None:
        return None

    required_keys = schema.get('required')
    properties = schema.get('properties')
    if not isinstance(required_keys, list) or not isinstance(properties, dict):
        errors.append(
            f'{AGENT_MANIFEST_SCHEMA}: schema must define object required keys and properties'
        )
        return None
    return schema


def validate_agent_manifest(
    agent_name: str,
    agent_file: Path,
    manifest_schema: dict[str, object] | None,
    all_skill_names: set[str],
    errors: list[str],
) -> dict[str, list[dict[str, object]]] | None:
    manifest_path = AGENT_DIR / f'{agent_name}.manifest.json'
    payload = load_json(manifest_path, errors)
    if payload is None:
        return None

    if manifest_schema is not None:
        expected_keys = set(manifest_schema['required'])
        actual_keys = set(payload.keys())
        if actual_keys != expected_keys:
            errors.append(
                f'{manifest_path}: manifest keys mismatch expected={sorted(expected_keys)} found={sorted(actual_keys)}'
            )

    if payload.get('schemaVersion') != '1.0.0':
        errors.append(f"{manifest_path}: schemaVersion must be '1.0.0'")

    if payload.get('name') != agent_name:
        errors.append(f"{manifest_path}: name must be '{agent_name}'")

    purpose = payload.get('purpose')
    if not isinstance(purpose, str) or len(purpose.strip()) < 12:
        errors.append(f'{manifest_path}: purpose must be a meaningful string')

    required_context = validate_string_list(
        manifest_path,
        payload,
        'required_context',
        required_non_empty=True,
        errors=errors,
    )
    validate_string_list(
        manifest_path,
        payload,
        'optional_context',
        required_non_empty=False,
        errors=errors,
    )
    allowed_sidecars = validate_string_list(
        manifest_path,
        payload,
        'allowed_sidecars',
        required_non_empty=False,
        errors=errors,
    )
    allowed_next_steps = validate_string_list(
        manifest_path,
        payload,
        'allowed_next_steps',
        required_non_empty=True,
        errors=errors,
    )
    preferred_skills = validate_string_list(
        manifest_path,
        payload,
        'preferred_skills',
        required_non_empty=False,
        errors=errors,
    )
    validate_string_list(
        manifest_path,
        payload,
        'must_not',
        required_non_empty=True,
        errors=errors,
    )
    validate_string_list(
        manifest_path,
        payload,
        'done_when',
        required_non_empty=True,
        errors=errors,
    )

    if not required_context:
        errors.append(f'{manifest_path}: required_context cannot be empty')

    runtime_sidecars = sorted(
        parse_frontmatter_agents(agent_file.read_text(encoding='utf-8'))
    )
    if sorted(allowed_sidecars) != runtime_sidecars:
        errors.append(
            f'{manifest_path}: allowed_sidecars must match frontmatter agents expected={runtime_sidecars} found={sorted(allowed_sidecars)}'
        )

    for sidecar in allowed_sidecars:
        if sidecar not in EXPECTED_AGENTS:
            errors.append(
                f"{manifest_path}: unknown allowed_sidecar '{sidecar}'"
            )
        if sidecar == agent_name:
            errors.append(
                f'{manifest_path}: agent cannot list itself in allowed_sidecars'
            )

    for next_step in allowed_next_steps:
        if (
            next_step not in EXPECTED_AGENTS
            and next_step not in SPECIAL_NEXT_STEPS
        ):
            errors.append(
                f"{manifest_path}: unknown allowed_next_step '{next_step}'"
            )

    for skill_name in preferred_skills:
        if skill_name not in all_skill_names:
            errors.append(
                f"{manifest_path}: unknown preferred_skill '{skill_name}'"
            )

    routing_checklist = validate_checklist(
        manifest_path,
        payload,
        'routing_checklist',
        preferred_skills,
        allowed_sidecars,
        allowed_next_steps,
        errors,
    )
    escalation_checklist = validate_checklist(
        manifest_path,
        payload,
        'escalation_checklist',
        preferred_skills,
        allowed_sidecars,
        allowed_next_steps,
        errors,
    )

    for forbidden_key in ('model', 'permission', 'tools', 'handoffs'):
        if forbidden_key in payload:
            errors.append(
                f"{manifest_path}: forbidden runtime field '{forbidden_key}'"
            )

    return {
        'routing_checklist': routing_checklist,
        'escalation_checklist': escalation_checklist,
    }


def validate_prompt_shape(
    agent_file: Path, text: str, errors: list[str]
) -> None:
    missing = missing_sections(text, REQUIRED_AGENT_SECTIONS)
    if missing:
        errors.append(f'{agent_file}: missing agent sections {missing}')

    legacy_sections = find_present_sections(text, LEGACY_AGENT_SECTIONS)
    if legacy_sections:
        errors.append(
            f'{agent_file}: legacy agent sections still present {legacy_sections}'
        )

    for phrase in PROHIBITED_GLOBAL_RULE_PATTERNS:
        if phrase.search(text):
            errors.append(
                f"{agent_file}: duplicates global rule phrase '{phrase.pattern}' that belongs in AGENTS.md or .agents/rules"
            )


def validate_prompt_checklists(
    agent_file: Path,
    text: str,
    manifest_checklists: dict[str, list[dict[str, object]]],
    errors: list[str],
) -> None:
    section_map = {
        'Routing Checklist': 'routing_checklist',
        'Escalation Checklist': 'escalation_checklist',
    }
    for heading, manifest_field in section_map.items():
        body = extract_section_body(text, heading)
        if body is None:
            continue

        expected = render_checklist_section(
            manifest_checklists.get(manifest_field, []),
            manifest_field,
        )
        if body.strip() != expected.strip():
            errors.append(
                f"{agent_file}: section '{heading}' does not mirror '{manifest_field}' from manifest"
            )


def validate_artifact_asset_layout(errors: list[str]) -> None:
    for artifact_type, asset_paths in EXPECTED_ARTIFACT_ASSETS.items():
        for asset_path in asset_paths:
            if not asset_path.exists():
                errors.append(
                    f'missing {artifact_type} artifact asset: {asset_path}'
                )

    for legacy_dir_name in ('templates', 'schemas'):
        legacy_dir = AGENTS_ROOT / legacy_dir_name
        if legacy_dir.exists() and any(legacy_dir.iterdir()):
            errors.append(
                f'legacy .agents/{legacy_dir_name} must stay empty or absent'
            )

    for asset_path in EXPECTED_VERIFY_ASSETS:
        if not asset_path.exists():
            errors.append(f'missing ai:verify asset: {asset_path}')


def main() -> int:
    agent_files = sorted(AGENT_DIR.glob('*.agent.md'))
    skill_files = [
        SKILLS_ROOT / skill_name / 'SKILL.md'
        for skill_name in sorted(PROTOCOL_SKILLS)
    ]

    errors: list[str] = []
    manifest_schema = validate_manifest_schema(errors)
    all_skill_names = {
        path.parent.name for path in SKILLS_ROOT.glob('*/SKILL.md')
    }

    found_agents = {path.name.replace('.agent.md', '') for path in agent_files}
    if found_agents != EXPECTED_AGENTS:
        errors.append(
            'agent set mismatch: '
            f'expected={sorted(EXPECTED_AGENTS)} found={sorted(found_agents)}'
        )

    for agent_file in agent_files:
        text = agent_file.read_text(encoding='utf-8')
        validate_prompt_shape(agent_file, text, errors)

        metadata = parse_frontmatter_metadata(text)
        if metadata.get('name') != agent_file.stem.replace('.agent', ''):
            errors.append(
                f'{agent_file}: frontmatter name must match filename'
            )

        for subagent in parse_frontmatter_agents(text):
            if not (AGENT_DIR / f'{subagent}.agent.md').exists():
                errors.append(
                    f'{agent_file}: missing referenced subagent {subagent}'
                )

        for skill_path in collect_paths(text, SKILL_PATH_RE):
            if not (REPO_ROOT / skill_path).exists():
                errors.append(f'{agent_file}: missing skill path {skill_path}')

        for script_path in collect_paths(text, SCRIPT_PATH_RE):
            if not (REPO_ROOT / script_path).exists():
                errors.append(
                    f'{agent_file}: missing script path {script_path}'
                )

        for session_ref in collect_paths(text, SESSION_PATH_RE):
            if not validate_session_reference(session_ref):
                errors.append(
                    f'{agent_file}: invalid session reference {session_ref}'
                )

        manifest_checklists = validate_agent_manifest(
            agent_file.name.replace('.agent.md', ''),
            agent_file,
            manifest_schema,
            all_skill_names,
            errors,
        )
        if manifest_checklists is not None:
            validate_prompt_checklists(
                agent_file, text, manifest_checklists, errors
            )

    for skill_file in skill_files:
        if not skill_file.exists():
            errors.append(f'missing protocol skill: {skill_file}')
            continue

        text = skill_file.read_text(encoding='utf-8')
        validate_agent_skill_metadata(skill_file, text, errors)
        missing = missing_sections(text, REQUIRED_SKILL_SECTIONS)
        if missing:
            errors.append(f'{skill_file}: missing skill sections {missing}')

        for skill_path in collect_paths(text, SKILL_PATH_RE):
            if not (REPO_ROOT / skill_path).exists():
                errors.append(
                    f'{skill_file}: missing nested skill path {skill_path}'
                )

        for script_path in collect_paths(text, SCRIPT_PATH_RE):
            if not (REPO_ROOT / script_path).exists():
                errors.append(
                    f'{skill_file}: missing script path {script_path}'
                )

    validate_artifact_asset_layout(errors)

    result = {
        'scope': VALIDATION_SCOPE,
        'status': 'ok' if not errors else 'error',
        'agents_checked': len(agent_files),
        'manifests_checked': len(list(AGENT_DIR.glob('*.manifest.json'))),
        'protocol_skills_checked': len(skill_files),
        'skills_checked': len(skill_files),
        'expected_agent_sections': REQUIRED_AGENT_SECTIONS,
        'expected_skill_sections': REQUIRED_SKILL_SECTIONS,
        'errors': errors,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Harness unico de verificacao do repo."""

from __future__ import annotations

import argparse
import contextlib
import fnmatch
import json
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_ROOT.parent
AI_VERIFY_SCHEMA_VERSION = '1.0.0'
PROFILE_PRIORITY = {
    'quick': 1,
    'standard': 2,
    'high-risk': 3,
    'ui-flow': 4,
    'security-touch': 5,
}
TOP_LEVEL_STATUSES = {'passed', 'failed', 'skipped', 'external_failure'}
GATE_STATUSES = {'passed', 'failed', 'skipped', 'external_failure'}
CLASSIFICATIONS = {'code', 'environment', 'not_configured', 'not_applicable'}


@dataclass
class PrecommitHookResult:
    hook_id: str
    label: str
    status: str
    classification: str
    exit_code: int | None
    details: str
    modified_files: bool
    duration_ms: int


@dataclass(frozen=True)
class GateSpec:
    name: str
    label: str
    command: str
    blocking: bool
    timeout_ms: int
    script: str | None = None
    allow_missing: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Executa verificacao repo-native com perfis declarativos.',
    )
    parser.add_argument(
        '--mode',
        choices=['precommit', 'gates'],
        default='precommit',
    )
    parser.add_argument(
        '--profile',
        choices=[
            'auto',
            'quick',
            'standard',
            'high-risk',
            'ui-flow',
            'security-touch',
        ],
        default='auto',
    )
    parser.add_argument('--session-dir', default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--changed-file', action='append', default=[])
    parser.add_argument('--skip-defaults', action='store_true')
    parser.add_argument(
        '--gate',
        action='append',
        default=[],
        help='Formato: gateId|Label|blocking|command',
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def normalize_repo_path(raw_path: str) -> str:
    path = Path(raw_path)
    if path.is_absolute():
        path = path.resolve().relative_to(REPO_ROOT)
    normalized = path.as_posix()
    if normalized.startswith('./'):
        normalized = normalized[2:]
    return normalized


def load_package_scripts() -> dict[str, str]:
    package_json = REPO_ROOT / 'package.json'
    if not package_json.exists():
        return {}
    payload = load_json(package_json)
    scripts = payload.get('scripts', {})
    if not isinstance(scripts, dict):
        return {}
    return {str(name): str(command) for name, command in scripts.items()}


def load_review_session_changed_files(session_dir: str | None) -> list[str]:
    if not session_dir:
        return []
    session_path = (
        REPO_ROOT / session_dir / 'artifacts' / 'review-session.json'
    )
    if not session_path.exists():
        return []
    payload = load_json(session_path)
    changed_files = payload.get('changedFiles', [])
    if not isinstance(changed_files, list):
        return []
    return sorted(
        normalize_repo_path(item)
        for item in changed_files
        if isinstance(item, str)
    )


def run_git_paths(command: list[str]) -> set[str]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return {
        normalize_repo_path(line.strip())
        for line in result.stdout.splitlines()
        if line.strip()
    }


def detect_changed_files(
    cli_changed_files: list[str], session_dir: str | None
) -> list[str]:
    if cli_changed_files:
        return sorted(
            {normalize_repo_path(item) for item in cli_changed_files}
        )

    session_changed = load_review_session_changed_files(session_dir)
    if session_changed:
        return session_changed

    changed = set()
    changed |= run_git_paths(['git', 'diff', '--name-only', '--cached'])
    changed |= run_git_paths(['git', 'diff', '--name-only'])
    changed |= run_git_paths(
        ['git', 'ls-files', '--others', '--exclude-standard']
    )
    return sorted(changed)


def path_matches(pattern: str, changed_file: str) -> bool:
    return fnmatch.fnmatch(changed_file, pattern)


def strongest_profile(profiles: list[str]) -> str | None:
    if not profiles:
        return None
    return max(profiles, key=lambda profile: PROFILE_PRIORITY[profile])


def resolve_effective_profile(
    requested_profile: str,
    changed_files: list[str],
    path_rules: list[dict[str, Any]],
) -> tuple[str, str]:
    matched_profiles: list[str] = []
    matched_reasons: list[str] = []

    for changed_file in changed_files:
        for rule in path_rules:
            pattern = str(rule.get('pattern', ''))
            profile = rule.get('profile')
            if not pattern or not isinstance(profile, str):
                continue
            if path_matches(pattern, changed_file):
                matched_profiles.append(profile)
                matched_reasons.append(
                    str(rule.get('reason', f'Matched {pattern}.'))
                )

    detected_profile = strongest_profile(matched_profiles)
    if requested_profile == 'auto':
        if detected_profile:
            return detected_profile, '; '.join(dict.fromkeys(matched_reasons))
        if not changed_files:
            return (
                'standard',
                'Nenhum arquivo alterado detectado; usando perfil standard por default.',
            )
        return (
            'standard',
            'Nenhuma regra especial disparou; usando perfil standard.',
        )

    requested_effective = requested_profile
    if (
        detected_profile
        and PROFILE_PRIORITY[detected_profile]
        > PROFILE_PRIORITY[requested_profile]
    ):
        return (
            detected_profile,
            '; '.join(
                dict.fromkeys(
                    [
                        *matched_reasons,
                        f"Perfil pedido '{requested_profile}' foi elevado para '{detected_profile}'.",
                    ]
                ),
            ),
        )
    return (
        requested_effective,
        f"Perfil '{requested_profile}' solicitado explicitamente.",
    )


def collect_escalation_reasons(
    changed_files: list[str],
    effective_profile: str,
    escalation_rules: dict[str, Any],
) -> dict[str, Any]:
    result = {
        'reviewRequired': False,
        'securityRequired': False,
        'testerRecommended': False,
        'reasons': [],
    }

    def apply_rules(flag_name: str, rules: list[dict[str, Any]]) -> None:
        for rule in rules:
            profile = rule.get('profile')
            pattern = rule.get('pattern')
            reason = str(rule.get('reason', '')).strip()
            if isinstance(profile, str) and profile == effective_profile:
                result[flag_name] = True
                if reason:
                    result['reasons'].append(reason)
            if isinstance(pattern, str) and any(
                path_matches(pattern, item) for item in changed_files
            ):
                result[flag_name] = True
                if reason:
                    result['reasons'].append(reason)

    apply_rules('reviewRequired', escalation_rules.get('reviewRequired', []))
    apply_rules(
        'securityRequired', escalation_rules.get('securityRequired', [])
    )
    apply_rules(
        'testerRecommended', escalation_rules.get('testerRecommended', [])
    )
    result['reasons'] = list(dict.fromkeys(result['reasons']))
    return result


def parse_custom_gate(raw_gate: str) -> GateSpec:
    parts = [item.strip() for item in raw_gate.split('|', 3)]
    if len(parts) != 4:
        raise ValueError(
            'gate spec must use format gateId|Label|blocking|command'
        )
    gate_name, label, blocking_raw, command = parts
    if blocking_raw.lower() not in {'true', 'false'}:
        raise ValueError(
            f'gate {gate_name!r} has invalid blocking flag {blocking_raw!r}'
        )
    if not gate_name or not label or not command:
        raise ValueError('gate spec cannot contain empty values')
    return GateSpec(
        name=gate_name,
        label=label,
        command=command,
        blocking=blocking_raw.lower() == 'true',
        timeout_ms=300000,
    )


def build_gate_specs(
    requested_profile: str,
    effective_profile: str,
    skip_defaults: bool,
    custom_gates: list[str],
) -> list[GateSpec]:
    profiles_config = load_json(
        SKILL_ROOT / 'assets' / 'verification-profiles.json'
    )
    gate_defs = profiles_config.get('gates', {})
    gates: list[GateSpec] = []

    if not skip_defaults:
        profile_gates = (
            profiles_config.get('profiles', {})
            .get(effective_profile, {})
            .get('gates', [])
        )
        for gate_entry in profile_gates:
            gate_id = gate_entry['id']
            gate_config = gate_defs.get(gate_id, {})
            if not gate_config:
                continue
            gates.append(
                GateSpec(
                    name=gate_id,
                    label=str(gate_config.get('label', gate_id)),
                    command=str(gate_config.get('command', '')),
                    blocking=bool(
                        gate_entry.get(
                            'blocking', gate_config.get('blocking', True)
                        )
                    ),
                    timeout_ms=int(gate_config.get('timeoutMs', 300000)),
                    script=str(gate_config.get('script'))
                    if gate_config.get('script')
                    else None,
                    allow_missing=bool(gate_config.get('allowMissing', False)),
                ),
            )

    for raw_gate in custom_gates:
        gates.append(parse_custom_gate(raw_gate))

    if not gates and not custom_gates:
        pass
    return gates


def failure_classification(output: str, exit_code: int | None) -> str:
    lowered = output.lower()
    if 'missing script' in lowered or 'unknown script' in lowered:
        return 'not_configured'
    if exit_code == 127:
        return 'environment'
    environment_signals = [
        'command not found',
        'no such file or directory',
        'enoent',
        'permission denied',
        'timed out',
        "playwright executable doesn't exist",
        'please run the following command to download new browsers',
    ]
    if any(signal in lowered for signal in environment_signals):
        return 'environment'
    return 'code'


def relative_log_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def write_gate_log(
    session_dir: str | None, gate_name: str, output: str
) -> str | None:
    if not session_dir:
        return None
    logs_dir = REPO_ROOT / session_dir / 'logs' / 'ai-verify'
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f'{gate_name}.log'
    log_path.write_text(output, encoding='utf-8')
    return relative_log_path(log_path)


def run_gate(
    spec: GateSpec,
    package_scripts: dict[str, str],
    dry_run: bool,
    session_dir: str | None,
) -> dict[str, Any]:
    if dry_run:
        return {
            'name': spec.name,
            'label': spec.label,
            'command': spec.command,
            'blocking': spec.blocking,
            'status': 'skipped',
            'classification': 'not_applicable',
            'durationMs': 0,
            'exitCode': 0,
            'logPath': None,
            'details': 'Dry run; gate nao foi executado.',
        }

    if spec.script and spec.script not in package_scripts:
        status = 'skipped' if spec.allow_missing else 'external_failure'
        details = f'Script repo-native ausente: npm run {spec.script}'
        return {
            'name': spec.name,
            'label': spec.label,
            'command': spec.command,
            'blocking': spec.blocking,
            'status': status,
            'classification': 'not_configured',
            'durationMs': 0,
            'exitCode': None,
            'logPath': write_gate_log(session_dir, spec.name, details),
            'details': details,
        }

    started_at = time.perf_counter()
    output = ''
    exit_code: int | None = None
    status = 'passed'
    classification = 'code'

    try:
        result = subprocess.run(
            shlex.split(spec.command),
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=max(1, spec.timeout_ms // 1000),
            check=False,
        )
        exit_code = result.returncode
        output = (result.stdout or '') + (
            ('\n' + result.stderr) if result.stderr else ''
        )
        if exit_code == 0:
            status = 'passed'
            classification = 'code'
        else:
            classification = failure_classification(output, exit_code)
            if classification == 'code':
                status = 'failed'
            elif classification == 'not_configured' and spec.allow_missing:
                status = 'skipped'
            else:
                status = 'external_failure'
    except subprocess.TimeoutExpired as error:
        output = f'Command timed out after {spec.timeout_ms}ms.\n{error}'
        exit_code = 124
        status = 'external_failure'
        classification = 'environment'
    except OSError as error:
        output = str(error)
        exit_code = None
        status = 'external_failure'
        classification = 'environment'

    duration_ms = int((time.perf_counter() - started_at) * 1000)
    details = output.strip().splitlines()
    details_text = '\n'.join(details[:10]).strip()
    return {
        'name': spec.name,
        'label': spec.label,
        'command': spec.command,
        'blocking': spec.blocking,
        'status': status,
        'classification': classification,
        'durationMs': duration_ms,
        'exitCode': exit_code,
        'logPath': write_gate_log(session_dir, spec.name, output),
        'details': details_text,
    }


def parse_precommit_output(output: str) -> list[PrecommitHookResult]:
    lines = output.splitlines()
    results = []

    current_hook = None
    details_buffer = []

    result_regex = re.compile(
        r'^(?P<label>.+?)\.+(?:\(no files to check\))?\s*(?P<status>Passed|Failed|Skipped)\s*$',
        re.IGNORECASE,
    )

    for line in lines:
        match = result_regex.match(line)
        if match:
            if current_hook:
                current_hook['details'] = '\n'.join(details_buffer).strip()
                results.append(current_hook)

            label = match.group('label').strip()
            status = match.group('status').lower()
            current_hook = {
                'hook_id': label.replace(' ', '-').lower(),
                'label': label,
                'status': status,
                'classification': 'code',
                'exit_code': None,
                'modified_files': False,
                'duration_ms': 0,
            }
            details_buffer = []
        else:
            if current_hook and current_hook['status'] == 'failed':
                details_buffer.append(line)

                if line.startswith('- hook id: '):
                    current_hook['hook_id'] = line.split('- hook id: ')[
                        1
                    ].strip()
                elif line.startswith('- exit code: '):
                    with contextlib.suppress(ValueError):
                        current_hook['exit_code'] = int(
                            line.split('- exit code: ')[1].strip()
                        )
                elif 'files were modified by this hook' in line:
                    current_hook['modified_files'] = True
                    current_hook['classification'] = 'code'

                if current_hook.get('exit_code') == 127:
                    current_hook['classification'] = 'environment'
                if 'Executable' in line and 'not found' in line:
                    current_hook['classification'] = 'environment'

    if current_hook:
        current_hook['details'] = '\n'.join(details_buffer).strip()
        results.append(current_hook)

    final_results = []
    for h in results:
        details_text = h['details']
        lines_detail = details_text.splitlines()
        if len(lines_detail) > 10:
            details_text = '\n'.join(lines_detail[:10])

        if h['modified_files']:
            details_text = (
                'autofix aplicado — arquivos modificados, reexecute\n'
                + details_text
            )

        final_results.append(
            PrecommitHookResult(
                hook_id=h['hook_id'],
                label=h['label'],
                status=h['status'],
                classification=h['classification'],
                exit_code=h['exit_code'],
                details=details_text.strip(),
                modified_files=h['modified_files'],
                duration_ms=h['duration_ms'],
            )
        )

    return final_results


def load_hook_policy() -> dict[str, Any]:
    policy_path = SKILL_ROOT / 'assets' / 'precommit-hook-policy.json'
    if not policy_path.exists():
        return {}
    return load_json(policy_path).get('hooks', {})


def list_hooks_from_config_as_dry_run() -> list[dict[str, Any]]:
    config_path = REPO_ROOT / '.pre-commit-config.yaml'
    if not config_path.exists():
        return [
            {
                'name': 'pre-commit-config',
                'label': 'Missing config',
                'command': 'pre-commit run',
                'blocking': True,
                'status': 'external_failure',
                'classification': 'not_configured',
                'durationMs': 0,
                'exitCode': 1,
                'logPath': None,
                'details': '.pre-commit-config.yaml not found',
            }
        ]

    try:
        import yaml
    except ImportError:
        return [
            {
                'name': 'pre-commit',
                'label': 'Dry run fallback',
                'command': 'pre-commit run',
                'blocking': True,
                'status': 'skipped',
                'classification': 'not_applicable',
                'durationMs': 0,
                'exitCode': 0,
                'logPath': None,
                'details': 'pyyaml not found. Would run pre-commit run --all-files.',
            }
        ]

    config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    hooks = []
    policy = load_hook_policy()
    for repo in config.get('repos', []):
        for hook in repo.get('hooks', []):
            hook_id = hook['id']
            hooks.append(
                {
                    'name': hook_id,
                    'label': hook.get('name', hook_id),
                    'command': f'pre-commit run {hook_id}',
                    'blocking': policy.get(hook_id, {}).get('blocking', True),
                    'status': 'skipped',
                    'classification': 'not_applicable',
                    'durationMs': 0,
                    'exitCode': 0,
                    'logPath': None,
                    'details': 'Dry run; gate nao foi executado.',
                }
            )
    return hooks


def resolve_scope(profile: str, changed_files: list[str]) -> list[str]:
    if profile in ('high-risk', 'security-touch', 'ui-flow'):
        return ['--all-files']
    if changed_files:
        return ['--files', *changed_files[:100]]
    return ['--all-files']


def to_gate(
    h: PrecommitHookResult, policy: dict[str, Any], session_dir: str | None
) -> dict[str, Any]:
    blocking = policy.get(h.hook_id, {}).get('blocking', True)
    return {
        'name': h.hook_id,
        'label': h.label,
        'command': f'pre-commit run {h.hook_id}',
        'blocking': blocking,
        'status': h.status,
        'classification': h.classification,
        'durationMs': h.duration_ms,
        'exitCode': h.exit_code,
        'logPath': write_gate_log(session_dir, h.hook_id, h.details)
        if h.details
        else None,
        'details': h.details or 'Passed/Skipped without output',
    }


def run_precommit_mode(
    changed_files: list[str],
    effective_profile: str,
    dry_run: bool,
    session_dir: str | None,
) -> list[dict[str, Any]]:
    if dry_run:
        return list_hooks_from_config_as_dry_run()

    scope = resolve_scope(effective_profile, changed_files)
    cmd = ['pre-commit', 'run', *scope]

    started = time.perf_counter()
    try:
        result = subprocess.run(
            cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=600
        )
    except FileNotFoundError:
        return [
            {
                'name': 'pre-commit',
                'label': 'pre-commit setup',
                'command': ' '.join(cmd),
                'blocking': True,
                'status': 'external_failure',
                'classification': 'not_configured',
                'durationMs': 0,
                'exitCode': 127,
                'logPath': None,
                'details': 'pre-commit command not found. Please install pre-commit first.',
            }
        ]
    except subprocess.TimeoutExpired as error:
        return [
            {
                'name': 'pre-commit-timeout',
                'label': 'pre-commit timeout',
                'command': ' '.join(cmd),
                'blocking': True,
                'status': 'external_failure',
                'classification': 'environment',
                'durationMs': 600000,
                'exitCode': 124,
                'logPath': None,
                'details': f'Command timed out after 600s.\n{error}',
            }
        ]

    duration_ms = int((time.perf_counter() - started) * 1000)
    hook_results = parse_precommit_output(result.stdout + result.stderr)
    policy = load_hook_policy()

    if not hook_results:
        return [
            {
                'name': 'pre-commit-raw',
                'label': 'pre-commit (fallback)',
                'command': ' '.join(cmd),
                'blocking': True,
                'status': 'failed' if result.returncode != 0 else 'passed',
                'classification': 'environment'
                if result.returncode == 127
                else 'code',
                'durationMs': duration_ms,
                'exitCode': result.returncode,
                'logPath': write_gate_log(
                    session_dir,
                    'pre-commit-raw',
                    result.stdout + result.stderr,
                ),
                'details': (result.stdout + result.stderr).strip()
                or 'No output and no hooks detected.',
            }
        ]

    return [to_gate(h, policy, session_dir) for h in hook_results]


def summarize_gates(
    gates: list[dict[str, Any]], dry_run: bool, effective_profile: str
) -> str:
    if dry_run:
        return f'Dry run: {len(gates)} gates selecionados para o perfil {effective_profile}.'
    counts = dict.fromkeys(GATE_STATUSES, 0)
    for gate in gates:
        counts[gate['status']] += 1
    parts = []
    for status in ('passed', 'failed', 'external_failure', 'skipped'):
        amount = counts[status]
        if amount:
            parts.append(f'{amount} {status}')
    return ', '.join(parts) if parts else 'Nenhum gate executado.'


def overall_status(gates: list[dict[str, Any]], dry_run: bool) -> str:
    if dry_run:
        return 'skipped'
    blocking_gates = [gate for gate in gates if gate['blocking']]
    if not gates or all(gate['status'] == 'skipped' for gate in gates):
        return 'skipped'
    if any(gate['status'] == 'failed' for gate in blocking_gates):
        return 'failed'
    if any(gate['status'] == 'external_failure' for gate in blocking_gates):
        return 'external_failure'
    return 'passed'


def should_fail_exit_code(gates: list[dict[str, Any]]) -> bool:
    return any(
        gate['blocking'] and gate['status'] in {'failed', 'external_failure'}
        for gate in gates
    )


def load_runtime_support():
    sys.path.append(str(REPO_ROOT / '.agents' / 'runtime' / 'reviewer'))
    from runtime_support import (  # type: ignore
        assert_transition,
        build_empty_gate_report,
        ensure_session_layout,
        load_or_migrate_artifact,
        now_iso,
        resolve_session_dir,
        save_artifact,
    )

    return {
        'assert_transition': assert_transition,
        'build_empty_gate_report': build_empty_gate_report,
        'ensure_session_layout': ensure_session_layout,
        'load_or_migrate_artifact': load_or_migrate_artifact,
        'now_iso': now_iso,
        'resolve_session_dir': resolve_session_dir,
        'save_artifact': save_artifact,
    }


def persist_gate_report(result: dict[str, Any]) -> None:
    session_dir = result['sessionDir']
    if not session_dir:
        return

    runtime = load_runtime_support()
    resolved_session_dir = runtime['resolve_session_dir'](
        session_dir=session_dir
    )
    runtime['ensure_session_layout'](resolved_session_dir)

    session_artifact_path = (
        resolved_session_dir / 'artifacts' / 'review-session.json'
    )
    review_id = resolved_session_dir.name
    if session_artifact_path.exists():
        session_artifact = runtime['load_or_migrate_artifact'](
            resolved_session_dir, 'review-session'
        )
        review_id = session_artifact['reviewId']

    gate_report_path = resolved_session_dir / 'artifacts' / 'gate-report.json'
    if gate_report_path.exists():
        gate_report = runtime['load_or_migrate_artifact'](
            resolved_session_dir, 'gate-report'
        )
    else:
        gate_report = runtime['build_empty_gate_report'](review_id)

    if gate_report['status'] == 'pending':
        runtime['assert_transition']('gate-report', 'pending', 'completed')

    gate_report.update(
        {
            'artifactType': 'gate-report',
            'reviewId': review_id,
            'status': 'completed',
            'updatedAt': runtime['now_iso'](),
            'profile': result['profile'],
            'effectiveProfile': result['effectiveProfile'],
            'profileReason': result['profileReason'],
            'changedFiles': result['changedFiles'],
            'escalations': result['escalations'],
            'summary': result['summary'],
            'gates': [
                {
                    'gateId': gate['name'],
                    'label': gate['label'],
                    'command': gate['command'],
                    'blocking': gate['blocking'],
                    'status': gate['status'],
                    'classification': gate['classification'],
                    'startedAt': gate_report.get(
                        'updatedAt', runtime['now_iso']()
                    ),
                    'finishedAt': runtime['now_iso'](),
                    'durationSeconds': round(gate['durationMs'] / 1000, 3),
                    'durationMs': gate['durationMs'],
                    'exitCode': gate['exitCode']
                    if isinstance(gate['exitCode'], int)
                    else 0,
                    'outcome': gate.get('details', ''),
                    'logPath': gate['logPath'],
                }
                for gate in result['gates']
            ],
        },
    )
    runtime['save_artifact'](resolved_session_dir, gate_report)


def validate_result_shape(result: dict[str, Any]) -> None:
    if result['status'] not in TOP_LEVEL_STATUSES:
        raise ValueError(f'invalid status {result["status"]!r}')
    for gate in result['gates']:
        if gate['status'] not in GATE_STATUSES:
            raise ValueError(f'invalid gate status {gate["status"]!r}')
        if gate['classification'] not in CLASSIFICATIONS:
            raise ValueError(
                f'invalid gate classification {gate["classification"]!r}'
            )


def main() -> int:
    args = parse_args()
    path_rules = load_json(SKILL_ROOT / 'assets' / 'path-rules.json')['rules']
    escalation_rules = load_json(
        SKILL_ROOT / 'assets' / 'escalation-rules.json'
    )
    package_scripts = load_package_scripts()
    changed_files = detect_changed_files(args.changed_file, args.session_dir)
    effective_profile, profile_reason = resolve_effective_profile(
        args.profile,
        changed_files,
        path_rules,
    )
    if args.mode == 'precommit':
        gate_results = run_precommit_mode(
            changed_files, effective_profile, args.dry_run, args.session_dir
        )
    else:
        gates = build_gate_specs(
            requested_profile=args.profile,
            effective_profile=effective_profile,
            skip_defaults=args.skip_defaults,
            custom_gates=args.gate,
        )
        gate_results = [
            run_gate(
                spec=gate,
                package_scripts=package_scripts,
                dry_run=args.dry_run,
                session_dir=args.session_dir,
            )
            for gate in gates
        ]
    result = {
        'schemaVersion': AI_VERIFY_SCHEMA_VERSION,
        'status': overall_status(gate_results, args.dry_run),
        'profile': args.profile,
        'effectiveProfile': effective_profile,
        'profileReason': profile_reason,
        'changedFiles': changed_files,
        'gates': gate_results,
        'escalations': collect_escalation_reasons(
            changed_files=changed_files,
            effective_profile=effective_profile,
            escalation_rules=escalation_rules,
        ),
        'sessionDir': args.session_dir,
        'summary': summarize_gates(
            gate_results, args.dry_run, effective_profile
        ),
    }

    if (
        any(
            gate['status'] in {'failed', 'external_failure'}
            for gate in gate_results
        )
        and not result['escalations']['reviewRequired']
    ):
        result['escalations']['reviewRequired'] = True
        result['escalations']['reasons'].append(
            'Falha de gate exige revisao ou remediacao antes do encerramento.',
        )

    result['escalations']['reasons'] = list(
        dict.fromkeys(result['escalations']['reasons'])
    )
    validate_result_shape(result)
    if args.session_dir and not args.dry_run:
        persist_gate_report(result)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 1 if should_fail_exit_code(gate_results) else 0


if __name__ == '__main__':
    raise SystemExit(main())

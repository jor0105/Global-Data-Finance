#!/usr/bin/env python3
"""Consolidação do veredito de review."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[3] / 'runtime' / 'reviewer')
)

from runtime_support import (
    CURRENT_SCHEMA_VERSION,
    NON_TERMINAL_SECURITY_STATUSES,
    assert_transition,
    list_findings,
    load_or_migrate_artifact,
    now_iso,
    resolve_session_dir,
    save_artifact,
    update_session_statistics,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Consolida o veredito final do review.'
    )
    parser.add_argument('--session-dir', required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session_dir = resolve_session_dir(session_dir=args.session_dir)
    session = load_or_migrate_artifact(session_dir, 'review-session')
    plan = load_or_migrate_artifact(session_dir, 'review-plan')
    gates = load_or_migrate_artifact(session_dir, 'gate-report')
    verdict = load_or_migrate_artifact(session_dir, 'verdict')
    findings = list_findings(session_dir)

    security_path = session_dir / 'artifacts' / 'security-handoff.json'
    security = (
        load_or_migrate_artifact(session_dir, 'security-handoff')
        if security_path.exists()
        else None
    )

    blocking_reasons = []
    advisories = []

    if any(item['status'] != 'completed' for item in plan['items']):
        blocking_reasons.append('Ainda existem itens de review pendentes.')

    blocking_findings = [
        finding
        for finding in findings
        if finding['blocking'] and finding['status'] == 'open'
    ]
    warning_findings = [
        finding
        for finding in findings
        if finding['severity'] == 'warning' and finding['status'] == 'open'
    ]
    nit_findings = [
        finding
        for finding in findings
        if finding['severity'] == 'nit' and finding['status'] == 'open'
    ]
    for finding in blocking_findings:
        blocking_reasons.append(
            f'{finding["findingId"]}: {finding["summary"]}'
        )
    for finding in warning_findings + nit_findings:
        advisories.append(f'{finding["findingId"]}: {finding["summary"]}')

    failed_blocking_gates = [
        gate
        for gate in gates['gates']
        if gate['blocking']
        and gate['status'] in {'failed', 'external_failure'}
    ]
    failed_advisory_gates = [
        gate
        for gate in gates['gates']
        if (not gate['blocking'])
        and gate['status'] in {'failed', 'external_failure'}
    ]
    for gate in failed_blocking_gates:
        if gate['status'] == 'external_failure':
            blocking_reasons.append(
                f'Gate bloqueante indisponivel: {gate["gateId"]}'
            )
        else:
            blocking_reasons.append(
                f'Gate bloqueante falhou: {gate["gateId"]}'
            )
    for gate in failed_advisory_gates:
        if gate['status'] == 'external_failure':
            advisories.append(f'Gate advisory indisponivel: {gate["gateId"]}')
        else:
            advisories.append(f'Gate advisory falhou: {gate["gateId"]}')

    security_outcome = 'not_requested'
    if security is not None:
        security_outcome = security['status']
        if security['status'] in NON_TERMINAL_SECURITY_STATUSES:
            blocking_reasons.append(
                f'Escalonamento de seguranca ainda aberto: {security["status"]}',
            )
        elif security['status'] == 'changes_required':
            blocking_reasons.append('Security engineer solicitou changes.')

    if (
        security is not None
        and security['status'] in NON_TERMINAL_SECURITY_STATUSES
    ):
        final_value = 'SECURITY_REVIEW_REQUIRED'
        summary = 'Review aguardando conclusao do handoff de seguranca.'
    elif blocking_reasons:
        final_value = 'CHANGES_REQUIRED'
        summary = 'Review consolidado com itens bloqueantes.'
    elif advisories:
        final_value = 'APPROVED'
        summary = 'Review aprovado com observacoes advisory registradas.'
    else:
        final_value = 'APPROVED'
        summary = 'Review aprovado sem bloqueios.'

    if verdict['status'] == 'draft':
        assert_transition('verdict', 'draft', 'final')
    verdict.update(
        {
            'artifactType': 'verdict',
            'schemaVersion': CURRENT_SCHEMA_VERSION,
            'reviewId': session['reviewId'],
            'status': 'final',
            'updatedAt': now_iso(),
            'verdict': final_value,
            'summary': summary,
            'blockingReasons': blocking_reasons,
            'advisories': advisories,
            'securityOutcome': security_outcome,
            'metrics': {
                'blockingFindings': len(blocking_findings),
                'warningFindings': len(warning_findings),
                'nitFindings': len(nit_findings),
                'failedBlockingGates': len(failed_blocking_gates),
                'failedAdvisoryGates': len(failed_advisory_gates),
            },
        },
    )
    save_artifact(session_dir, verdict)

    current_status = session['status']
    next_status = (
        'completed'
        if final_value in {'APPROVED', 'CHANGES_REQUIRED'}
        else 'awaiting_security'
    )
    if current_status != next_status:
        assert_transition('review-session', current_status, next_status)
        session['status'] = next_status
        session['updatedAt'] = now_iso()
        save_artifact(session_dir, session)
    update_session_statistics(session_dir)
    print(json.dumps(verdict, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

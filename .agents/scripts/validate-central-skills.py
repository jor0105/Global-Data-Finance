#!/usr/bin/env python3
"""Valida as skills centrais do projeto.

Skills centrais são o núcleo do sistema de agentes — falhas aqui impactam
todos os fluxos. Este script roda o mesmo validador base (validate-skills.py)
e adiciona checagens específicas das skills centrais:
  - Existência do arquivo SKILL.md
  - Ausência de termos legados banidos
  - Consistência com o pack-registry (quando existir)
"""

from __future__ import annotations

import json
import py_compile
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_ROOT.parent.parent
SKILLS_ROOT = REPO_ROOT / '.agents' / 'skills'
REVIEWER_RUNTIME_ROOT = REPO_ROOT / '.agents' / 'runtime' / 'reviewer'
PACK_REGISTRY_PATH = REVIEWER_RUNTIME_ROOT / 'pack-registry.json'

# Skills consideradas centrais para o sistema de agentes.
# Atualizar aqui quando uma nova skill central for adicionada.
CENTRAL_SKILLS: list[str] = [
    'modularizar',
    'lint-and-validate',
    'brainstorming',
    'plan-writing',
    'architecture',
    'api-patterns',
    'frontend-design',
    'ui-ux',
    'database-design',
    'performance-profiling',
    'testing-patterns',
    'tdd-workflow',
    'webapp-testing',
    'vulnerability-scanner',
    'red-team-tactics',
    'react-performance',
    'supabase-postgres-best-practices',
]

# Termos de nomes de agentes legados que não devem aparecer nas skills centrais.
# Banidos pois criam acoplamento a papéis que foram renomeados ou removidos.
BANNED_LEGACY_TERMS: list[str] = [
    'senior-dev',
    'orchestrator',
    'minimalist squad',
    'frontend-specialist',
    'backend-specialist',
    'security-auditor',
    'test-engineer',
    'mobile-developer',
    'database-architect',
]


def _validate_single_via_subprocess(skill_name: str) -> list[str]:
    """Roda validate-skills.py --skill <nome> e retorna lista de erros."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_ROOT / 'validate-skills.py'),
            '--skill',
            skill_name,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return []
    try:
        payload = json.loads(result.stdout)
        return payload.get('errors', [])
    except json.JSONDecodeError:
        return [
            f'validate-skills.py retornou saída inesperada: {result.stdout[:200]}'
        ]


def _check_banned_terms(path: Path, text: str, errors: list[str]) -> None:
    lowered = text.lower()
    for term in BANNED_LEGACY_TERMS:
        if term.lower() in lowered:
            errors.append(f"{path}: contém termo legado banido '{term}'")


def _check_exposed_python_scripts(
    path: Path, text: str, errors: list[str]
) -> None:
    refs = set(
        re.findall(
            r'(?:scripts/[A-Za-z0-9._\-/]+\.py|\.agents/skills/[A-Za-z0-9._-]+/scripts/[A-Za-z0-9._\-/]+\.py)',
            text,
        )
    )

    for ref in sorted(refs):
        if ref.startswith('.agents/skills/'):
            script_path = REPO_ROOT / ref
        else:
            script_path = path.parent / ref

        if not script_path.exists():
            errors.append(f'{path}: script Python exposto não existe: {ref}')
            continue

        try:
            py_compile.compile(str(script_path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f'{script_path}: falha de compilação Python: {exc}')


def _validate_pack_registry(
    skill_texts: dict[str, tuple[Path, str]], errors: list[str]
) -> None:
    if not PACK_REGISTRY_PATH.exists():
        return

    registry: dict[str, dict] = json.loads(
        PACK_REGISTRY_PATH.read_text(encoding='utf-8')
    )
    checklist_path = REVIEWER_RUNTIME_ROOT / 'review-rubric.md'
    checklist_text = (
        checklist_path.read_text(encoding='utf-8')
        if checklist_path.exists()
        else ''
    )

    for pack_name, pack in registry.items():
        for skill_name in pack.get('skills', []):
            entry = skill_texts.get(skill_name)
            if entry is None:
                errors.append(
                    f"{PACK_REGISTRY_PATH}: pack '{pack_name}' referencia skill desconhecida '{skill_name}'"
                )
                continue
            _, text = entry
            if 'status: archived' in text:
                errors.append(
                    f"{PACK_REGISTRY_PATH}: pack '{pack_name}' referencia skill arquivada '{skill_name}'"
                )

        for checklist_id in pack.get('checklists', []):
            if checklist_id not in checklist_text:
                errors.append(
                    f"{PACK_REGISTRY_PATH}: pack '{pack_name}' referencia checklist inexistente '{checklist_id}'"
                )


def main() -> int:
    errors: list[str] = []
    skill_texts: dict[str, tuple[Path, str]] = {}

    for skill_name in CENTRAL_SKILLS:
        path = SKILLS_ROOT / skill_name / 'SKILL.md'

        # 1. Existência
        if not path.exists():
            errors.append(
                f"{path}: SKILL.md não encontrado para skill central '{skill_name}'"
            )
            continue

        text = path.read_text(encoding='utf-8')
        skill_texts[skill_name] = (path, text)

        # 2. Validação estrutural completa via validate-skills.py
        errors.extend(_validate_single_via_subprocess(skill_name))

        # 3. Termos legados banidos (checagem adicional das centrais)
        _check_banned_terms(path, text, errors)

        # 4. Scripts Python expostos pela skill precisam existir e compilar
        _check_exposed_python_scripts(path, text, errors)

    # 5. Consistência do pack-registry
    _validate_pack_registry(skill_texts, errors)

    payload = {
        'status': 'ok' if not errors else 'error',
        'skills_checked': len(CENTRAL_SKILLS),
        'pack_registry_packs': len(
            json.loads(PACK_REGISTRY_PATH.read_text(encoding='utf-8'))
        )
        if PACK_REGISTRY_PATH.exists()
        else 0,
        'errors': errors,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())

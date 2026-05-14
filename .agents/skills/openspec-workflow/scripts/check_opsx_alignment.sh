#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"
repo_root="$(cd "${skill_dir}/../../.." && pwd)"

skill_file="${skill_dir}/SKILL.md"
command_map="${skill_dir}/references/COMMAND_MAP.md"
guardrails="${skill_dir}/references/GUARDRAILS.md"
evals="${skill_dir}/references/EVALS.md"

expected_commands=(
  "new"
  "continue"
  "apply"
  "verify"
  "sync"
  "archive"
  "bulk-archive"
  "explore"
  "ff"
  "onboard"
)

required_files=(
  "${skill_file}"
  "${command_map}"
  "${guardrails}"
  "${evals}"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "${file}" ]]; then
    echo "Missing required file: ${file}" >&2
    exit 1
  fi
done

for command in "${expected_commands[@]}"; do
  workflow="${repo_root}/.agents/workflows/opsx-${command}.prompt.md"
  mirror="${repo_root}/.github/prompts/opsx-${command}.prompt.md"
  token="/opsx:${command}"

  if [[ ! -f "${workflow}" ]]; then
    echo "Missing workflow: ${workflow}" >&2
    exit 1
  fi

  if [[ ! -f "${mirror}" ]]; then
    echo "Missing workflow mirror: ${mirror}" >&2
    exit 1
  fi

  if ! cmp -s "${workflow}" "${mirror}"; then
    echo "Mirror drift detected for ${token}" >&2
    exit 1
  fi

  if ! rg -q --fixed-strings "${token}" "${skill_file}"; then
    echo "Command token missing from skill: ${token}" >&2
    exit 1
  fi

  if ! rg -q --fixed-strings "${token}" "${command_map}"; then
    echo "Command token missing from command map: ${token}" >&2
    exit 1
  fi
done

if rg -n 'openspec/changes/<(name|target)>\.md' "${skill_dir}"; then
  echo "Forbidden legacy execution pattern found in openspec-workflow skill" >&2
  exit 1
fi

echo "opsx alignment ok"

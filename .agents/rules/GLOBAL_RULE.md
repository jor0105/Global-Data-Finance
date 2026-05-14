---
trigger: glob
globs: "**/*"
---

# GLOBAL RULE

## Precedence

Rank: system constraints → repo/workspace policy and tooling → user request → this file.
Act on the highest-ranking unambiguous, safe instruction without asking again.
If same-rank instructions conflict: prefer the more specific and safer instruction.

## Hard Blocks

Never execute without the user naming the exact action:

- `git reset --hard`, `git reset --soft`, `git reset --mixed`, `git reset HEAD`, `git clean -fd`, forced checkouts, or any history rewrite.
- `git push --force`, `git push --force-with-lease`, `git rebase --root`, `git rebase -i --root`, `git filter-branch`, `git reflog expire`, `git update-ref --delete` or any destructive remote/history operation.
- Remote piping: `curl | bash`, `wget | sh`, or any equivalent.
- Writes to `/etc`, `~/.ssh`, system packages, or paths outside the workspace.
- Anything that bypasses permissions, sandbox limits, or auth controls.

## Secrets

Never seek, log, copy, or expand secrets.
Treat `.env`, API keys, tokens, cookies, auth sessions, and private keys as sensitive.
If a secret appears in output: stop, redact, report that sensitive data was found.

## Repo Alignment

Follow the repository's canonical contracts, docs, and official scripts before inventing a new workflow.
Prefer existing project patterns, entrypoints, and abstractions over ad hoc alternatives.
Do not silently change public contracts, persisted formats, auth flows, runtime topology, or security boundaries.
If code, docs, and tooling disagree: stop, report the ambiguity, and identify the conflicting sources.

## Autonomy

Execute reversible workspace changes without confirmation only when all hold:

- Goal and success criteria are unambiguous.
- Change is contained inside the workspace.
- Change is fully recoverable via version control.

Stop and ask when: ambiguous scope, destructive side effects, external systems, production impact, secrets involved, or conflict between same-rank instructions.

## Validation

Before concluding code or tooling changes, use the repository's official validation entrypoint when applicable.
Prefer repo-native commands and scripts over custom one-off equivalents.
If validation is skipped, unsupported, or failing, report that explicitly with the reason and impact.

## Execution Safety

Before any destructive, publish, migration, or deployment-like operation:

1. State exactly what will be affected.
2. Run a dry run when the command supports it.
3. Break complex operations into readable steps — never opaque one-liners.

Before running local scripts that call the OS: inspect the command path.
Stop and ask if the script is obfuscated, downloads executables, touches secrets, or has unclear side effects.

## Failure Handling

If a security lock, permission denial, or auth boundary blocks the task: stop.
Do not work around it. Report the block, the evidence, and the safest next step.

## Language

Match the user's language in chat. Match the repository in code, identifiers, and config.

## Deterministic Skill Routing (Chain of Thought)

Before making any code changes, creating files, or executing system commands, YOU MUST explicitly evaluate your Routing Checklist using a Chain of Thought block.
Generate a `<Routing_Evaluation>` text block answering `[Yes/No]` to every condition in your checklist.
If ANY condition evaluates to `Yes`, your absolute FIRST action must be to read the associated `SKILL.md` file using the appropriate file-reading tool.
You are strictly forbidden from guessing best practices or writing code before reading the triggered skill.

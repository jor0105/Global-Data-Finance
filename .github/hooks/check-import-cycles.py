#!/usr/bin/env python3
"""Fail when the package's import graph contains a cycle.

import-linter (see [tool.importlinter] in pyproject.toml) enforces the
*layering* between top-level packages, but it has no contract type that
expresses "no cycles anywhere". The gap matters: the common Python cycle is a
submodule importing its own package root (``from ...core import x`` while
``core/__init__`` imports that same submodule). That is invisible to a layers
contract because the package root is the container, not a sibling layer.

Such a cycle usually still imports successfully -- but only because of the
statement order inside ``__init__.py``. Reordering imports turns it into an
ImportError at package import time. This hook makes the fragility explicit.
"""

from __future__ import annotations

import sys

import grimp

PACKAGE = 'globaldatafinance'


def find_cycles(graph: grimp.ImportGraph) -> list[list[str]]:
    """Return every strongly connected component that contains a cycle.

    This check uses a static import graph. Grimp's default build includes
    imports guarded by ``TYPE_CHECKING``; dynamic imports are outside this
    contract.

    Iterative Tarjan, so a deep import graph cannot blow the stack.
    """
    modules = sorted(graph.modules)
    adjacency = {
        m: sorted(graph.find_modules_directly_imported_by(m)) for m in modules
    }

    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    cycles: list[list[str]] = []
    counter = 0

    for root in modules:
        if root in index:
            continue
        work: list[tuple[str, int]] = [(root, 0)]
        while work:
            node, child_i = work[-1]
            if child_i == 0:
                index[node] = low[node] = counter
                counter += 1
                stack.append(node)
                on_stack.add(node)

            recursed = False
            children = adjacency.get(node, ())
            for i in range(child_i, len(children)):
                child = children[i]
                if child not in index:
                    work[-1] = (node, i + 1)
                    work.append((child, 0))
                    recursed = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            if recursed:
                continue

            if low[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                if (
                    len(component) > 1
                    or component[0] in adjacency[component[0]]
                ):
                    cycles.append(sorted(component))

            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])

    return cycles


def main() -> int:
    graph = grimp.build_graph(PACKAGE)
    cycles = find_cycles(graph)

    if not cycles:
        print(f'  ok no import cycles ({len(graph.modules)} modules)')
        return 0

    print(f'Import cycle(s) detected in {PACKAGE}:', file=sys.stderr)
    for component in cycles:
        print('', file=sys.stderr)
        for module in component:
            targets = sorted(
                set(graph.find_modules_directly_imported_by(module))
                & set(component)
            )
            for target in targets:
                details = graph.get_import_details(
                    importer=module, imported=target
                )
                where = (
                    f' (line {details[0]["line_number"]})'
                    if details and details[0].get('line_number')
                    else ''
                )
                print(f'  {module} -> {target}{where}', file=sys.stderr)
    print(
        '\nImport a defining module directly instead of routing through the '
        'package root.',
        file=sys.stderr,
    )
    return 1


if __name__ == '__main__':
    raise SystemExit(main())

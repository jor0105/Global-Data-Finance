"""Tests for the repository import-cycle checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import grimp
import pytest

HOOK_PATH = (
    Path(__file__).resolve().parents[2] / 'scripts' / 'check-import-cycles.py'
)


def load_checker() -> ModuleType:
    """Load the hook module from its executable script path."""
    spec = importlib.util.spec_from_file_location(
        'check_import_cycles', HOOK_PATH
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f'Unable to load checker from {HOOK_PATH}')

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def checker() -> Any:
    """Return the loaded import-cycle checker module."""
    return load_checker()


def make_graph(
    edges: list[tuple[str, str]],
    *,
    modules: list[str] | None = None,
) -> grimp.ImportGraph:
    """Build a small import graph for a behavior-focused test."""
    graph = grimp.ImportGraph()
    for module in modules or []:
        graph.add_module(module)
    for importer, imported in edges:
        graph.add_import(importer=importer, imported=imported)
    return graph


@pytest.mark.unit
def test_find_cycles_returns_empty_for_acyclic_graph(checker: Any) -> None:
    """An acyclic graph has no strongly connected components."""
    graph = make_graph([('a', 'b'), ('b', 'c')])

    assert checker.find_cycles(graph) == []


@pytest.mark.unit
def test_find_cycles_finds_two_module_cycle(checker: Any) -> None:
    """A mutual import is reported as one component."""
    graph = make_graph([('a', 'b'), ('b', 'a')])

    assert checker.find_cycles(graph) == [['a', 'b']]


@pytest.mark.unit
def test_find_cycles_finds_three_module_component_with_extra_edges(
    checker: Any,
) -> None:
    """A component remains one cycle when it has a tail and an extra edge."""
    graph = make_graph(
        [
            ('a', 'b'),
            ('b', 'c'),
            ('c', 'a'),
            ('c', 'b'),
            ('c', 'tail'),
        ]
    )

    assert checker.find_cycles(graph) == [['a', 'b', 'c']]


@pytest.mark.unit
def test_find_cycles_reports_self_loop(checker: Any) -> None:
    """A module importing itself is a singleton strongly connected component."""
    graph = make_graph([('a', 'a')])

    assert checker.find_cycles(graph) == [['a']]


@pytest.mark.unit
def test_find_cycles_handles_deep_cycle_without_recursion(
    checker: Any,
) -> None:
    """Deep graphs are processed iteratively instead of via recursion."""
    module_count = 1_500
    graph = make_graph(
        [
            (
                f'module_{index}',
                f'module_{(index + 1) % module_count}',
            )
            for index in range(module_count)
        ]
    )

    cycles = checker.find_cycles(graph)

    assert len(cycles) == 1
    assert len(cycles[0]) == module_count
    assert cycles[0][0] == 'module_0'


@pytest.mark.unit
def test_main_returns_failure_and_line_details_for_cycle(
    checker: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The executable hook fails and reports the import locations."""
    graph = grimp.ImportGraph()
    graph.add_import(
        importer='globaldatafinance.a',
        imported='globaldatafinance.b',
        line_number=7,
        line_contents='from . import b',
    )
    graph.add_import(
        importer='globaldatafinance.b',
        imported='globaldatafinance.a',
        line_number=11,
        line_contents='from . import a',
    )
    monkeypatch.setattr(
        checker.grimp, 'build_graph', lambda *args, **kwargs: graph
    )

    assert checker.main() == 1

    error = capsys.readouterr().err
    assert 'globaldatafinance.a -> globaldatafinance.b (line 7)' in error
    assert 'globaldatafinance.b -> globaldatafinance.a (line 11)' in error

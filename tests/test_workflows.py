import pytest

from dynamic_games.workflows import (
    RandomGameConfig,
    SolveWorkflowError,
    build_solution_report,
    solve_example_game,
    solve_random_game,
)


def test_solve_example_game_builds_report_with_tree_and_steps():
    solved = solve_example_game('centipede')

    report = build_solution_report(solved.game, solved.result, include_tree=True, include_steps=True)

    assert '=== ДЕРЕВО ИГРЫ ===' in report
    assert '=== РЕШЕНИЕ ===' in report
    assert '=== ШАГИ ОБРАТНОЙ ИНДУКЦИИ ===' in report


def test_solve_random_game_supports_three_players():
    solved = solve_random_game(RandomGameConfig(players=3, depth=3, branching=2, seed=42))

    assert len(solved.game.players) == 3
    assert solved.result.root_solutions


def test_solve_example_game_reports_unknown_example():
    with pytest.raises(SolveWorkflowError):
        solve_example_game('missing-example')

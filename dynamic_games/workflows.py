from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .examples import build_example_game
from .io_json import GameFormatError, load_game_from_file
from .models import Game
from .random_generator import generate_random_game
from .renderer_text import render_algorithm_steps, render_game_tree, render_solution_report
from .solver import BackwardInductionResult, solve_game
from .validator import ValidationError, validate_game


class SolveWorkflowError(RuntimeError):
    pass


@dataclass(frozen=True)
class RandomGameConfig:
    players: int = 2
    depth: int = 3
    branching: int = 2
    seed: int | None = None
    title: str = 'Random dynamic game'


@dataclass(frozen=True)
class SolvedGame:
    game: Game
    result: BackwardInductionResult


def solve_loaded_game(game: Game, epsilon: float = 0.0) -> SolvedGame:
    try:
        validate_game(game)
    except ValidationError as exc:
        details = '\n'.join(f'  - {message}' for message in exc.messages)
        raise SolveWorkflowError(f'Ошибка валидации входного графа:\n{details}') from exc
    return SolvedGame(game=game, result=solve_game(game, epsilon=epsilon))


def solve_game_from_path(path: str | Path, epsilon: float = 0.0) -> SolvedGame:
    try:
        game = load_game_from_file(path)
    except GameFormatError as exc:
        raise SolveWorkflowError(f'Ошибка чтения файла игры: {exc}') from exc
    return solve_loaded_game(game, epsilon=epsilon)


def solve_example_game(name: str, epsilon: float = 0.0) -> SolvedGame:
    try:
        game = build_example_game(name)
    except ValueError as exc:
        raise SolveWorkflowError(str(exc)) from exc
    return solve_loaded_game(game, epsilon=epsilon)


def solve_random_game(config: RandomGameConfig, epsilon: float = 0.0) -> SolvedGame:
    try:
        game = generate_random_game(
            num_players=config.players,
            depth=config.depth,
            branching=config.branching,
            seed=config.seed,
            title=config.title,
        )
    except ValueError as exc:
        raise SolveWorkflowError(str(exc)) from exc
    return solve_loaded_game(game, epsilon=epsilon)


def build_solution_report(
    game: Game,
    result: BackwardInductionResult,
    include_tree: bool = False,
    include_steps: bool = False,
) -> str:
    sections: list[str] = []
    if include_tree:
        sections.append('=== ДЕРЕВО ИГРЫ ===\n' + render_game_tree(game))

    sections.append('=== РЕШЕНИЕ ===\n' + render_solution_report(game, result))

    if include_steps:
        sections.append('=== ШАГИ ОБРАТНОЙ ИНДУКЦИИ ===\n' + render_algorithm_steps(result))

    return '\n\n'.join(sections)

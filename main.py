from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dynamic_games.examples import EXAMPLE_BUILDERS, build_example_game
from dynamic_games.io_json import GameFormatError, load_game_from_file, save_game_to_file
from dynamic_games.random_generator import generate_random_game
from dynamic_games.renderer_graph import render_game_to_file
from dynamic_games.solver import solve_game
from dynamic_games.validator import ValidationError, validate_game
from dynamic_games.workflows import build_solution_report


def _ascii_fallback(text: str) -> str:
    translations = {
        '└': '+',
        '├': '+',
        '│': '|',
        '─': '-',
        '↳': '>',
    }
    return ''.join(translations.get(char, char) for char in text)


def _write_console(text: str, file: object = None) -> None:
    stream = file if file is not None else sys.stdout
    try:
        stream.write(text + '\n')
    except UnicodeEncodeError:
        encoding = getattr(stream, 'encoding', None) or 'utf-8'
        safe_text = _ascii_fallback(text)
        safe_text = safe_text.encode(encoding, errors='replace').decode(encoding, errors='replace')
        stream.write(safe_text + '\n')


def cmd_list_examples(_: argparse.Namespace) -> int:
    _write_console('Встроенные примеры:')
    for name in sorted(EXAMPLE_BUILDERS):
        _write_console(f'  - {name}')
    return 0


def cmd_export_example(args: argparse.Namespace) -> int:
    game = build_example_game(args.name)
    save_game_to_file(game, args.out)
    _write_console(f'Пример {args.name!r} сохранён в: {args.out}')
    return 0


def cmd_random(args: argparse.Namespace) -> int:
    game = generate_random_game(
        num_players=args.players,
        depth=args.depth,
        branching=args.branching,
        seed=args.seed,
        title=args.title,
    )
    save_game_to_file(game, args.out)
    _write_console(f'Случайная игра сохранена в: {args.out}')
    return 0


def cmd_solve(args: argparse.Namespace) -> int:
    try:
        game = load_game_from_file(args.input)
    except GameFormatError as exc:
        _write_console(f'Ошибка чтения файла игры: {exc}', file=sys.stderr)
        return 2

    try:
        validate_game(game)
    except ValidationError as exc:
        _write_console('Ошибка валидации входного графа:', sys.stderr)
        for message in exc.messages:
            _write_console(f'  - {message}', sys.stderr)
        return 2

    result = solve_game(game, epsilon=args.epsilon)

    _write_console(
        build_solution_report(
            game,
            result,
            include_tree=args.print_tree,
            include_steps=args.print_steps,
        )
    )

    if args.render_png:
        output_path = Path(args.render_png)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        saved_path = render_game_to_file(game, output_path, result.first_optimal_path)
        _write_console('')
        _write_console(f'Граф сохранён: {saved_path}')

    if args.save_solution_json:
        from dynamic_games.io_json import save_solution_to_file

        save_solution_to_file(result, args.save_solution_json)
        _write_console(f'JSON с решением сохранён: {args.save_solution_json}')

    return 0


def cmd_gui(_: argparse.Namespace) -> int:
    from dynamic_games.gui_app import run_gui

    run_gui()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Анализ и рационализация динамических игр методом обратной индукции.'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    p_list = subparsers.add_parser('list-examples', help='Показать встроенные примеры.')
    p_list.set_defaults(func=cmd_list_examples)

    p_export = subparsers.add_parser('export-example', help='Сохранить встроенный пример в JSON.')
    p_export.add_argument('name', choices=sorted(EXAMPLE_BUILDERS.keys()))
    p_export.add_argument('out', type=Path)
    p_export.set_defaults(func=cmd_export_example)

    p_random = subparsers.add_parser('random', help='Сгенерировать случайную игру.')
    p_random.add_argument('--players', type=int, default=2)
    p_random.add_argument('--depth', type=int, default=3)
    p_random.add_argument('--branching', type=int, default=2)
    p_random.add_argument('--seed', type=int, default=None)
    p_random.add_argument('--title', type=str, default='Random dynamic game')
    p_random.add_argument('--out', type=Path, required=True)
    p_random.set_defaults(func=cmd_random)

    p_gui = subparsers.add_parser('gui', help='Запустить графический интерфейс.')
    p_gui.set_defaults(func=cmd_gui)

    p_solve = subparsers.add_parser('solve', help='Решить игру из JSON.')
    p_solve.add_argument('input', type=Path)
    p_solve.add_argument('--print-tree', action='store_true')
    p_solve.add_argument('--print-steps', action='store_true')
    p_solve.add_argument('--render-png', type=Path, default=None)
    p_solve.add_argument('--save-solution-json', type=Path, default=None)
    p_solve.add_argument('--epsilon', type=float, default=0.0)
    p_solve.set_defaults(func=cmd_solve)

    return parser


if __name__ == '__main__':
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))

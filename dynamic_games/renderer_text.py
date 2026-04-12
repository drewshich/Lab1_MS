from __future__ import annotations

from collections import Counter

from .models import Game
from .solver import BackwardInductionResult, SubgameSolution



def _format_payoff(values: tuple[float, ...] | list[float]) -> str:
    parts = []
    for value in values:
        if float(value).is_integer():
            parts.append(str(int(value)))
        else:
            parts.append(f'{value:.3f}')
    return '(' + ', '.join(parts) + ')'



def render_game_tree(game: Game) -> str:
    parent_counts = Counter()
    for node in game.nodes.values():
        for edge in node.edges:
            parent_counts[edge.to_node] += 1

    lines: list[str] = []
    expanded: set[str] = set()

    def describe(node_id: str) -> str:
        node = game.nodes[node_id]
        label = f' [{node.label}]' if node.label else ''
        if node.is_terminal:
            return f'{node_id}{label} TERM {_format_payoff(node.payoff or [])}'
        player_name = game.get_player_name(node.player or '')
        return f'{node_id}{label} DECISION {player_name}'

    def visit(node_id: str, prefix: str, is_last: bool) -> None:
        connector = '└── ' if prefix else ''
        if prefix and not is_last:
            connector = '├── '
        lines.append(prefix + connector + describe(node_id))

        node = game.nodes[node_id]
        if node.is_terminal:
            return

        if node_id in expanded:
            lines.append(prefix + ('    ' if is_last else '│   ') + '↳ [повторная ссылка на уже раскрытую подигру]')
            return
        expanded.add(node_id)

        child_prefix = prefix + ('    ' if is_last else '│   ')
        for index, edge in enumerate(node.edges):
            child_is_last = index == len(node.edges) - 1
            edge_connector = '└── ' if child_is_last else '├── '
            child_node = game.nodes[edge.to_node]
            if child_node.is_terminal:
                lines.append(
                    child_prefix + edge_connector +
                    f'{edge.action} -> {child_node.id} TERM {_format_payoff(child_node.payoff or [])}'
                )
            else:
                lines.append(child_prefix + edge_connector + f'{edge.action} ->')
                nested_prefix = child_prefix + ('    ' if child_is_last else '│   ')
                visit(edge.to_node, nested_prefix, True)

    lines.append(describe(game.root))
    root = game.nodes[game.root]
    for index, edge in enumerate(root.edges):
        child_is_last = index == len(root.edges) - 1
        child_node = game.nodes[edge.to_node]
        connector = '└── ' if child_is_last else '├── '
        if child_node.is_terminal:
            lines.append(f'{connector}{edge.action} -> {child_node.id} TERM {_format_payoff(child_node.payoff or [])}')
        else:
            lines.append(f'{connector}{edge.action} ->')
            visit(edge.to_node, '    ' if child_is_last else '│   ', True)
    return '\n'.join(lines)



def _render_single_solution(solution: SubgameSolution) -> str:
    steps = ' -> '.join(f'{node}:{action}' for node, action in solution.path)
    if not steps:
        steps = '[лист]'
    return f'Путь: {steps}; полезности: {_format_payoff(solution.payoff)}'



def render_solution_report(game: Game, result: BackwardInductionResult) -> str:
    lines = [f'Игра: {game.title}', f'Корень: {game.root}', 'Оптимальные решения:']
    for index, solution in enumerate(result.root_solutions, start=1):
        lines.append(f'  {index}. {_render_single_solution(solution)}')
    lines.append(f'Порядок сворачивания: {", ".join(result.evaluation_order)}')
    return '\n'.join(lines)



def render_algorithm_steps(result: BackwardInductionResult) -> str:
    return '\n'.join(f'{index + 1}. {message}' for index, message in enumerate(result.logs))

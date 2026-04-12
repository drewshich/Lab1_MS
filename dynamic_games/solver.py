from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .models import Game


@dataclass(frozen=True)
class SubgameSolution:
    payoff: tuple[float, ...]
    path: tuple[tuple[str, str], ...]


@dataclass
class NodeSolutionSet:
    node_id: str
    player_id: str | None
    optimal_solutions: list[SubgameSolution]
    best_utility: float | None
    explored_candidates: list[SubgameSolution]


@dataclass
class BackwardInductionResult:
    game_title: str
    root: str
    root_solutions: list[SubgameSolution]
    node_results: dict[str, NodeSolutionSet]
    evaluation_order: list[str]
    logs: list[str]

    @property
    def first_optimal_path(self) -> tuple[tuple[str, str], ...]:
        if not self.root_solutions:
            return ()
        return self.root_solutions[0].path



def _format_payoff(payoff: tuple[float, ...]) -> str:
    numbers = []
    for value in payoff:
        if float(value).is_integer():
            numbers.append(str(int(value)))
        else:
            numbers.append(f'{value:.3f}')
    return '(' + ', '.join(numbers) + ')'



def solve_game(game: Game, epsilon: float = 0.0) -> BackwardInductionResult:
    node_results: dict[str, NodeSolutionSet] = {}
    evaluation_order: list[str] = []
    logs: list[str] = []

    def is_equal(a: float, b: float) -> bool:
        return abs(a - b) <= epsilon

    def deduplicate(solutions: list[SubgameSolution]) -> list[SubgameSolution]:
        seen: set[tuple[tuple[float, ...], tuple[tuple[str, str], ...]]] = set()
        unique: list[SubgameSolution] = []
        for solution in solutions:
            key = (solution.payoff, solution.path)
            if key not in seen:
                seen.add(key)
                unique.append(solution)
        return unique

    @lru_cache(maxsize=None)
    def solve_subgame(node_id: str) -> NodeSolutionSet:
        node = game.nodes[node_id]

        if node.is_terminal:
            payoff = tuple(node.payoff or [])
            solution = SubgameSolution(payoff=payoff, path=())
            result = NodeSolutionSet(
                node_id=node_id,
                player_id=None,
                optimal_solutions=[solution],
                best_utility=None,
                explored_candidates=[solution],
            )
            node_results[node_id] = result
            evaluation_order.append(node_id)
            logs.append(f'Лист {node_id}: полезности {_format_payoff(payoff)}.')
            return result

        player_index = game.get_player_index(node.player or '')
        player_name = game.get_player_name(node.player or '')

        candidates: list[SubgameSolution] = []
        edge_to_payoffs: dict[str, list[tuple[float, ...]]] = {}
        for edge in node.edges:
            child_result = solve_subgame(edge.to_node)
            for child_solution in child_result.optimal_solutions:
                prefixed = SubgameSolution(
                    payoff=child_solution.payoff,
                    path=((node_id, edge.action),) + child_solution.path,
                )
                candidates.append(prefixed)
                edge_to_payoffs.setdefault(edge.action, []).append(child_solution.payoff)

        best_utility = max(solution.payoff[player_index] for solution in candidates)
        optimal = [solution for solution in candidates if is_equal(solution.payoff[player_index], best_utility)]
        optimal = deduplicate(optimal)

        edge_fragments = []
        for action, payoffs in edge_to_payoffs.items():
            values = ', '.join(_format_payoff(tuple(payoff)) for payoff in payoffs)
            edge_fragments.append(f'{action}: {values}')
        joined = '; '.join(edge_fragments)
        logs.append(
            f'Вершина {node_id} ({player_name}) -> рассматриваем {joined}. '
            f'Максимум по игроку {player_name}: {best_utility:g}. '
            f'Сохраняем {len(optimal)} оптимальн(ых/ое) продолжени(я/е).'
        )

        result = NodeSolutionSet(
            node_id=node_id,
            player_id=node.player,
            optimal_solutions=optimal,
            best_utility=best_utility,
            explored_candidates=deduplicate(candidates),
        )
        node_results[node_id] = result
        evaluation_order.append(node_id)
        return result

    root_result = solve_subgame(game.root)
    return BackwardInductionResult(
        game_title=game.title,
        root=game.root,
        root_solutions=root_result.optimal_solutions,
        node_results=node_results,
        evaluation_order=evaluation_order,
        logs=logs,
    )

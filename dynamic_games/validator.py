from __future__ import annotations

from dataclasses import dataclass

from .models import Game


@dataclass
class ValidationError(Exception):
    messages: list[str]

    def __str__(self) -> str:
        return '\n'.join(self.messages)



def validate_game(game: Game) -> None:
    errors: list[str] = []

    if not game.players:
        errors.append('Список игроков пуст.')
    player_ids = [player.id for player in game.players]
    if len(set(player_ids)) != len(player_ids):
        errors.append('Идентификаторы игроков должны быть уникальными.')

    if not game.nodes:
        errors.append('Граф игры пуст.')
    if game.root not in game.nodes:
        errors.append(f'Корневая вершина {game.root!r} отсутствует в графе.')

    for node_id, node in game.nodes.items():
        if node.kind not in {'decision', 'terminal'}:
            errors.append(f'Вершина {node_id!r} имеет неподдерживаемый тип {node.kind!r}.')
            continue

        if node.is_decision:
            if not node.player:
                errors.append(f'У вершины выбора {node_id!r} не указан игрок.')
            elif node.player not in player_ids:
                errors.append(f'У вершины {node_id!r} указан неизвестный игрок {node.player!r}.')
            if not node.edges:
                errors.append(f'У вершины выбора {node_id!r} нет исходящих рёбер.')
            if node.payoff is not None:
                errors.append(f'У вершины выбора {node_id!r} не должно быть payoff.')
            actions = [edge.action for edge in node.edges]
            if len(set(actions)) != len(actions):
                errors.append(f'В вершине {node_id!r} названия действий должны быть уникальны.')
        else:
            if node.edges:
                errors.append(f'Терминальная вершина {node_id!r} не должна иметь исходящих рёбер.')
            if node.payoff is None:
                errors.append(f'У терминальной вершины {node_id!r} не указан payoff.')
            elif len(node.payoff) != len(game.players):
                errors.append(
                    f'Размер payoff вершины {node_id!r} должен совпадать с числом игроков: '
                    f'{len(node.payoff)} != {len(game.players)}.'
                )

        for edge in node.edges:
            if edge.to_node not in game.nodes:
                errors.append(f'Из вершины {node_id!r} есть ребро в неизвестную вершину {edge.to_node!r}.')

    if game.root in game.nodes:
        reachable = _reachable_nodes(game)
        unreachable = sorted(set(game.nodes) - reachable)
        if unreachable:
            errors.append(f'Недостижимые вершины из корня {game.root!r}: {", ".join(unreachable)}.')

        cycle = _find_cycle(game)
        if cycle is not None:
            errors.append('Граф содержит цикл: ' + ' -> '.join(cycle))

    if errors:
        raise ValidationError(errors)



def _reachable_nodes(game: Game) -> set[str]:
    visited: set[str] = set()

    def dfs(node_id: str) -> None:
        if node_id in visited:
            return
        visited.add(node_id)
        for edge in game.nodes[node_id].edges:
            dfs(edge.to_node)

    dfs(game.root)
    return visited



def _find_cycle(game: Game) -> list[str] | None:
    color: dict[str, int] = {}
    stack: list[str] = []

    def dfs(node_id: str) -> list[str] | None:
        color[node_id] = 1
        stack.append(node_id)
        for edge in game.nodes[node_id].edges:
            nxt = edge.to_node
            state = color.get(nxt, 0)
            if state == 0:
                cycle = dfs(nxt)
                if cycle is not None:
                    return cycle
            elif state == 1:
                start = stack.index(nxt)
                return stack[start:] + [nxt]
        stack.pop()
        color[node_id] = 2
        return None

    if game.root not in game.nodes:
        return None
    return dfs(game.root)

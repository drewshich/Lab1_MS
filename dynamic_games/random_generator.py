from __future__ import annotations

import random

from .models import Edge, Game, Node, Player



def generate_random_game(
    num_players: int = 2,
    depth: int = 3,
    branching: int = 2,
    seed: int | None = None,
    title: str = 'Random dynamic game',
) -> Game:
    if num_players < 2:
        raise ValueError('num_players must be at least 2')
    if depth < 1:
        raise ValueError('depth must be at least 1')
    if branching < 2:
        raise ValueError('branching must be at least 2')

    rng = random.Random(seed)
    players = [Player(f'P{i}', f'Игрок {i}') for i in range(1, num_players + 1)]
    nodes: dict[str, Node] = {}

    terminal_counter = 0

    def build_subtree(current_depth: int, player_index: int, node_id: str) -> None:
        nonlocal terminal_counter
        if current_depth == depth:
            terminal_counter += 1
            payoff = [rng.randint(-2, 10) for _ in range(num_players)]
            nodes[node_id] = Node(id=node_id, kind='terminal', payoff=payoff, label=f'Терминал {terminal_counter}')
            return

        edges: list[Edge] = []
        for branch_index in range(branching):
            child_id = f'{node_id}_{branch_index + 1}'
            edges.append(Edge(action=f'A{branch_index + 1}', to_node=child_id))
            build_subtree(current_depth + 1, (player_index + 1) % num_players, child_id)
        nodes[node_id] = Node(
            id=node_id,
            kind='decision',
            player=players[player_index].id,
            edges=edges,
            label=f'Глубина {current_depth}',
        )

    build_subtree(0, 0, 'N0')
    return Game(title=title, players=players, root='N0', nodes=nodes)

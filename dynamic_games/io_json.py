from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Edge, Game, Node, Player
from .solver import BackwardInductionResult


class GameFormatError(ValueError):
    pass


NODE_KINDS = {'decision', 'terminal'}


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise GameFormatError(f'Missing key: {key}')
    return mapping[key]


def load_game_from_dict(data: dict[str, Any]) -> Game:
    title = str(data.get('title', 'Untitled dynamic game'))

    raw_players = _require(data, 'players')
    if not isinstance(raw_players, list) or not raw_players:
        raise GameFormatError('players must be a non-empty list')
    players = [Player(id=str(item['id']), name=str(item.get('name', item['id']))) for item in raw_players]

    root = str(_require(data, 'root'))
    raw_nodes = _require(data, 'nodes')
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise GameFormatError('nodes must be a non-empty list')

    nodes: dict[str, Node] = {}
    for item in raw_nodes:
        node_id = str(_require(item, 'id'))
        kind = str(_require(item, 'kind'))
        if kind not in NODE_KINDS:
            raise GameFormatError(f'Unsupported node kind: {kind}')
        label = item.get('label')
        if kind == 'decision':
            player = str(_require(item, 'player'))
            raw_edges = item.get('edges', [])
            if not isinstance(raw_edges, list):
                raise GameFormatError(f'edges for node {node_id} must be a list')
            edges = [Edge(action=str(_require(edge, 'action')), to_node=str(_require(edge, 'to'))) for edge in raw_edges]
            node = Node(id=node_id, kind=kind, player=player, edges=edges, payoff=None, label=label)
        else:
            raw_payoff = _require(item, 'payoff')
            if not isinstance(raw_payoff, list):
                raise GameFormatError(f'payoff for node {node_id} must be a list')
            payoff = [float(x) for x in raw_payoff]
            node = Node(id=node_id, kind=kind, player=None, edges=[], payoff=payoff, label=label)
        if node_id in nodes:
            raise GameFormatError(f'Duplicate node id: {node_id}')
        nodes[node_id] = node

    return Game(title=title, players=players, root=root, nodes=nodes)



def load_game_from_file(path: str | Path) -> Game:
    path = Path(path)
    try:
        raw_text = path.read_text(encoding='utf-8-sig')
    except OSError as exc:
        raise GameFormatError(f'Cannot read game file: {path}') from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise GameFormatError(f'Invalid JSON in game file {path}: {exc.msg}') from exc

    if not isinstance(data, dict):
        raise GameFormatError('Root JSON value must be an object')
    return load_game_from_dict(data)



def dump_game_to_dict(game: Game) -> dict[str, Any]:
    return {
        'title': game.title,
        'players': [{'id': player.id, 'name': player.name} for player in game.players],
        'root': game.root,
        'nodes': [
            {
                'id': node.id,
                'kind': node.kind,
                **({'label': node.label} if node.label else {}),
                **({'player': node.player} if node.is_decision else {}),
                **({'edges': [{'action': edge.action, 'to': edge.to_node} for edge in node.edges]} if node.is_decision else {}),
                **({'payoff': node.payoff} if node.is_terminal else {}),
            }
            for node in game.nodes.values()
        ],
    }



def save_game_to_file(game: Game, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dump_game_to_dict(game), ensure_ascii=False, indent=2), encoding='utf-8')



def dump_solution_to_dict(result: BackwardInductionResult) -> dict[str, Any]:
    return {
        'title': result.game_title,
        'root': result.root,
        'optimal_solutions': [
            {
                'payoff': list(solution.payoff),
                'path': [{'node': node_id, 'action': action} for node_id, action in solution.path],
            }
            for solution in result.root_solutions
        ],
        'logs': result.logs,
        'evaluation_order': result.evaluation_order,
    }



def save_solution_to_file(result: BackwardInductionResult, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dump_solution_to_dict(result), ensure_ascii=False, indent=2), encoding='utf-8')

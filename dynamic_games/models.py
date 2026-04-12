from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class Player:
    id: str
    name: str


@dataclass(frozen=True)
class Edge:
    action: str
    to_node: str


@dataclass
class Node:
    id: str
    kind: str  # decision | terminal
    player: str | None = None
    edges: list[Edge] = field(default_factory=list)
    payoff: list[float] | None = None
    label: str | None = None

    @property
    def is_terminal(self) -> bool:
        return self.kind == 'terminal'

    @property
    def is_decision(self) -> bool:
        return self.kind == 'decision'


@dataclass
class Game:
    title: str
    players: list[Player]
    root: str
    nodes: dict[str, Node]

    def player_ids(self) -> list[str]:
        return [player.id for player in self.players]

    def player_names(self) -> list[str]:
        return [player.name for player in self.players]

    def get_player_index(self, player_id: str) -> int:
        for index, player in enumerate(self.players):
            if player.id == player_id:
                return index
        raise KeyError(f'Unknown player id: {player_id}')

    def get_player_name(self, player_id: str) -> str:
        for player in self.players:
            if player.id == player_id:
                return player.name
        raise KeyError(f'Unknown player id: {player_id}')

    def edges(self) -> Iterable[tuple[str, Edge]]:
        for node in self.nodes.values():
            for edge in node.edges:
                yield node.id, edge

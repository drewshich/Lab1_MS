import pytest

from dynamic_games.models import Edge, Game, Node, Player
from dynamic_games.validator import ValidationError, validate_game



def test_cycle_is_rejected():
    players = [Player('P1', 'Игрок 1'), Player('P2', 'Игрок 2')]
    nodes = {
        'N0': Node(id='N0', kind='decision', player='P1', edges=[Edge('go', 'N1')]),
        'N1': Node(id='N1', kind='decision', player='P2', edges=[Edge('back', 'N0')]),
    }
    game = Game(title='Cycle', players=players, root='N0', nodes=nodes)
    with pytest.raises(ValidationError):
        validate_game(game)



def test_unreachable_node_is_rejected():
    players = [Player('P1', 'Игрок 1'), Player('P2', 'Игрок 2')]
    nodes = {
        'N0': Node(id='N0', kind='decision', player='P1', edges=[Edge('go', 'T1')]),
        'T1': Node(id='T1', kind='terminal', payoff=[1, 0]),
        'T2': Node(id='T2', kind='terminal', payoff=[0, 1]),
    }
    game = Game(title='Unreachable', players=players, root='N0', nodes=nodes)
    with pytest.raises(ValidationError):
        validate_game(game)

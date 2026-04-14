from dynamic_games.examples import build_bargaining_game, build_centipede_game, build_trust_model_game
from dynamic_games.models import Edge, Game, Node, Player
from dynamic_games.solver import solve_game
from dynamic_games.validator import validate_game



def test_centipede_root_action_is_stop():
    game = build_centipede_game(turns=4)
    validate_game(game)
    result = solve_game(game)
    assert result.root_solutions
    first_step = result.root_solutions[0].path[0]
    assert first_step == ('C1', 'Stop')



def test_bargaining_finishes_in_first_round_with_rational_offer():
    game = build_bargaining_game()
    validate_game(game)
    result = solve_game(game)
    assert result.root_solutions[0].path[0] == ('B0', 'Рациональное предложение')



def test_trust_model_prefers_safe_choice():
    game = build_trust_model_game()
    validate_game(game)
    result = solve_game(game)
    assert result.root_solutions[0].path[0] == ('T0', 'O: безопасный выбор')



def test_multiple_optimal_solutions_are_kept():
    players = [Player('P1', 'Игрок 1'), Player('P2', 'Игрок 2')]
    nodes = {
        'N0': Node(
            id='N0',
            kind='decision',
            player='P1',
            edges=[Edge('A', 'T1'), Edge('B', 'T2')],
        ),
        'T1': Node(id='T1', kind='terminal', payoff=[5, 0]),
        'T2': Node(id='T2', kind='terminal', payoff=[5, 1]),
    }
    game = Game(title='Tie game', players=players, root='N0', nodes=nodes)
    validate_game(game)
    result = solve_game(game)
    assert len(result.root_solutions) == 2

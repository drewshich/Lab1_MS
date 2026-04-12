from __future__ import annotations

from .models import Edge, Game, Node, Player



def build_centipede_game(turns: int = 4) -> Game:
    players = [Player('P1', 'Игрок 1'), Player('P2', 'Игрок 2')]
    nodes: dict[str, Node] = {}

    continuation_value = (0.0, 0.0)
    stop_payoffs: dict[int, tuple[float, float]] = {}
    current_player_index = (turns - 1) % 2
    for turn in range(turns, 0, -1):
        current_player_index = (turn - 1) % 2
        values = list(continuation_value)
        values[current_player_index] += 2.0
        values[1 - current_player_index] -= 1.0
        continuation_value = (values[0], values[1])
        stop_payoffs[turn] = continuation_value

    final_outcome = [0.0, 0.0]
    final_outcome[current_player_index] -= 1.0
    final_outcome[1 - current_player_index] += 1.0

    for turn in range(1, turns + 1):
        node_id = f'C{turn}'
        player = 'P1' if turn % 2 == 1 else 'P2'
        edges = [Edge('Stop', f'T_stop_{turn}')]
        if turn < turns:
            edges.append(Edge('Continue', f'C{turn + 1}'))
        else:
            edges.append(Edge('Continue', 'T_continue_end'))
        nodes[node_id] = Node(id=node_id, kind='decision', player=player, edges=edges, label=f'Ход {turn}')
        nodes[f'T_stop_{turn}'] = Node(
            id=f'T_stop_{turn}', kind='terminal', payoff=list(stop_payoffs[turn]), label=f'Остановка на шаге {turn}'
        )
    nodes['T_continue_end'] = Node(
        id='T_continue_end', kind='terminal', payoff=final_outcome, label='Все продолжают до конца'
    )

    return Game(title='Игра многоножки', players=players, root='C1', nodes=nodes)



def build_bargaining_game(sigma1: float = 0.9, sigma2: float = 0.9) -> Game:
    players = [Player('P1', 'Игрок 1'), Player('P2', 'Игрок 2')]
    nodes: dict[str, Node] = {}

    round3_accept = [sigma1**2, 0.0]
    round2_accept = [sigma1**2, sigma2 * (1.0 - sigma1)]
    round1_accept = [1.0 - sigma2 * (1.0 - sigma1), sigma2 * (1.0 - sigma1)]

    nodes['B0'] = Node(
        id='B0',
        kind='decision',
        player='P1',
        edges=[Edge('Рациональное предложение', 'B1A'), Edge('Жадное предложение', 'B1G')],
        label='Раунд 1: ход Игрока 1',
    )
    nodes['B1A'] = Node(
        id='B1A',
        kind='decision',
        player='P2',
        edges=[Edge('Принять', 'B1A_T'), Edge('Отклонить', 'B2')],
        label='Ответ Игрока 2',
    )
    nodes['B1G'] = Node(
        id='B1G',
        kind='decision',
        player='P2',
        edges=[Edge('Принять', 'B1G_T'), Edge('Отклонить', 'B2')],
        label='Ответ Игрока 2 на жадное предложение',
    )
    nodes['B2'] = Node(
        id='B2',
        kind='decision',
        player='P2',
        edges=[Edge('Рациональное контрпредложение', 'B2A'), Edge('Жадное контрпредложение', 'B2G')],
        label='Раунд 2: ход Игрока 2',
    )
    nodes['B2A'] = Node(
        id='B2A',
        kind='decision',
        player='P1',
        edges=[Edge('Принять', 'B2A_T'), Edge('Отклонить', 'B3')],
        label='Ответ Игрока 1',
    )
    nodes['B2G'] = Node(
        id='B2G',
        kind='decision',
        player='P1',
        edges=[Edge('Принять', 'B2G_T'), Edge('Отклонить', 'B3')],
        label='Ответ Игрока 1 на жадное контрпредложение',
    )
    nodes['B3'] = Node(
        id='B3',
        kind='decision',
        player='P1',
        edges=[Edge('Финальное предложение', 'B3A')],
        label='Раунд 3: последний шанс',
    )
    nodes['B3A'] = Node(
        id='B3A',
        kind='decision',
        player='P2',
        edges=[Edge('Принять', 'B3A_T'), Edge('Отклонить', 'B_fail')],
        label='Последний ответ Игрока 2',
    )

    nodes['B1A_T'] = Node(id='B1A_T', kind='terminal', payoff=round1_accept, label='Сделка в 1 раунде')
    nodes['B1G_T'] = Node(id='B1G_T', kind='terminal', payoff=[0.99, 0.01], label='Жадная сделка 1 раунда')
    nodes['B2A_T'] = Node(id='B2A_T', kind='terminal', payoff=round2_accept, label='Сделка во 2 раунде')
    nodes['B2G_T'] = Node(id='B2G_T', kind='terminal', payoff=[0.05, 0.95], label='Жадная сделка 2 раунда')
    nodes['B3A_T'] = Node(id='B3A_T', kind='terminal', payoff=round3_accept, label='Сделка в 3 раунде')
    nodes['B_fail'] = Node(id='B_fail', kind='terminal', payoff=[0.0, 0.0], label='Сделка не состоялась')

    return Game(title='Игра торга', players=players, root='B0', nodes=nodes)



def build_trust_model_game() -> Game:
    players = [
        Player('P1', 'Игрок 1'),
        Player('P2', 'Игрок 2'),
        Player('P3', 'Игрок 3'),
    ]
    nodes: dict[str, Node] = {}

    nodes['T0'] = Node(
        id='T0',
        kind='decision',
        player='P1',
        edges=[Edge('O: безопасный выбор', 'T_safe_1'), Edge('Передать ход Игроку 2', 'T1')],
        label='Старт доверия',
    )
    nodes['T1'] = Node(
        id='T1',
        kind='decision',
        player='P2',
        edges=[Edge('O: безопасный выбор', 'T_safe_2'), Edge('Передать ход Игроку 3', 'T2')],
        label='Оценка доверия',
    )
    nodes['T2'] = Node(
        id='T2',
        kind='decision',
        player='P3',
        edges=[Edge('Парето-оптимальный исход', 'T_pareto'), Edge('Случайный/эгоистичный исход', 'T_selfish')],
        label='Выбор Игрока 3',
    )

    nodes['T_safe_1'] = Node(id='T_safe_1', kind='terminal', payoff=[2, 2, 0], label='Безопасный исход Игрока 1')
    nodes['T_safe_2'] = Node(id='T_safe_2', kind='terminal', payoff=[1, 2, 0], label='Безопасный исход Игрока 2')
    nodes['T_pareto'] = Node(id='T_pareto', kind='terminal', payoff=[4, 4, 3], label='Парето-оптимальный исход')
    nodes['T_selfish'] = Node(id='T_selfish', kind='terminal', payoff=[1, 1, 5], label='Эгоистичный выбор Игрока 3')

    return Game(title='Модель доверия', players=players, root='T0', nodes=nodes)


EXAMPLE_BUILDERS = {
    'centipede': build_centipede_game,
    'bargaining': build_bargaining_game,
    'trust_model': build_trust_model_game,
}



def build_example_game(name: str) -> Game:
    try:
        return EXAMPLE_BUILDERS[name]()
    except KeyError as exc:
        raise ValueError(f'Unknown example: {name}') from exc

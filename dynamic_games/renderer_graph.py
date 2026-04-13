from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path

from .models import Game



def _fallback_dot(game: Game, path: Path, solution_path: tuple[tuple[str, str], ...]) -> Path:
    highlighted = set(solution_path)
    dot_lines = ['digraph G {', '  rankdir=LR;', '  node [fontname="Arial"];']
    for node_id, node in game.nodes.items():
        if node.is_terminal:
            label = f'{node_id}\n{tuple(node.payoff or [])}'
            dot_lines.append(f'  "{node_id}" [shape=box, label="{label}"];')
        else:
            label = f'{node_id}\n{game.get_player_name(node.player or "")}'
            dot_lines.append(f'  "{node_id}" [shape=ellipse, label="{label}"];')
    for node_id, node in game.nodes.items():
        for edge in node.edges:
            attrs = [f'label="{edge.action}"']
            if (node_id, edge.action) in highlighted:
                attrs.append('penwidth=3')
                attrs.append('color="red"')
            dot_lines.append(f'  "{node_id}" -> "{edge.to_node}" [{", ".join(attrs)}];')
    dot_lines.append('}')
    dot_path = path.with_suffix('.dot')
    dot_path.write_text('\n'.join(dot_lines), encoding='utf-8')
    return dot_path



def _build_positions(game: Game) -> dict[str, tuple[float, float]]:
    levels: dict[str, int] = {game.root: 0}
    queue = deque([game.root])
    while queue:
        node_id = queue.popleft()
        for edge in game.nodes[node_id].edges:
            if edge.to_node not in levels:
                levels[edge.to_node] = levels[node_id] + 1
                queue.append(edge.to_node)

    grouped: dict[int, list[str]] = defaultdict(list)
    for node_id, level in levels.items():
        grouped[level].append(node_id)

    positions: dict[str, tuple[float, float]] = {}
    for level, node_ids in grouped.items():
        node_ids = sorted(node_ids)
        width = len(node_ids)
        for index, node_id in enumerate(node_ids):
            x = index - (width - 1) / 2
            y = -level
            positions[node_id] = (x, y)
    return positions



def render_game_to_file(game: Game, path: str | Path, solution_path: tuple[tuple[str, str], ...] = ()) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib.pyplot as plt
        import networkx as nx
    except Exception:
        return _fallback_dot(game, path, solution_path)

    graph = nx.DiGraph()
    highlighted_edges = set()
    current = game.root
    for node_id, action in solution_path:
        for edge in game.nodes[node_id].edges:
            if edge.action == action:
                highlighted_edges.add((node_id, edge.to_node, action))
                break

    for node_id, node in game.nodes.items():
        graph.add_node(node_id, terminal=node.is_terminal)
        for edge in node.edges:
            graph.add_edge(node_id, edge.to_node, action=edge.action)

    pos = _build_positions(game)
    plt.figure(figsize=(12, 6))

    decision_nodes = [node_id for node_id, node in game.nodes.items() if node.is_decision]
    terminal_nodes = [node_id for node_id, node in game.nodes.items() if node.is_terminal]

    nx.draw_networkx_nodes(graph, pos, nodelist=decision_nodes, node_shape='o', node_size=2600, alpha=0.95)
    nx.draw_networkx_nodes(graph, pos, nodelist=terminal_nodes, node_shape='s', node_size=2200, alpha=0.95)

    normal_edges = []
    solution_edges = []
    for src, dst, data in graph.edges(data=True):
        marker = (src, dst, data['action'])
        if marker in highlighted_edges:
            solution_edges.append((src, dst))
        else:
            normal_edges.append((src, dst))

    nx.draw_networkx_edges(graph, pos, edgelist=normal_edges, arrows=True, width=1.5, alpha=0.7)
    nx.draw_networkx_edges(graph, pos, edgelist=solution_edges, arrows=True, width=3.5, alpha=0.95)

    node_labels = {}
    for node_id, node in game.nodes.items():
        if node.is_terminal:
            payoff = tuple(node.payoff or [])
            node_labels[node_id] = f'{node_id}\n{payoff}'
        else:
            node_labels[node_id] = f'{node_id}\n{game.get_player_name(node.player or "")}'
    nx.draw_networkx_labels(graph, pos, labels=node_labels, font_size=8)

    edge_labels = {(src, dst): data['action'] for src, dst, data in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=8)

    plt.title(game.title)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches='tight')
    plt.close()
    return path

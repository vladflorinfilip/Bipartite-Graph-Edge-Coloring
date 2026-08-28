from bipartite_g import BipartiteGraph
import copy
from maximum_matching import hopcroft_karp_algorithm

def cover_max_degree(graph: BipartiteGraph, pair_u: dict, pair_v: dict):
    """Rematch so every leftover max-degree vertex is paired (same matching size)."""
    delta = max(len(nbrs) for nbrs in graph.adj.values())
    must = {x for x in graph.adj if len(graph.adj[x]) == delta}

    def steal(start, mine, theirs):
        prev = {start: None}
        queue = [start]
        seen = {start}
        while queue:
            u = queue.pop(0)
            for v in graph.adj[u]:
                if v in seen or mine[u] == v:
                    continue
                prev[v] = u
                seen.add(v)
                u2 = theirs[v]
                if u2 is None or u2 not in must:
                    while v is not None:
                        u = prev[v]
                        mine[u], theirs[v], v = v, u, prev.get(u)
                    if u2 is not None:
                        mine[u2] = None
                    return
                if u2 not in seen:
                    prev[u2] = v
                    seen.add(u2)
                    queue.append(u2)

    for x in must:
        if x in graph.U and pair_u[x] is None:
            steal(x, pair_u, pair_v)
        elif x in graph.V and pair_v[x] is None:
            steal(x, pair_v, pair_u)

def edge_color_max(graph: BipartiteGraph):
    """Use the max-degree matching algorithm to find your layers"""
    copied_graph = copy.deepcopy(graph)
    layer_count = 0
    dp_layers = {}
    while True:
        size, pair_u, pair_v = hopcroft_karp_algorithm(copied_graph)
        if size == 0:
            break
        cover_max_degree(copied_graph, pair_u, pair_v)
        edges = [(u, v) for u, v in pair_u.items() if v is not None]
        for u, v in edges:
            if dp_layers.get(u) is None:
                dp_layers[u] = {}
            dp_layers[u][v] = layer_count
        layer_count += 1
        for u, v in edges:
            copied_graph.adj[u].remove(v)
            copied_graph.adj[v].remove(u)

    return dp_layers

def pad_to_regular(graph: BipartiteGraph, delta: int) -> BipartiteGraph:
    """Convert a general graph to a delat-regular equivalent"""
    u_list, v_list = list(graph.U), list(graph.V)
    n = max(len(u_list), len(v_list))
    u_list += [(i, "PAD_D") for i in range (n - len(u_list))]
    v_list += [(i, "PAD_A") for i in range (n - len(v_list))]

    adj = {v: [] for v in u_list + v_list}
    for u in graph.U:
        for v in graph.adj[u]:
            adj[u].append(v)
            adj[v].append(u)

    gaps_u = [u for u in u_list for _ in range(delta - len(adj[u]))]
    gaps_v = [v for v in v_list for _ in range(delta - len(adj[v]))]
    for u, v in zip(gaps_u, gaps_v):
        adj[u].append(v)
        adj[v].append(u)

    padded = BipartiteGraph()
    padded.U, padded.V, padded.adj = set(u_list), set(v_list), adj
    return padded


def edge_color_regular(graph: BipartiteGraph):
    """Use the delta-regular padded graph to find your layers"""
    if not any(graph.adj.values()):
        return {}
    delta = max(len(nbrs) for nbrs in graph.adj.values())
    padded = pad_to_regular(graph, delta)
    real_edges = {(u, v) for u in graph.U for v in graph.adj[u]}

    dp_layers = {}
    for layer_count in range(delta):
        _size, pair_u, _pair_v = hopcroft_karp_algorithm(padded)
        for u, v in pair_u.items():
            if v is None:
                continue
            padded.adj[u].remove(v)
            padded.adj[v].remove(u)
            if (u, v) in real_edges:
                dp_layers.setdefault(u, {})[v] = layer_count
                real_edges.discard((u, v))
    return dp_layers
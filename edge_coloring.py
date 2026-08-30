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

    for x in sorted(must):
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
    u_list, v_list = sorted(graph.U), sorted(graph.V)
    n = max(len(u_list), len(v_list))
    u_list += [(i, "PAD_D") for i in range (n - len(u_list))]
    v_list += [(i, "PAD_A") for i in range (n - len(v_list))]

    adj = {v: [] for v in u_list + v_list}
    for u in sorted(graph.U):
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


def euler_halve(edges: list, ids: list):
    """Deal alternate edges of each closed walk into two halves.

    Every vertex has even degree, so a walk can only run out of edges back where
    it started, and a closed walk in a bipartite graph has even length. Taking
    every other edge therefore hands each half exactly half of every degree.
    """
    incident = {}
    for i in ids:
        u, v = edges[i]
        incident.setdefault(u, []).append(i)
        incident.setdefault(v, []).append(i)

    def leave(node):
        while incident[node]:
            i = incident[node].pop()
            if i not in walked:
                return i

    walked, halves = set(), ([], [])
    for start in list(incident):
        node, position, i = start, 0, leave(start)
        while i is not None:
            walked.add(i)
            halves[position % 2].append(i)
            u, v = edges[i]
            node, position = (v if node == u else u), position + 1
            i = leave(node)
    return halves


def peel_perfect_matching(edges: list, ids: list):
    """Lift one matching out so the remaining degree is even everywhere.

    Parallel edges collapse when the helper graph is built, which is harmless:
    Hall's condition only cares which vertices are adjacent, not how often.
    """
    helper, first_edge = BipartiteGraph(), {}
    for i in ids:
        u, v = edges[i]
        helper.add_vertex(u, "data")
        helper.add_vertex(v, "ancilla")
        helper.add_edge(u, v)
        first_edge.setdefault((u, v), i)

    _size, pair_u, _pair_v = hopcroft_karp_algorithm(helper)
    matched = {first_edge[(u, v)] for u, v in pair_u.items() if v is not None}
    return list(matched), [i for i in ids if i not in matched]


def edge_color_euler(graph: BipartiteGraph):
    """Halve the degree repeatedly instead of peeling one matching per layer.

    Costs O(E log delta) against O(delta * E * sqrt(V)) for the matching route,
    which only pays off once delta is large; QEC codes keep it small.
    """
    if not any(graph.adj.values()):
        return {}
    delta = max(len(nbrs) for nbrs in graph.adj.values())
    padded = pad_to_regular(graph, delta)

    edges = [(u, v) for u in sorted(padded.U) for v in padded.adj[u]]

    def split(ids, remaining):
        if not ids:
            return []
        if remaining == 1:
            return [ids]
        if remaining % 2:
            matched, rest = peel_perfect_matching(edges, ids)
            return [matched] + split(rest, remaining - 1)
        first, second = euler_halve(edges, ids)
        return split(first, remaining // 2) + split(second, remaining // 2)

    real_edges = {(u, v) for u in graph.U for v in graph.adj[u]}
    dp_layers = {}
    for layer_count, group in enumerate(split(list(range(len(edges))), delta)):
        for i in group:
            u, v = edges[i]
            if (u, v) in real_edges:
                dp_layers.setdefault(u, {})[v] = layer_count
                real_edges.discard((u, v))
    return dp_layers
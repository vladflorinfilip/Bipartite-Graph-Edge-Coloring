from bipartite_g import BipartiteGraph
import copy

def hopcroft_karp_algorithm(graph: BipartiteGraph) -> tuple[int, dict, dict]:
    pair_u = {u: None for u in graph.U}
    pair_v = {v: None for v in graph.V}
    dist = {u: float('inf') for u in graph.U}

    def bfs():
        queue = []
        for u in graph.U:
            if pair_u[u] is None:
                dist[u] = 0
                queue.append(u)
            else:
                dist[u] = float('inf')
        dist[None] = float('inf')

        while queue:
            u = queue.pop(0)
            if dist[u] < dist[None]:
                for v in graph.adj[u]:
                    u2 = pair_v[v]
                    if dist[u2] == float('inf'):
                        dist[u2] = dist[u] + 1
                        queue.append(u2)
        
        return dist[None] != float('inf')

    def dfs(u):
        if u is None:
            return True
        for v in graph.adj[u]:
            if dist[pair_v[v]] == dist[u] + 1 and dfs(pair_v[v]):
                pair_u[u] = v
                pair_v[v] = u
                return True
        dist[u] = float('inf')
        return False
    
    matching = 0
    while bfs():
        for u in graph.U:
            if pair_u[u] is None and dfs(u):
                matching += 1
    return matching, pair_u, pair_v

def cover_max_degree(graph: BipartiteGraph, pair_u: dict, pair_v: dict):
    """Rematch so every leftover max-degree data qubit is paired (same matching size)."""
    delta = max(len(nbrs) for nbrs in graph.adj.values())
    must = {u for u in graph.U if len(graph.adj[u]) == delta}

    def steal(start):
        prev = {start: None}
        queue = [start]
        seen = {start}
        while queue:
            u = queue.pop(0)
            for v in graph.adj[u]:
                if v in seen or pair_u[u] == v:
                    continue
                prev[v] = u
                seen.add(v)
                u2 = pair_v[v]
                if u2 is None or u2 not in must:
                    while v is not None:
                        u = prev[v]
                        pair_u[u], pair_v[v], v = v, u, prev.get(u)
                    if u2 is not None:
                        pair_u[u2] = None
                    return
                if u2 not in seen:
                    prev[u2] = v
                    seen.add(u2)
                    queue.append(u2)

    for u in must:
        if pair_u[u] is None:
            steal(u)


def edge_color_hk(graph: BipartiteGraph):
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
from bipartite_g import BipartiteGraph

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
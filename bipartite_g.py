class BipartiteGraph:
    def __init__(self):
        self.U = set()
        self.V = set()
        self.adj = {}

    def add_vertices(self, vertices, kind):
        for vertex in vertices:
            self.add_vertex(vertex, kind)

    def add_vertex(self, vertex, kind):
        if kind == "data":
            self.U.add(vertex)
        elif kind == "ancilla":
            self.V.add(vertex)
        else:
            raise ValueError("Vertex kind must be 'data' or 'ancilla'")
        self.adj.setdefault(vertex, [])

    def add_edge(self, u, v):
        if (u in self.U and v in self.V) or (u in self.V and v in self.U):
            if v not in self.adj[u]:
                self.adj[u].append(v)
            if u not in self.adj[v]:
                self.adj[v].append(u)
        else:
            raise ValueError("Edge must connect a data qubit to an ancilla")
    
    def add_edges(self, u, edges):
        for edge in edges:
            self.add_edge(u, edge)

    def print_graph(self):
        for u in self.U:
            print(f"{u}: {self.adj[u]}")
        for v in self.V:
            print(f"{v}: {self.adj[v]}")
    
    def is_bipartite(self):
        for u in self.U:
            for v in self.adj[u]:
                if v in self.U:
                    return False
        for v in self.V:
            for u in self.adj[v]:
                if u in self.V:
                    return False
        return True

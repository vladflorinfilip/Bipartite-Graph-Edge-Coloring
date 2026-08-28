from bipartite_g import BipartiteGraph


def initialize_graph(nx: int, nz: int, n: int, edges_x: list, edges_z: list):
    """Seed X and Z Tanner graphs with n data qubits and the given check–data edges."""
    Tanner_graph = BipartiteGraph()

    all_data = [(i, "D") for i in range(n)]
    all_x = [(i, "X") for i in range(nx)]
    all_z = [(i, "Z") for i in range(nz)]

    Tanner_graph.add_vertices(all_x, "ancilla")
    Tanner_graph.add_vertices(all_z, "ancilla")
    Tanner_graph.add_vertices(all_data, "data")

    for i, j in edges_x:
        Tanner_graph.add_edge((i, "X"), (j, "D"))

    for i, j in edges_z:
        Tanner_graph.add_edge((i, "Z"), (j, "D"))

    return Tanner_graph


def complete_edges(n_checks: int, n_data: int) -> list[tuple[int, int]]:
    return [(i, j) for i in range(n_checks) for j in range(n_data)]


def complete_args(nx: int, nz: int, n: int):
    return nx, nz, n, complete_edges(nx, n), complete_edges(nz, n)


def complete_graph(nx: int, nz: int, n: int):

    return initialize_graph(*complete_args(nx, nz, n))


# Steane [[7, 1, 3]]
STEANE_H = (
    (1, 0, 1, 0, 1, 0, 1),
    (0, 1, 1, 0, 0, 1, 1),
    (0, 0, 0, 1, 1, 1, 1),
)
STEANE_EDGES = [
    (i, j) for i, row in enumerate(STEANE_H) for j, bit in enumerate(row) if bit
]


def steane_graph():
    return initialize_graph(3, 3, 7, STEANE_EDGES, STEANE_EDGES)


def toric_edges(d: int):
    """Qubits sit on the lines of a d x d grid that wraps around at the borders."""
    horizontal = lambda r, c: (r % d) * d + (c % d)
    vertical = lambda r, c: d * d + (r % d) * d + (c % d)

    edges_x, edges_z = [], []
    for r in range(d):
        for c in range(d):
            check = r * d + c
            # star
            edges_x += [
                (check, horizontal(r, c)),
                (check, horizontal(r, c - 1)),
                (check, vertical(r, c)),
                (check, vertical(r - 1, c)),
            ]
            # plaquette
            edges_z += [
                (check, horizontal(r, c)),
                (check, horizontal(r + 1, c)),
                (check, vertical(r, c)),
                (check, vertical(r, c + 1)),
            ]
    return edges_x, edges_z


def toric_graph(d: int):
    """Toric code of distance d >= 3: 2*d*d data qubits, d*d checks of each type."""
    return initialize_graph(d * d, d * d, 2 * d * d, *toric_edges(d))

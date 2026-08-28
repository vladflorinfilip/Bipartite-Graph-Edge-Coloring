"""Shared Tanner graphs for tests. Edges are (check_index, data_index)."""
from main import initialize_graph

def complete_edges(n_checks: int, n_data: int) -> list[tuple[int, int]]:
    return [(i, j) for i in range(n_checks) for j in range(n_data)]


def complete_args(nx: int, nz: int, n: int):
    return nx, nz, n, complete_edges(nx, n), complete_edges(nz, n)


def complete_graph(nx: int, nz: int, n: int):

    return initialize_graph(*complete_args(nx, nz, n))


# Steane [[7, 1, 3]]: HX = HZ = the [7, 4, 3] Hamming matrix.
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

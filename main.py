"""Compare the scheduling algorithms on a set of CSS codes.

Every algorithm turns a Tanner graph into dp_layers, so they are judged on the
same three numbers: how long they took, how many layers they need, and whether
any ordering pair is left broken at the end.
"""

import time

from edge_coloring import edge_color_regular
from graphs import steane_graph, toric_graph
from multigraph_algorithm import (
    combine_x_and_z_graphs_naive,
    combine_x_and_z_graphs_packed,
    multigraph_algorithm,
)
from stencils import (
    check_no_layer_contains_two_incident_edges,
    check_ordering_constraint,
    fix_ordering_constraint_min_distance,
    fix_ordering_constraint_trailing_layer,
    layers_from_dp,
)


def interleaved_with_fix(graph, fix):
    """Colour X and Z together in delta layers, then repair the broken pairs."""
    dp_layers = edge_color_regular(graph)
    return fix(dp_layers, check_ordering_constraint(dp_layers))


ALGORITHMS = (
    ("interleaved + min_distance",
     lambda graph: interleaved_with_fix(graph, fix_ordering_constraint_min_distance)),
    ("interleaved + trailing",
     lambda graph: interleaved_with_fix(graph, fix_ordering_constraint_trailing_layer)),
    ("X-then-Z naive", lambda graph: multigraph_algorithm(graph, combine_x_and_z_graphs_naive)),
    ("X-then-Z packed", lambda graph: multigraph_algorithm(graph, combine_x_and_z_graphs_packed)),
)

GRAPHS = (
    ("steane", steane_graph),
    ("toric d=3", lambda: toric_graph(3)),
    ("toric d=4", lambda: toric_graph(4)),
    ("toric d=5", lambda: toric_graph(5)),
)


def measure(algorithm, graph) -> dict:
    start = time.perf_counter()
    dp_layers = algorithm(graph)
    seconds = time.perf_counter() - start
    return {
        "seconds": seconds,
        "layers": len(layers_from_dp(dp_layers)),
        "broken": len(check_ordering_constraint(dp_layers)),
        "valid": check_no_layer_contains_two_incident_edges(dp_layers),
    }


def lower_bound(graph) -> int:
    """No schedule can beat the busiest vertex, and Konig says that bound is tight."""
    return max(len(nbrs) for nbrs in graph.adj.values())


def main():
    results = {}
    for graph_name, build in GRAPHS:
        bound = lower_bound(build())
        print("=== %s (lower bound %d layers) ===" % (graph_name, bound))
        print("%-28s %-8s %-8s %-7s %s" % ("algorithm", "layers", "broken", "valid", "seconds"))
        for algorithm_name, algorithm in ALGORITHMS:
            got = measure(algorithm, build())
            results[(graph_name, algorithm_name)] = got
            print("%-28s %-8d %-8d %-7s %.6f" % (
                algorithm_name, got["layers"], got["broken"],
                "yes" if got["valid"] else "NO", got["seconds"]))
        print()

if __name__ == "__main__":
    main()

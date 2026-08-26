from bipartite_g import BipartiteGraph
from algorithms import edge_color_hk
import time
from stencils import check_ordering_constraint, fix_ordering_constraint, layers_from_dp


def initialize_graph(nx: int, nz: int, n: int):
    """Seed X and Z Tanner graphs with n data qubits and a matching of checks."""
    Tanner_graph = BipartiteGraph()

    all_data = [(i, "D") for i in range(n)]
    all_x = [(i, "X") for i in range(nx)]
    all_z = [(i, "Z") for i in range(nz)]

    Tanner_graph.add_vertices(all_x, "ancilla")
    Tanner_graph.add_vertices(all_z, "ancilla")
    Tanner_graph.add_vertices(all_data, "data")

    for d in all_data:
        Tanner_graph.add_edges(d, all_x)
        Tanner_graph.add_edges(d, all_z)

    return Tanner_graph

def __main__():
    Tanner_graph = initialize_graph(1, 1, 601)

    # print("Tanner graph:\n")
    # Tanner_graph.print_graph()

    print("--------------------------------")
    print("Hopcroft-Karp algorithm:\n")

    start_time_color     = time.time()
    dp_layers = edge_color_hk(Tanner_graph)
    end_time_color = time.time()

    broken = check_ordering_constraint(dp_layers)
    print("Broken before fix:", len(broken))
    print(f"Time taken to color edges: {end_time_color - start_time_color:.6f} seconds")
    print("Layers before fix:\n")
    layers = layers_from_dp(dp_layers)
    print(len(layers))
    # for layer in layers:
    #     print(layer)

    start_time_fix = time.time()
    dp_layers = fix_ordering_constraint(dp_layers, broken)
    end_time_fix = time.time()

    print("--------------------------------")
    print("Fixing ordering constraint:\n")

    print("Broken after fix:", len(check_ordering_constraint(dp_layers)))
    print(f"Time taken to fix ordering constraint: {end_time_fix - start_time_fix:.6f} seconds")

    print("--------------------------------")
    print("Total time taken: {end_time_fix - start_time_color:.6f} seconds")
    print("Final layers:\n")
    layers = layers_from_dp(dp_layers)
    print(len(layers))
    # for layer in layers:
    #     print(layer)


if __name__ == "__main__":
    __main__()

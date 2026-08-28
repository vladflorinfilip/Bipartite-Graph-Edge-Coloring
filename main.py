from edge_coloring import edge_color_max, edge_color_regular
import time
from graphs import complete_graph, steane_graph
from stencils import check_ordering_constraint, fix_ordering_constraint, layers_from_dp, check_no_layer_contains_two_incident_edges


def __main__():
    Tanner_graph = steane_graph()

    # print("Tanner graph:\n")
    # Tanner_graph.print_graph()

    print("--------------------------------")
    print("Hopcroft-Karp algorithm:\n")

    start_time_color = time.time()
    dp_layers = edge_color_regular(Tanner_graph)
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
    print(f"Total time taken: {end_time_fix - start_time_color:.6f} seconds")
    print("Final layers:\n")
    layers = layers_from_dp(dp_layers)
    print(len(layers))
    # for layer in layers:
    #     print(layer)

    check = check_no_layer_contains_two_incident_edges(dp_layers)
    print("Checking no layer contains two incident edges:", check)
    if not check:
        print("Error: No layer contains two incident edges")
        return


if __name__ == "__main__":
    __main__()

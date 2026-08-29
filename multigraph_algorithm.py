from edge_coloring import edge_color_regular
from bipartite_g import BipartiteGraph

def multigraph_algorithm(graph: BipartiteGraph):
    # Separate the graph into X and Z graphs
    x_graph = graph.copy()
    z_graph = graph.copy()
    for u in list(x_graph.V):
        if u[1] == "Z":
            x_graph.remove_vertex(u)
    for u in list(z_graph.V):
        if u[1] == "X":
            z_graph.remove_vertex(u)

    # Color the X and Z graphs
    x_dp_layers = edge_color_regular(x_graph)
    z_dp_layers = edge_color_regular(z_graph)

    # Combine the X and Z graphs
    return combine_x_and_z_graphs_naive(x_dp_layers, z_dp_layers)

def combine_x_and_z_graphs_naive(x_dp_layers, z_dp_layers):
    # Combine the X and Z graphs, every Z edge landing after every X edge
    delta_x = 1 + max(t for checks in x_dp_layers.values() for t in checks.values())
    dp_layers = {d: dict(checks) for d, checks in x_dp_layers.items()}
    for d, checks in z_dp_layers.items():
        for v, t in checks.items():
            dp_layers.setdefault(d, {})[v] = t + delta_x
    return dp_layers
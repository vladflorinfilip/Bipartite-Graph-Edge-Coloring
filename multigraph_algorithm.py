from edge_coloring import edge_color_regular
from bipartite_g import BipartiteGraph

def multigraph_algorithm(graph: BipartiteGraph, combine=None):
    """Separate the graph into X and Z graphs"""
    x_graph = graph.copy()
    z_graph = graph.copy()
    for u in list(x_graph.V):
        if u[1] == "Z":
            x_graph.remove_vertex(u)
    for u in list(z_graph.V):
        if u[1] == "X":
            z_graph.remove_vertex(u)

    """Color the X and Z graphs"""
    x_dp_layers = edge_color_regular(x_graph)
    z_dp_layers = edge_color_regular(z_graph)

    """Combine the X and Z graphs"""
    return (combine or combine_x_and_z_graphs_naive)(x_dp_layers, z_dp_layers)

def combine_x_and_z_graphs_naive(x_dp_layers, z_dp_layers):
    """Combine the X and Z graphs, every Z edge landing after every X edge"""
    delta_x = 1 + max(t for checks in x_dp_layers.values() for t in checks.values())
    dp_layers = {d: dict(checks) for d, checks in x_dp_layers.items()}
    for d, checks in z_dp_layers.items():
        for v, t in checks.items():
            dp_layers.setdefault(d, {})[v] = t + delta_x
    return dp_layers

def combine_x_and_z_graphs_packed(x_dp_layers, z_dp_layers):
    """Slot Z edges into spare X layers, then colour and append whatever is left."""
    delta_x = 1 + max(t for checks in x_dp_layers.values() for t in checks.values())
    dp_layers = {d: dict(checks) for d, checks in x_dp_layers.items()}

    busy = {}
    for d, checks in x_dp_layers.items():
        for v, t in checks.items():
            busy.setdefault(d, set()).add(t)
            busy.setdefault(v, set()).add(t)

    leftover = []
    for d, checks in z_dp_layers.items():
        d_slots = busy.setdefault(d, set())
        window = range(max(d_slots, default=-1) + 1, delta_x)

        for v in sorted(checks, key=checks.get):
            v_slots = busy.setdefault(v, set())
            slot = next((t for t in window if t not in d_slots and t not in v_slots), None)
            if slot is None:
                leftover.append((d, v))
                continue
            dp_layers.setdefault(d, {})[v] = slot
            d_slots.add(slot)
            v_slots.add(slot)

    tail = BipartiteGraph()
    for d, v in leftover:
        tail.add_vertex(d, "data")
        tail.add_vertex(v, "ancilla")
        tail.add_edge(d, v)
    tail_dp_layers = edge_color_regular(tail)
    
    return combine_x_and_z_graphs_naive(dp_layers, tail_dp_layers)
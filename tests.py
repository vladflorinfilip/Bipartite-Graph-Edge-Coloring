from edge_coloring import edge_color_max, edge_color_regular
from graphs import complete_graph, steane_graph, toric_graph
from maximum_matching import hopcroft_karp_algorithm
from stencils import (
    check_ordering_constraint,
    fix_ordering_constraint,
    layers_from_dp,
)


def test_is_bipartite():
    assert complete_graph(1, 3, 5).is_bipartite()
    assert complete_graph(2, 3, 5).is_bipartite()
    assert complete_graph(100, 100, 100).is_bipartite()
    assert steane_graph().is_bipartite()
    assert toric_graph(3).is_bipartite()


def test_hopcroft_karp_algorithm():
    layer, _, _ = hopcroft_karp_algorithm(complete_graph(1, 1, 2))
    assert layer == 2

    layer, _, _ = hopcroft_karp_algorithm(complete_graph(1, 3, 5))
    assert layer == 4

    layer, _, _ = hopcroft_karp_algorithm(complete_graph(200, 300, 1000))
    assert layer == 500

    layer, _, _ = hopcroft_karp_algorithm(steane_graph())
    assert layer == 6


def test_edge_color_regular():
    def n_layers(graph):
        dp = edge_color_regular(graph)
        return 1 + max(t for checks in dp.values() for t in checks.values())

    assert n_layers(complete_graph(1, 1, 10)) == 10
    assert n_layers(complete_graph(1, 3, 6)) == 6
    assert n_layers(complete_graph(1, 3, 5)) == 5
    assert n_layers(complete_graph(4, 4, 79)) == 79
    assert n_layers(complete_graph(4, 4, 80)) == 80
    assert n_layers(complete_graph(4, 4, 81)) == 81
    assert n_layers(steane_graph()) == 6


def _assert_layers_are_matchings(dp_layers):
    for layer in layers_from_dp(dp_layers):
        data = [d for d, _ in layer]
        checks = [v for _, v in layer]
        assert len(data) == len(set(data))
        assert len(checks) == len(set(checks))


def test_check_ordering_constraint():
    d0, d1 = (0, "D"), (1, "D")
    x, z = (0, "X"), (0, "Z")
    even = {
        d0: {x: 0, z: 1},
        d1: {x: 0, z: 1},
    }
    assert check_ordering_constraint(even) == []

    odd = {
        d0: {x: 0, z: 1},
        d1: {x: 1, z: 0},
    }
    broken = check_ordering_constraint(odd)
    assert len(broken) == 1
    assert broken[0][0] == x and broken[0][1] == z
    assert len(broken[0][3]) % 2 == 1


def test_fix_ordering_constraint_handmade():
    d0, d1 = (0, "D"), (1, "D")
    x, z = (0, "X"), (0, "Z")
    dp = {
        d0: {x: 0, z: 1},
        d1: {x: 1, z: 0},
    }
    broken = check_ordering_constraint(dp)
    dp = fix_ordering_constraint(dp, broken)
    assert check_ordering_constraint(dp) == []
    _assert_layers_are_matchings(dp)


def test_fix_ordering_constraint_after_coloring():
    for color in (edge_color_max, edge_color_regular):
        for graph in (
            complete_graph(1, 1, 2),
            complete_graph(1, 1, 4),
            complete_graph(1, 3, 4),
            complete_graph(2, 2, 4),
            steane_graph(),
        ):
            dp = color(graph)
            for _ in range(5):
                broken = check_ordering_constraint(dp)
                if not broken:
                    break
                dp = fix_ordering_constraint(dp, broken)
            assert check_ordering_constraint(dp) == []
            _assert_layers_are_matchings(dp)


def test_layers_from_dp():
    d0, d1 = (0, "D"), (1, "D")
    x, z = (0, "X"), (0, "Z")
    dp = {
        d0: {x: 0, z: 1},
        d1: {x: 1, z: 0},
    }
    layers = layers_from_dp(dp)
    assert (d0, x) in layers[0] and (d1, z) in layers[0]
    assert (d0, z) in layers[1] and (d1, x) in layers[1]

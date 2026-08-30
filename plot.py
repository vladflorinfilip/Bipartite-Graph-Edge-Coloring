"""Draw main.py's comparison tables into results.png."""

import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from edge_coloring import pad_to_regular
from main import ALGORITHMS, COLOURERS, COLOURING_GRAPHS, GRAPHS, lower_bound
from stencils import layers_from_dp

REPEATS = 5


def collect(run, build):
    """None means the fixer gave up, which is worth drawing rather than hiding."""
    try:
        dp_layers = run(build())
    except RuntimeError:
        return None
    times = []
    for _ in range(REPEATS):
        graph = build()
        start = time.perf_counter()
        run(graph)
        times.append(time.perf_counter() - start)
    return {"layers": len(layers_from_dp(dp_layers)), "seconds": min(times)}


def run_all(graphs, methods, label_of):
    rows = []
    for name, build in graphs:
        graph = build()
        results = {method: collect(run, build) for method, run in methods}
        rows.append((label_of(name, graph), lower_bound(graph), results))
    return rows


def padding_label(name, graph):
    edges = sum(len(nbrs) for nbrs in graph.adj.values())
    padded = sum(len(nbrs) for nbrs in pad_to_regular(graph, lower_bound(graph)).adj.values())
    return "%s\nx%.1f padding" % (name, padded / edges)


def bars(axis, rows, methods, key, fmt, title, ylabel, bound=False):
    width = 0.8 / len(methods)
    for index, method in enumerate(methods):
        got = [row[2][method] for row in rows]
        heights = [0 if result is None else result[key] for result in got]
        offset = index * width - 0.4 + width / 2
        drawn = axis.bar([column + offset for column in range(len(rows))],
                         heights, width, label=method)
        axis.bar_label(drawn, fontsize=6, padding=2,
                       labels=["gave up" if result is None else fmt(height)
                               for result, height in zip(got, heights)])

    if bound:
        for column, row in enumerate(rows):
            axis.hlines(row[1], column - 0.45, column + 0.45, color="black", ls="--", lw=1.2)
        axis.plot([], [], color="black", ls="--", lw=1.2, label=r"lower bound $\Delta$")

    # log throughout
    axis.set_yscale("log")
    axis.set_xticks(range(len(rows)))
    axis.set_xticklabels([row[0] for row in rows], rotation=15, ha="right", fontsize=8)
    axis.set_title(title, fontsize=10)
    axis.set_ylabel(ylabel)
    axis.legend(fontsize=7)
    axis.grid(axis="y", alpha=0.3, lw=0.5)
    axis.set_axisbelow(True)


def main():
    colouring = run_all(COLOURING_GRAPHS, COLOURERS, padding_label)
    schedules = run_all(GRAPHS, ALGORITHMS, lambda name, graph: name)
    layers = lambda value: "%d" % value
    seconds = lambda value: "%.2fms" % (value * 1e3)

    figure, axes = plt.subplots(2, 2, figsize=(13, 9))
    bars(axes[0][0], colouring, [name for name, _ in COLOURERS], "layers", layers,
         "Edge colouring: every method reaches the optimum", "layers (log)", bound=True)
    bars(axes[0][1], colouring, [name for name, _ in COLOURERS], "seconds", seconds,
         "Edge colouring: cost of the guarantee", "seconds (log)")
    bars(axes[1][0], schedules, [name for name, _ in ALGORITHMS], "layers", layers,
         "Full schedule: the repair is what costs layers", "layers (log)", bound=True)
    bars(axes[1][1], schedules, [name for name, _ in ALGORITHMS], "seconds", seconds,
         "Full schedule: runtime", "seconds (log)")

    figure.tight_layout()
    figure.savefig("results.png", dpi=150)


if __name__ == "__main__":
    main()

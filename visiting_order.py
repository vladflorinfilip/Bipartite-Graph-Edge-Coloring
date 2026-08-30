"""Schedule by choosing the order in which each check visits its data qubits.

The ordering constraint only ever asks, at a shared data qubit, whether the X
check acts before the Z check. That answer is fixed by the two visiting orders
alone, so searching over orders keeps parity in view from the start instead of
colouring edges first and discovering broken pairs afterwards.
"""

import math
import random
import time
from itertools import permutations

from edge_coloring import edge_color_regular
from stencils import (
    check_no_layer_contains_two_incident_edges,
    check_ordering_constraint,
)

COMPASS = ("N", "W", "E", "S")
CONFLICT_WEIGHT = 10


def schedule_from_orders(orders: dict) -> dict:
    """Turn {check: [qubit at t=0, qubit at t=1, ...]} into dp_layers."""
    dp_layers = {}
    for check, qubits in orders.items():
        for t, d in enumerate(qubits):
            dp_layers.setdefault(d, {})[check] = t
    return dp_layers


def orders_from_schedule(dp_layers: dict) -> dict:
    """Read dp_layers back as one visiting order per check."""
    slots = {}
    for d, checks in dp_layers.items():
        for check, t in checks.items():
            slots.setdefault(check, {})[t] = d
    return {check: [qs[t] for t in sorted(qs)] for check, qs in slots.items()}


def is_valid(dp_layers: dict) -> bool:
    """A schedule nothing can complain about: a proper colouring with even parities."""
    return check_no_layer_contains_two_incident_edges(dp_layers) and not check_ordering_constraint(dp_layers)


def toric_compass_orders(d: int, star_order=COMPASS, plaquette_order=COMPASS) -> dict:
    """Every star and every plaquette walks the compass the same way."""
    horizontal = lambda r, c: (r % d) * d + (c % d)
    vertical = lambda r, c: d * d + (r % d) * d + (c % d)

    orders = {}
    for r in range(d):
        for c in range(d):
            star = {
                "N": vertical(r - 1, c),
                "W": horizontal(r, c - 1),
                "E": horizontal(r, c),
                "S": vertical(r, c),
            }
            plaquette = {
                "N": horizontal(r, c),
                "W": vertical(r, c),
                "E": vertical(r, c + 1),
                "S": horizontal(r + 1, c),
            }
            check = r * d + c
            orders[(check, "X")] = [(star[side], "D") for side in star_order]
            orders[(check, "Z")] = [(plaquette[side], "D") for side in plaquette_order]
    return orders


def search_toric_compass(d: int) -> list:
    """All compass pairs that schedule the toric code in delta layers."""
    good = []
    for star_order in permutations(COMPASS):
        for plaquette_order in permutations(COMPASS):
            dp_layers = schedule_from_orders(toric_compass_orders(d, star_order, plaquette_order))
            if is_valid(dp_layers):
                good.append((star_order, plaquette_order))
    return good


class VisitingOrderSearch:
    """Anneal over visiting orders, scoring qubit clashes alongside broken pairs.

    Clashes are weighted heavily because a schedule that double-books a qubit is
    not a schedule at all, whereas a broken pair is merely wrong.
    """

    def __init__(self, graph, delta: int = None, seed: int = 0, shuffle: bool = False):
        self.rng = random.Random(seed)
        self.delta = delta or max(len(nbrs) for nbrs in graph.adj.values())
        self.checks = [v for v in graph.adj if v[1] in "XZ"]

        self.time_of = {check: {} for check in self.checks}
        for d, checks in edge_color_regular(graph).items():
            for check, t in checks.items():
                self.time_of[check][d] = t
        if shuffle:
            for slots in self.time_of.values():
                times = list(slots.values())
                self.rng.shuffle(times)
                slots.update(zip(list(slots), times))

        self.at_qubit, self.conflicts = {}, 0
        for slots in self.time_of.values():
            for d, t in slots.items():
                self._occupy(d, t, +1)

        self.pairs_of = {check: [] for check in self.checks}
        for x in (c for c in self.checks if c[1] == "X"):
            for z in (c for c in self.checks if c[1] == "Z"):
                shared = tuple(set(graph.adj[x]) & set(graph.adj[z]))
                if shared:
                    self.pairs_of[x].append((x, z, shared))
                    self.pairs_of[z].append((x, z, shared))

        self.odd = {}
        for pairs in self.pairs_of.values():
            for pair in pairs:
                self.odd[pair[:2]] = self._parity(pair)
        self.broken = sum(self.odd.values())

    def _occupy(self, d, t, step):
        slots = self.at_qubit.setdefault(d, {})
        count = slots.get(t, 0)
        self.conflicts -= max(0, count - 1)
        slots[t] = count + step
        self.conflicts += max(0, slots[t] - 1)

    def _parity(self, pair):
        x, z, shared = pair
        return sum(self.time_of[x][d] < self.time_of[z][d] for d in shared) % 2

    def score(self) -> int:
        return CONFLICT_WEIGHT * self.conflicts + self.broken

    def snapshot(self) -> dict:
        dp_layers = {}
        for check, slots in self.time_of.items():
            for d, t in slots.items():
                dp_layers.setdefault(d, {})[check] = t
        return dp_layers

    def retime(self, check, moves):
        """Apply [(qubit, new time)] for one check and refresh the parities it touches."""
        for d, _ in moves:
            self._occupy(d, self.time_of[check][d], -1)
        for d, t in moves:
            self.time_of[check][d] = t
            self._occupy(d, t, +1)
        for pair in self.pairs_of[check]:
            fresh = self._parity(pair)
            self.broken += fresh - self.odd[pair[:2]]
            self.odd[pair[:2]] = fresh

    def propose(self):
        """Either swap two of a check's slots, or shift one edge into a slot it never uses."""
        check = self.rng.choice(self.checks)
        used = self.time_of[check]
        free = [t for t in range(self.delta) if t not in used.values()]
        if len(used) > 1 and (not free or self.rng.random() < 0.5):
            first, second = self.rng.sample(list(used), 2)
            return check, [(first, used[second]), (second, used[first])]
        if not free:
            return None, None
        d = self.rng.choice(list(used))
        return check, [(d, self.rng.choice(free))]

    def run(self, seconds: float = 20.0, temperature: float = 3.0, cooling: float = 0.99995):
        best, best_state = self.score(), self.snapshot()
        deadline = time.time() + seconds
        while time.time() < deadline and best > 0:
            check, moves = self.propose()
            if check is None:
                continue
            before = self.score()
            undo = [(d, self.time_of[check][d]) for d, _ in moves]
            self.retime(check, moves)
            after = self.score()
            if after <= before or self.rng.random() < math.exp((before - after) / max(temperature, 1e-9)):
                if after < best:
                    best, best_state = after, self.snapshot()
            else:
                self.retime(check, undo)
            temperature *= cooling
        return best, best_state


def search_visiting_orders(graph, seconds: float = 20.0, restarts: int = 1, **kwargs):
    """Best schedule found across a few annealing restarts."""
    best, best_state = None, None
    for seed in range(restarts):
        score, dp_layers = VisitingOrderSearch(graph, seed=seed, shuffle=seed > 0, **kwargs).run(seconds=seconds)
        if best is None or score < best:
            best, best_state = score, dp_layers
        if best == 0:
            break
    return best, best_state

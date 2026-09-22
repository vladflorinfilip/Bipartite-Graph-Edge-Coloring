# Scheduling Fault-Tolerant Syndrome Extraction Circuits

_by **Vlad Filip**_

_AI disclaimer:_ I used AI assistance to search the literature, summarise existing edge-colouring algorithms, and weigh different approaches before writing any code — particularly around graph colouring strategies. The layer-maximisation heuristic, the padding trick, the fix for the ordering constraint, and the split-and-recombine (X-then-Z) design are my own ideas, developed independently of that research pass.

## Repository layout
Run `python main.py` to reproduce the full comparison across every method below, and `python plot.py` to regenerate the figure referenced in the Results section.

* `bipartite_g.py` — the `BipartiteGraph` class
* `graphs.py` — test fixtures. `initialize_graph` constructs a Tanner graph from qubit counts and two edge lists; built on top of this are a complete bipartite seed graph, the Steane code, and the toric code at arbitrary distance
* `maximum_matching.py` — Hopcroft–Karp maximum matching, the core primitive shared by every colouring routine
* `edge_coloring.py` — the three colouring strategies
* `stencils.py` — logic for enforcing the ordering constraint
* `multigraph_algorithm.py` — the X-then-Z construction: split the graph in two, colour each half separately, then recombine either naively or via the bin-packing combiner
* `main.py` — runs every colourer and every scheduling strategy against the fixtures, printing layer counts, broken pairs, and timings
* `plot.py` — turns those same results into `results.png`
* `tests.py` — unit tests

## Edge colouring

A bipartite graph splits its vertices into two disjoint groups, with every edge running between the groups and never within one. Scheduling each edge into a non-conflicting time slot — a "layer" — is exactly the edge-colouring problem: no layer may contain two edges sharing a vertex. This is classical territory in graph theory; König's edge-colouring theorem guarantees that a bipartite graph's chromatic index equals its maximum degree, $\Delta$. So the theoretical floor on the number of layers is $\Delta$, and the question is how close a practical algorithm gets to it.

I evaluated three candidate approaches:

1. **Hopcroft–Karp matching**, running at $O(\Delta E\sqrt{V})$. Each call pulls one maximum matching — a single layer's worth of edges — out of the graph by alternating breadth-first and depth-first passes: the BFS phase labels every vertex with its distance along the nearest augmenting path (unmatched vertices start at depth zero), and the DFS phase walks that path, alternating between unmatched and matched edges and flipping each one it touches. Once a matching is extracted, its edges are deleted and the process repeats on what remains until nothing is left. The catch is that raw peeling doesn't keep vertex degrees balanced along the way, so a high-degree vertex can get shortchanged early and end up needing extra layers later, pushing the total above $\Delta$. I tried two fixes for this:

    * **Layer-maximisation repair**, which stops any $\Delta$-degree vertex from being left uncovered. Hopcroft–Karp only optimises for matching *size*, not *composition* — a graph typically admits several maximum matchings, and the algorithm hands back an arbitrary one, which is exactly how the imbalance above creeps in. My fix walks an alternating path outward from every uncovered $\Delta$-degree vertex until it hits a vertex that isn't itself at $\Delta$-degree, then flips that path so the important vertex takes the matched slot and the less-constrained one gives it up — the matching stays maximum-sized throughout. Each walk is one $O(V+E)$ BFS, run at most once per uncovered vertex, so the whole repair costs $O(k(V+E))$ per layer with $k$ typically 0 or 1. It pays off in practice: naive peeling needs 8 layers on Steane against a theoretical floor of 6, and this repair closes the gap to exactly 6. Over 2000 randomly generated sparse Tanner graphs, unrepaired peeling blew past $\Delta$ 13.4% of the time, while the repaired version never did. The downside is that it's a heuristic without a formal guarantee — it only fixes coverage within the layer just extracted, and the next layer starts from a fresh set of max-degree vertices in the residual graph.

    * **Regularisation via padding**, which sidesteps the imbalance problem entirely by making every matching perfect. Adding virtual vertices and edges until the graph is $\Delta$-regular guarantees that a single Hopcroft–Karp call peels off exactly $\Delta$ edges cleanly; the virtual structure is then stripped back out to leave a valid colouring. This is provably correct with no need for a repair pass, at the cost of extra graph size — building the padded graph scales as $O(n\Delta)$, where $n$ is the larger side's vertex count, so it gets expensive when the padded edge count dwarfs the real one. That overhead scales with $n\Delta / E$, which conveniently doubles as a measure of how lopsided the original graph is: it's exactly 1 for an already-regular, balanced graph and climbs as one vertex starts to dominate. That's a good fit here, since CSS codes are LDPC by construction — fixed stabiliser weight, fixed qubit degree — so this ratio stays close to 1 across the whole code family. My toric fixtures are already 4-regular, so padding costs nothing extra and the correctness guarantee is essentially free; measured runtime came in about 2.5x faster than the repair route, since there's no repair step to run at all. Steane is smaller and more uneven (qubit 6 sits at degree 6, qubit 0 at degree 2), so padding there costs 1.75x — still comfortably under a tenth of a millisecond.

2. **Euler splitting**, at $O(E\log\Delta)$ when $\Delta$ is a power of two and $O(E\sqrt{V}\log\Delta)$ otherwise. This is a divide-and-conquer strategy: once the graph is padded to $\Delta$-regular, every vertex has an even degree, and a closed walk through the graph always uses edges at each vertex in arrive/leave pairs. Splitting each walk's edges alternately into two sets halves every vertex's degree in one pass, cutting the graph in two. Repeating this recursively drives every degree down to 1, at which point the remaining edges form a perfect matching — one layer. This only works cleanly while degrees stay even; an odd degree forces one Hopcroft–Karp matching extraction to bring it back down to even before the halving can continue — the only point in this method where a matching gets computed at all. That's also what separates the easy and hard cases: $\Delta=4$ on the toric code halves $4\to2\to1$ without ever hitting an odd degree, whereas $\Delta=6$ on Steane splits into two odd 3-regular halves and needs an extra matching step to recover. Edges are tracked by index into a flat list rather than by their endpoint pair, since padding can introduce several parallel edges between the same two vertices and only an index reliably distinguishes them.

3. **Cole–Ost–Schirra**, the asymptotically optimal choice at $O(E\log\Delta)$. I chose not to implement this one — the gain over Euler splitting is marginal here, since it would only remove the odd-degree penalty, and with $\Delta$ at 4 (toric) and 6 (Steane), that penalty is already small relative to $\log\Delta$.

## Ordering constraint

Every X/Z check pair needs to share an even number of qubits with the X check scheduled first. I looked at two ways to enforce this: colour the whole bipartite graph as one unit and patch violations afterward, or split it into separate X and Z graphs up front and combine the results.

### Post-hoc repairs

Starting from a valid $\Delta$-layer colouring, `check_ordering_constraint` scans the graph and evaluates every X-then-Z parity, returning the broken (x, z) pairs along with their parity-check group `S` and shared data-qubit set `I`. I tried two repair strategies on top of that:

1. **Nearest-slot repair** finds, for each broken pair, the shared qubit where the two checks are closest together in layer order, then delays whichever check currently comes first until it sits just after the other — a single fresh layer inserted mid-schedule, flipping the parity of exactly the qubit in question. Each repair costs exactly one extra layer, so total depth ends up at $\Delta$ plus the repair count (12 on Steane: $6+6$; 124 on toric at $d=5$: $4+120$). It has to run over several passes, though, because reordering at one shared qubit flips the parity of every other pair that also touches it — so a repair can re-break pairs that were already fixed. Toric at $d=5$, for instance, starts with 100 broken pairs and needs 120 repairs spread across 3 passes. Since layer count grows linearly with repair count, depth scales with code size even though $\Delta$ itself stays fixed at 4. Complexity is $O(B\cdot E)$ per pass over $B$ broken pairs.

2. **Trailing-layer repair** takes the same underlying fix but appends to a trailing layer instead of inserting mid-schedule, and packs multiple repairs into that trailing layer via `used_d` and `used_check` tracking sets — a new repair joins the current trailing layer unless it collides, in which case the trailing layer advances by one. It ends up needing more total repairs than the nearest-slot approach, since it picks the qubit to fix lazily rather than optimally, but the packing more than makes up for it: it fits roughly 1.4–1.6 repairs per extra layer (8 repairs into 5 extra layers on Steane, for 11 total; 150 repairs into 106 extra layers on toric $d=5$, for 110 total). It's also cheaper per repair — a dictionary write plus two set insertions, versus a full sweep — giving $O(B)$ per pass. It still shares the same core limitation as nearest-slot repair, though: depth keeps growing with the number of broken pairs and with code size.

### Split-graph construction with bin packing

The alternative sidesteps repairs altogether by splitting the bipartite graph into an X sub-graph and a Z sub-graph up front, colouring each independently, and then combining the two valid schedules:

1. **Straight concatenation** simply appends the Z layers after all the X layers, which trivially satisfies the ordering constraint since every Z operation then follows every X operation. The tradeoff is a longer schedule — the total layer count becomes the sum of the two sub-graphs' maximum degrees rather than the shared $\Delta$ — but it needs no repair pass at all, just an $O(1)$ append.

2. **Packed combination** does better: for each Z-side edge $(d, z)$, it looks up where qubit $d$ last appears in the X schedule and tries to slot the edge into the immediately following X layer, provided the colouring allows it, removing it from the Z schedule in the process. If $d$'s last X appearance is already in the final X layer, the edge stays in the Z schedule and gets appended as in the naive case. The packing loop itself runs at $O(E\Delta)$, since each Z edge checks at most $\Delta_x$ candidate layers with $O(1)$ set-membership tests per check. Any edges left unplaced afterward get re-coloured via `edge_color_regular` at $O(\Delta E\sqrt{V})$, which dominates the overall cost — so the combine step doesn't change the asymptotic complexity class of the colouring it's built on, and the packing itself comes essentially free.

## Test fixtures: CSS codes

Calderbank–Shor–Steane (CSS) codes are graphs of physical and ancilla ("check") qubits used to encode logical qubits, with stabilisers correcting bit-flip (X), phase-flip (Z), or combined (Y) errors. I tested against two families: the Steane code (7 physical qubits encoding one logical qubit — a small, fixed block with maximum degree 6 and minimum degree 2), and the toric code (qubits placed on the edges of a periodic 2D lattice, with ancillas on the star and plaquette operators, giving a uniform degree of 4).

## Results

![Layers and runtime for each colouring and scheduling algorithm](results.png)

All three colouring algorithms hit the $\Delta$ floor on every fixture, in under a millisecond on the CSS codes — so among them, the deciding factor is padding overhead rather than output quality. That overhead only really bites on lopsided complete graphs (a 10x padding factor makes the regularised colourer roughly three times slower than the max-cover variant), while on the near-regular toric codes padding costs nothing and comes out ahead.

The results also show clearly that it's the ordering constraint, not the colouring step, that dominates final layer count — which is where I'd say the real difficulty of this problem lives. Post-hoc repair of an interleaved colouring degrades sharply as the code grows: 124 layers on toric $d=5$ against a theoretical floor of 4. The split X-then-Z construction, by contrast, stays flat at 7–8 layers across every fixture tested. My preference is **X-then-Z with the packed combiner** — it's correct by construction and never loses to the naive concatenation on layer count. It does cost more in runtime than the naive version, though, so the right choice ultimately depends on how much that speed difference matters for the target use case.

## Possible extensions

Given more time, I'd implement Cole–Ost–Schirra properly rather than skipping it. I'm also interested in tighter packing strategies for the X-then-Z split — specifically, grouping Z-side edges by parity and finding ways to interleave them into existing X layers rather than strictly appending, which would relax the "Z always after X" rule while preserving parity through the grouping itself. That's riskier than it sounds, though, since a change like that could easily disturb the parity of (x, z) pairs it wasn't meant to touch, so it would need careful handling to avoid trading one bug for another.

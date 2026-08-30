# River Lane Technical Challenege

_written by **Vlad Filip**_

## Edge Coloring
A bipartite graph is a network whose vertices can be split into two groups. Edges on a bipartite graph exclusively connect vertices from different groups, never from the same group. The task of assigning each edge to a layer is effectively an edge coloring algorithm, where no layer contains two edges incident on the same vertex. Edge coloring is a well studied problem within mathematics, where the Koning's line coloring theorem states that the chromatic index of a bipartite graph equals its maximum degree ($\Delta$). This means that the optimal number of layers for a bipartite graph is equal to the $\Delta$.

I have considered 3 ways in which the edge coloring of a bipartite graph can be solved:
1. **Hopcroft-Karp Algorithm:** A fundamental algorithm with a time complexity of $O(\Delta E\sqrt{V})$. This extracts the maximum matching (a layer of maximum members) from the bipartite graph by runing zig-zags between the vertices. The idea of this approach rests on augmenting paths that alternate between free-edge, matched-edge, free-edge, etc.. It does this in two steps: a breadth-first search (a) and a depth-first search (it flips the defined connection in the layer zig-zag). In the (a) search, we check where the nearest augmenting path is and label every vertex in its depth. An unmatched data qubit starts at depth 0. Starting at a node `u`, it finds an umatch vertex `v` and then jumps to its matched pair `pair_v[v]`. This is the zig-zag pattern. The algorithm extracts one matching, then removes the edges from the current bipartite graph and recurses until the graph is empty. Yet, we need to ensure that vertices are balanced as the algorithm iterates so that we are not left with a node with a high degree at the end. This will cause the solution to be suboptimal as we need to spill the edges of that vertex to additional layers. I considered two approaches to this problem:

    * **Maximizing the cover of a layer**, so no $\Delta$-degree vertex is skipped. The HK algorithm maximizes the number of pairs, not which pairs. A graph has different maximum matchings and HP gives you an arbitrary one, running the risk of the additional layers mentioned above. To correct this, after each HK run I take every uncovered $\Delta$-degree vertex and walk an alternating path from it until I reach a vertex that is not itself $\Delta$-degree, then flip that path. The critical vertex takes the slot and the expendable one gives it up, so the matching stays the same size and is still maximum. Each walk is a single BFS at $O(V + E)$, run once per uncovered vertex, so the repair adds $O(k(V+E))$ per layer, with $k$ usually 0 or 1. The gain is worth it: on Steane, plain HK peeling needs 8 layers against a lower bound of 6, and this repair recovers the optimal 6. Across 2000 random sparse Tanner graphs, plain peeling exceeded $\Delta$ in 13.4% of cases while the repaired version never did. Its weakness is that it remains a heuristic with no proof, since it only guarantees coverage in the current layer and the residual graph has a fresh max-degree set once that layer is peeled.

    * **Padding to a $\Delta$-regular graph**, which makes every matching perfect. By creating virtual edges and nodes to our graph to ensure a $\Delta$-regular pattern, this guratees that the algorithm would return $\Delta$ layers by peeling exactly $\Delta$ edges with one matching. This means that after we have constructed our layer matching we can remove the virtual edges and vertex and obtain a valid edge coliring solution. While this is guranteed to succeed mathematically, needs no extra validation but has an added time complexity. To build the padded graph, we scale to O(n $\Delta$), where n is the maximum number of vertices from one side of the bipartite graph. This means that if E for the padded graph is much larger than the actual E, the algorithm would be slower. Therefore, padding costs us a factor of $n\Delta / E$, which is itself a measure of how uneven the graph is: it equals 1 when the graph is already $\Delta$-regular and balanced, and grows as a single vertex starts to dominate. This is why the method suits the problem at hand. CSS codes are LDPC by construction, with a fixed stabilizer weight and a fixed qubit degree, so the ratio sits at or near 1 across the whole family. My toric graphs are already 4-regular, so padding adds zero edges and the guarantee comes for free; measured, it also runs about 2.5x faster than the repair route because it skips the repair entirely. Steane is small and lopsided (qubit 6 has degree 6, qubit 0 has degree 2) so it pays 1.75x, which still amounts to under a tenth of a millisecond.

2. **Euler Splitting:** halving the degree along closed walks, $O(E\log\Delta)$ on optimal cases but $O(E\Delta)$ for worse case scenarios.

3. **Cole–Ost–Schirra:** The most efficient solution for time complexity given by $O(E\log\Delta)$. Despite being the optimal solution for edge coloring, I chose to not implement this algorithm because the improvement is small ($\Delta$ is 4 on a toric and 6 on Steane). The algorithm would have removed the odd-degree penalty from the Euler splitting, which in this case is small when considering $\log\Delta$ and $\Delta$.

## Ordering Constraint
The ordering constraint requires every X/Z check pair to share an even number of qubits where the X check acts first.

### Ordering Fixes

### Multigraph & Bin Packing

## CSS Test Data
A Calderbank–Shor–Steane (CSS) code are graph networks of real qubits and ancilla qubits (checks) used to encode logical information. They use stabilizers to correct errors in magnitude (X stablizers), phase (Z) or both (Y).

## Results

## Futher Improvements and Other Considerations


def check_ordering_constraint(dp_layers):
    xs, zs = set(), set()
    for checks in dp_layers.values():
        for v in checks:
            if v[1] == "X":
                xs.add(v)
            elif v[1] == "Z":
                zs.add(v)
    broken = []
    for x in xs:
        for z in zs:
            I = [d for d, ch in dp_layers.items() if x in ch and z in ch]
            S = [d for d in I if dp_layers[d][x] < dp_layers[d][z]]
            if len(S) % 2 == 1:
                broken.append((x, z, I, S))
    return broken

def fix_ordering_constraint(
    dp_layers: dict,
    broken: list
):
    new_t = 1 + max(t for checks in dp_layers.values() for t in checks.values())
    used_d, used_check = set(), set()
    for x, z, I, S in broken:
        d = I[0]
        check = x if dp_layers[d][x] < dp_layers[d][z] else z
        if d in used_d or check in used_check:
            new_t += 1
            used_d, used_check = set(), set()
        dp_layers[d][check] = new_t
        used_d.add(d)
        used_check.add(check)
    return dp_layers


def layers_from_dp(dp_layers):
    if not dp_layers:
        return []
    layers = [[] for _ in range(1 + max(t for checks in dp_layers.values() for t in checks.values()))]
    for d, checks in dp_layers.items():
        for v, t in checks.items():
            layers[t].append((d, v))
    return layers

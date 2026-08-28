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
    for x, z, I, _S in broken:
        d = min(I, key=lambda q: distance_between_checks(dp_layers, q, x, z))
        early, late = (x, z) if dp_layers[d][x] < dp_layers[d][z] else (z, x)
        t = dp_layers[d][late]
        for checks in dp_layers.values():
            for v in checks:
                if checks[v] > t:
                    checks[v] += 1
        dp_layers[d][early] = t + 1
    return dp_layers


def distance_between_checks(dp_layers, d, x, z):
    order = sorted(dp_layers[d], key=dp_layers[d].get)
    return abs(order.index(x) - order.index(z)) - 1


def layers_from_dp(dp_layers):
    if not dp_layers:
        return []
    layers = [[] for _ in range(1 + max(t for checks in dp_layers.values() for t in checks.values()))]
    for d, checks in dp_layers.items():
        for v, t in checks.items():
            layers[t].append((d, v))
    return layers

def check_no_layer_contains_two_incident_edges(dp_layers):
    layers = layers_from_dp(dp_layers)
    for layer in layers:
        seen_x = set()
        seen_z = set()
        seen_d = set()
        for d, v in layer:
            if v[1] == "X":
                if v[0] in seen_x:
                    return False
                seen_x.add(v[0])
            elif v[1] == "Z":
                if v[0] in seen_z:
                    return False
                seen_z.add(v[0])
            else:
                if v[0] in seen_d:
                    return False
                seen_d.add(v[0])
    return True
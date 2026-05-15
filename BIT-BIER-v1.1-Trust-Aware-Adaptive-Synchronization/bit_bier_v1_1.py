import numpy as np
import random

# =========================================================
# BIT-BIER v1.1 — BOUNDED ADAPTIVE TRUST REWIRING
# =========================================================

def wrap_phase(phi):
    return phi % (2 * np.pi)

def phase_diff(target, current):
    return (target - current + np.pi) % (2 * np.pi) - np.pi

def circular_mean(phases):
    if len(phases) == 0:
        return 0.0
    return np.angle(np.mean(np.exp(1j * np.array(phases)))) % (2 * np.pi)

def weighted_circular_mean(phases, weights):
    if len(phases) == 0:
        return 0.0

    phases = np.array(phases)
    weights = np.array(weights)

    if np.sum(weights) <= 1e-9:
        return circular_mean(phases)

    z = np.sum(weights * np.exp(1j * phases)) / np.sum(weights)
    return np.angle(z) % (2 * np.pi)


class BITNode:
    def __init__(self, node_id):
        self.node_id = node_id

        self.phi = np.random.uniform(0, 2 * np.pi)
        self.velocity = 0.0
        self.drift = np.random.uniform(-0.01, 0.01)

        self.learning_rate = 0.30
        self.neighbor_coupling = 0.20
        self.damping = 0.84
        self.velocity_limit = 0.36

        self.memory_chi = 0.5

        self.failed = False
        self.malicious = False

        self.trust = 1.0
        self.state_suspicion = 0.0
        self.echo_suspicion = 0.0
        self.quarantined = False
        self.echo_integrity = 1.0

        self.phase_history = [self.phi]

    def apply_shock(self, strength=2.3):
        if self.failed:
            return
        shock = np.random.normal(0, strength)
        self.phi = wrap_phase(self.phi + shock)
        self.velocity *= 0.25

    def fail(self):
        self.failed = True
        self.velocity = 0.0
        self.trust = 0.0
        self.echo_integrity = 0.0
        self.quarantined = True

    def make_malicious(self):
        if not self.failed:
            self.malicious = True

    def observed_phi(self):
        if self.failed:
            return None

        if self.malicious:
            return wrap_phase(self.phi + np.pi + np.random.normal(0, 0.45))

        return self.phi

    def update_trust(self, master_phi):
        if self.failed:
            self.trust = 0.0
            self.echo_integrity = 0.0
            self.quarantined = True
            return

        d_state = abs(phase_diff(master_phi, self.phi))
        state_coherence = max(0.0, 1.0 - d_state / np.pi)

        if state_coherence < 0.55:
            self.state_suspicion += 0.06
        elif state_coherence < 0.75:
            self.state_suspicion += 0.025
        else:
            self.state_suspicion -= 0.035

        self.state_suspicion = float(np.clip(self.state_suspicion, 0.0, 1.0))

        obs = self.observed_phi()
        if obs is None:
            echo_error = np.pi
        else:
            echo_error = abs(phase_diff(obs, self.phi))

        self.echo_integrity = max(0.0, 1.0 - echo_error / np.pi)

        if self.echo_integrity < 0.45:
            self.echo_suspicion += 0.18
        elif self.echo_integrity < 0.70:
            self.echo_suspicion += 0.08
        else:
            self.echo_suspicion -= 0.06

        self.echo_suspicion = float(np.clip(self.echo_suspicion, 0.0, 1.0))

        combined_suspicion = (
            0.35 * self.state_suspicion +
            0.65 * self.echo_suspicion
        )

        self.trust = float(np.clip(1.0 - combined_suspicion, 0.02, 1.0))

        self.quarantined = (
            self.trust < 0.45 or
            self.echo_suspicion > 0.65
        )

    def step(self, master_phi, neighbor_phis, neighbor_weights, recovery_mode=False):
        if self.failed:
            return 0.0

        local_phi = weighted_circular_mean(neighbor_phis, neighbor_weights) if neighbor_phis else self.phi

        d_master = phase_diff(master_phi, self.phi)
        d_local = phase_diff(local_phi, self.phi)

        lr = self.learning_rate
        if recovery_mode:
            lr *= 2.0

        if self.quarantined:
            lr *= 1.45
            local_weight = 0.03
        else:
            local_weight = self.neighbor_coupling

        lr = min(lr, 0.78)

        pull_force = lr * d_master + local_weight * d_local

        self.velocity += pull_force
        self.velocity *= self.damping
        self.velocity = np.clip(self.velocity, -self.velocity_limit, self.velocity_limit)

        drift_comp = -0.75 * self.drift

        self.phi = wrap_phase(self.phi + self.velocity + self.drift + drift_comp)

        final_diff = phase_diff(master_phi, self.phi)
        coherence = max(0.0, 1.0 - abs(final_diff) / np.pi)

        coherence = 0.84 * coherence + 0.16 * self.memory_chi
        self.memory_chi = coherence

        self.phase_history.append(self.phi)

        return coherence


def build_topology(n_nodes, mode="mesh", mesh_degree=5):
    graph = {i: set() for i in range(n_nodes)}

    if mode == "ring":
        for i in range(n_nodes):
            graph[i].add((i - 1) % n_nodes)
            graph[i].add((i + 1) % n_nodes)

    elif mode == "mesh":
        for i in range(n_nodes):
            while len(graph[i]) < mesh_degree:
                j = random.randint(0, n_nodes - 1)
                if j != i:
                    graph[i].add(j)
                    graph[j].add(i)

    elif mode == "hierarchical":
        clusters = np.array_split(np.arange(n_nodes), 4)
        leaders = []

        for cluster in clusters:
            leader = int(cluster[0])
            leaders.append(leader)

            for node in cluster:
                node = int(node)
                if node != leader:
                    graph[leader].add(node)
                    graph[node].add(leader)

        for i in range(len(leaders)):
            a = leaders[i]
            b = leaders[(i + 1) % len(leaders)]
            graph[a].add(b)
            graph[b].add(a)

        for _ in range(n_nodes // 3):
            a = random.randint(0, n_nodes - 1)
            b = random.randint(0, n_nodes - 1)
            if a != b:
                graph[a].add(b)
                graph[b].add(a)

    else:
        raise ValueError("mode phải là: ring, mesh, hierarchical")

    return graph


def apply_partition(graph, n_nodes, partition_ratio=0.35):
    new_graph = {i: set(v) for i, v in graph.items()}

    edges = []
    for i in range(n_nodes):
        for j in new_graph[i]:
            if i < j:
                edges.append((i, j))

    cut_count = int(len(edges) * partition_ratio)
    cut_edges = random.sample(edges, min(cut_count, len(edges)))

    for a, b in cut_edges:
        new_graph[a].discard(b)
        new_graph[b].discard(a)

    return new_graph, cut_count


def graph_edge_count(graph):
    return sum(len(v) for v in graph.values()) // 2

def node_degree(graph, node_id):
    return len(graph[node_id])

def alive_good_nodes(nodes, trust_threshold=0.75):
    return [
        i for i, n in enumerate(nodes)
        if (not n.failed)
        and (not n.quarantined)
        and n.trust >= trust_threshold
        and n.echo_integrity >= 0.85
    ]

def max_edges_for_alive(alive_count, target_avg_degree=4.0):
    return int((alive_count * target_avg_degree) / 2)


def bounded_trust_rewire(
    graph,
    nodes,
    max_new_edges_per_step=5,
    min_degree=2,
    target_avg_degree=4.0,
    trust_threshold=0.55,
    add_trust_threshold=0.75
):
    n_nodes = len(nodes)
    new_graph = {i: set(v) for i, v in graph.items()}

    removed_edges = 0
    added_edges = 0

    for i in range(n_nodes):
        for j in list(new_graph[i]):
            if i > j:
                continue

            ni = nodes[i]
            nj = nodes[j]

            bad_i = ni.failed or ni.quarantined or ni.trust < trust_threshold or ni.echo_integrity < 0.55
            bad_j = nj.failed or nj.quarantined or nj.trust < trust_threshold or nj.echo_integrity < 0.55

            if bad_i or bad_j:
                if j in new_graph[i]:
                    new_graph[i].discard(j)
                    new_graph[j].discard(i)
                    removed_edges += 1

    alive_count = sum(1 for n in nodes if not n.failed)
    edge_limit = max_edges_for_alive(alive_count, target_avg_degree=target_avg_degree)
    current_edges = graph_edge_count(new_graph)

    if current_edges >= edge_limit:
        return new_graph, removed_edges, added_edges, edge_limit

    healthy = alive_good_nodes(nodes, trust_threshold=add_trust_threshold)

    if len(healthy) < 2:
        return new_graph, removed_edges, added_edges, edge_limit

    low_degree = [
        i for i in healthy
        if node_degree(new_graph, i) < min_degree
    ]

    candidate_pool = low_degree if low_degree else healthy

    attempts = 0

    while (
        added_edges < max_new_edges_per_step
        and graph_edge_count(new_graph) < edge_limit
        and attempts < 300
    ):
        attempts += 1

        a = random.choice(candidate_pool)

        possible = [
            b for b in healthy
            if b != a
            and b not in new_graph[a]
            and node_degree(new_graph, b) < max(3, int(target_avg_degree * 1.5))
        ]

        if not possible:
            continue

        b = random.choice(possible)

        new_graph[a].add(b)
        new_graph[b].add(a)
        added_edges += 1

    return new_graph, removed_edges, added_edges, edge_limit


def run_simulation(
    topology_mode="mesh",
    n_nodes=60,
    steps=320,
    master_speed=0.20,

    shock_steps=(80, 170),
    shock_strength=2.3,

    failure_step=120,
    failure_ratio=0.30,

    malicious_step=150,
    malicious_ratio=0.20,

    partition_step=200,
    partition_ratio=0.35,

    rewiring_start_step=155,
    rewiring_interval=5,

    recovery_threshold=0.90,
    latency_max_steps=10,

    target_avg_degree=4.0,
    seed=42
):
    np.random.seed(seed)
    random.seed(seed)

    nodes = [BITNode(i) for i in range(n_nodes)]
    graph = build_topology(n_nodes, topology_mode)

    master_phi = 0.0
    recovery_mode = False
    recovered_steps = []

    total_removed_edges = 0
    total_added_edges = 0
    latest_edge_limit = None

    system_log = []

    print("=" * 165)
    print(f"BIT-BIER v1.1 BOUNDED TRUST REWIRING | Topology: {topology_mode}")
    print("=" * 165)
    print(
        f"{'Step':<6} | {'Global C':<10} | {'Frag':<10} | {'Var':<10} | "
        f"{'Trust':<10} | {'EchoInt':<10} | {'QNodes':<7} | {'Alive':<7} | "
        f"{'Edges':<7} | {'AvgDeg':<7} | {'EdgeEff':<10} | {'State'}"
    )
    print("-" * 165)

    for step in range(steps):
        master_phi = wrap_phase(master_phi + master_speed)

        if step in shock_steps:
            for node in nodes:
                node.apply_shock(shock_strength)
            recovery_mode = True
            print(f"{step:<6} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<7} | {'---':<7} | {'---':<7} | {'---':<7} | {'---':<10} | SHOCK EVENT")

        if step == failure_step:
            fail_count = int(n_nodes * failure_ratio)
            alive_ids = [i for i, n in enumerate(nodes) if not n.failed]
            failed_ids = random.sample(alive_ids, min(fail_count, len(alive_ids)))

            for idx in failed_ids:
                nodes[idx].fail()

            recovery_mode = True
            print(f"{step:<6} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<7} | {'---':<7} | {'---':<7} | {'---':<7} | {'---':<10} | NODE FAILURE: {len(failed_ids)} nodes")

        if step == malicious_step:
            alive_ids = [i for i, n in enumerate(nodes) if not n.failed]
            bad_count = int(n_nodes * malicious_ratio)
            bad_ids = random.sample(alive_ids, min(bad_count, len(alive_ids)))

            for idx in bad_ids:
                nodes[idx].make_malicious()

            recovery_mode = True
            print(f"{step:<6} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<7} | {'---':<7} | {'---':<7} | {'---':<7} | {'---':<10} | BAD ECHO: {len(bad_ids)} nodes")

        if step == partition_step:
            graph, cut_count = apply_partition(graph, n_nodes, partition_ratio)
            recovery_mode = True
            print(f"{step:<6} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<10} | {'---':<7} | {'---':<7} | {'---':<7} | {'---':<7} | {'---':<10} | NETWORK PARTITION: cut {cut_count} edges")

        for node in nodes:
            node.update_trust(master_phi)

        if step >= rewiring_start_step and step % rewiring_interval == 0:
            graph, removed, added, edge_limit = bounded_trust_rewire(
                graph,
                nodes,
                max_new_edges_per_step=5,
                min_degree=2,
                target_avg_degree=target_avg_degree,
                trust_threshold=0.55,
                add_trust_threshold=0.75
            )

            latest_edge_limit = edge_limit
            total_removed_edges += removed
            total_added_edges += added

            if removed > 0 or added > 0:
                recovery_mode = True

        coherences = []

        for i, node in enumerate(nodes):
            neighbor_phis = []
            neighbor_weights = []

            for nb in graph[i]:
                nb_node = nodes[nb]

                obs = nb_node.observed_phi()
                if obs is None:
                    continue

                delay = random.randint(0, latency_max_steps)
                if len(nb_node.phase_history) > delay:
                    obs = nb_node.phase_history[-1 - delay]

                weight = nb_node.trust * nb_node.echo_integrity

                if nb_node.quarantined:
                    weight *= 0.03

                weight = max(0.001, weight)

                neighbor_phis.append(obs)
                neighbor_weights.append(weight)

            chi = node.step(master_phi, neighbor_phis, neighbor_weights, recovery_mode)
            coherences.append(chi)

        alive_coherences = [
            c for c, n in zip(coherences, nodes)
            if not n.failed
        ]

        alive_nodes = [n for n in nodes if not n.failed]
        alive_count = len(alive_coherences)

        global_c = float(np.mean(alive_coherences)) if alive_coherences else 0.0
        frag = 1.0 - global_c
        var = float(np.var(alive_coherences)) if alive_coherences else 0.0

        avg_trust = float(np.mean([n.trust for n in alive_nodes])) if alive_nodes else 0.0
        avg_echo = float(np.mean([n.echo_integrity for n in alive_nodes])) if alive_nodes else 0.0
        qnodes = sum(1 for n in alive_nodes if n.quarantined)

        edges = graph_edge_count(graph)
        avg_degree = (2 * edges / alive_count) if alive_count > 0 else 0.0
        edge_eff = global_c / edges if edges > 0 else 0.0

        if global_c > 0.94:
            state = "HIGH_RESONANCE"
        elif global_c > 0.90:
            state = "RESONANCE"
        elif recovery_mode:
            state = "RECOVERING"
        else:
            state = "ADAPTING"

        if recovery_mode and global_c >= recovery_threshold:
            recovered_steps.append(step)
            recovery_mode = False
            state = "RECOVERED"

        system_log.append({
            "step": step,
            "global_coherence": global_c,
            "fragmentation": frag,
            "variance": var,
            "avg_trust": avg_trust,
            "avg_echo_integrity": avg_echo,
            "quarantined_nodes": qnodes,
            "alive": alive_count,
            "edges": edges,
            "avg_degree": avg_degree,
            "edge_efficiency": edge_eff,
            "state": state
        })

        interesting_steps = set()
        for s in shock_steps:
            interesting_steps.update([s, s + 1, s + 2, s + 3])

        interesting_steps.update([
            failure_step, failure_step + 1, failure_step + 2,
            malicious_step, malicious_step + 1, malicious_step + 2,
            partition_step, partition_step + 1, partition_step + 2,
            rewiring_start_step, rewiring_start_step + 1, rewiring_start_step + 2
        ])

        if step % 10 == 0 or step in interesting_steps or state == "RECOVERED":
            print(
                f"{step:<6} | "
                f"{global_c:<10.4f} | "
                f"{frag:<10.4f} | "
                f"{var:<10.5f} | "
                f"{avg_trust:<10.4f} | "
                f"{avg_echo:<10.4f} | "
                f"{qnodes:<7} | "
                f"{alive_count:<7} | "
                f"{edges:<7} | "
                f"{avg_degree:<7.2f} | "
                f"{edge_eff:<10.6f} | "
                f"{state}"
            )

    print("-" * 165)
    print("FINAL REPORT")
    print("-" * 165)

    final = system_log[-1]

    print(f"Final Global Coherence : {final['global_coherence']:.4f}")
    print(f"Final Fragmentation    : {final['fragmentation']:.4f}")
    print(f"Final Variance         : {final['variance']:.5f}")
    print(f"Final Avg Trust        : {final['avg_trust']:.4f}")
    print(f"Final Echo Integrity   : {final['avg_echo_integrity']:.4f}")
    print(f"Final Quarantine Nodes : {final['quarantined_nodes']}")
    print(f"Final Edges            : {final['edges']}")
    print(f"Final Avg Degree       : {final['avg_degree']:.2f}")
    print(f"Final Edge Efficiency  : {final['edge_efficiency']:.6f}")

    if latest_edge_limit is not None:
        print(f"Edge Limit             : {latest_edge_limit}")

    print(f"Total Removed Edges    : {total_removed_edges}")
    print(f"Total Added Edges      : {total_added_edges}")

    failed_total = sum(1 for n in nodes if n.failed)
    bad_total = sum(1 for n in nodes if n.malicious)

    print(f"Failed Nodes           : {failed_total}/{n_nodes}")
    print(f"Bad Echo Nodes         : {bad_total}/{n_nodes}")
    print(f"Alive Nodes            : {final['alive']}/{n_nodes}")

    if recovered_steps:
        print(f"Recovery Events        : {recovered_steps}")
    else:
        print("Recovery Events        : None")

    malicious_alive = [n for n in nodes if n.malicious and not n.failed]
    if malicious_alive:
        avg_bad_trust = np.mean([n.trust for n in malicious_alive])
        avg_bad_echo = np.mean([n.echo_integrity for n in malicious_alive])
        bad_quarantined = sum(1 for n in malicious_alive if n.quarantined)

        print(f"Bad Echo Avg Trust     : {avg_bad_trust:.4f}")
        print(f"Bad Echo Integrity     : {avg_bad_echo:.4f}")
        print(f"Bad Echo Quarantined   : {bad_quarantined}/{len(malicious_alive)}")

    print("\nFinal Node Snapshot:")
    for n in nodes[:8]:
        print({
            "node": n.node_id,
            "failed": n.failed,
            "malicious": n.malicious,
            "quarantined": n.quarantined,
            "trust": round(n.trust, 3),
            "echo_integrity": round(n.echo_integrity, 3),
            "phi": round(n.phi, 3),
            "velocity": round(n.velocity, 3),
            "chi": round(n.memory_chi, 3)
        })

    return system_log, nodes, graph


if __name__ == "__main__":
    for topo in ["ring", "mesh", "hierarchical"]:
        run_simulation(
            topology_mode=topo,
            n_nodes=60,
            steps=320,
            master_speed=0.20,

            shock_steps=(80, 170),
            shock_strength=2.3,

            failure_step=120,
            failure_ratio=0.30,

            malicious_step=150,
            malicious_ratio=0.20,

            partition_step=200,
            partition_ratio=0.35,

            rewiring_start_step=155,
            rewiring_interval=5,

            recovery_threshold=0.90,
            latency_max_steps=10,

            target_avg_degree=4.0,
            seed=42
        )

        print("\n\n")

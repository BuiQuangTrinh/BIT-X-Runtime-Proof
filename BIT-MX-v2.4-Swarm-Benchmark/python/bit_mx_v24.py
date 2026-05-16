import numpy as np
import matplotlib.pyplot as plt
import csv
import os

# ============================================================
# BIT-MX Simulation Engine v2.4
# Formation-Restoring Statistical Benchmark Prototype
# Status: illustrative numerical benchmark, not hardware validation
# ============================================================

OUTPUT_DIR = "bit_mx_v24_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------
# CONFIG
# ----------------------------
NUM_DRONES = 3
D_TARGET = 5.0
D_MIN = 1.5
D_REPULSE = 2.2

E_CRIT = 6.0
K_MIN = 0.4

TIMESTEPS = 120
DT = 0.1
NUM_SEEDS = 20

M = 1.2
C_DRAG = 0.25
F_MAX = 22.0

K_CENTER = 2.5
K_REPULSE = 5.0
K_SPRING = 8.5
C_DAMPER = 1.2
K_SYNC = 5.0

# ----------------------------
# INIT
# ----------------------------
def init_swarm():
    positions = np.array([
        [0.0, 0.0],
        [5.0, 0.0],
        [2.5, 4.33]
    ], dtype=float)

    velocities = np.array([
        [2.5, 0.0],
        [2.5, 0.0],
        [2.5, 0.0]
    ], dtype=float)

    return positions, velocities


def generate_wind(seed):
    rng = np.random.default_rng(seed)
    wind = np.zeros((TIMESTEPS, 2), dtype=float)

    for t in range(TIMESTEPS):
        if 25 <= t <= 75:
            wind[t] = np.array([-7.5, 4.5]) + rng.normal(0, 1.8, size=2)

    return wind


# ----------------------------
# METRICS
# ----------------------------
def pair_distances(positions):
    return [
        np.linalg.norm(positions[0] - positions[1]),
        np.linalg.norm(positions[1] - positions[2]),
        np.linalg.norm(positions[2] - positions[0])
    ]


def formation_energy(distances):
    return sum(abs(d - D_TARGET) for d in distances)


def coherence_metric(velocities):
    headings = np.array([np.arctan2(v[1], v[0]) for v in velocities])
    theta_group = np.mean(headings)

    k_heading = np.mean([np.cos(h - theta_group) for h in headings])

    speeds = np.linalg.norm(velocities, axis=1)
    k_velocity = 1.0 - np.std(speeds) / (np.mean(speeds) + 1e-6)

    k_total = 0.6 * k_heading + 0.4 * k_velocity
    return float(k_total), float(k_heading), float(k_velocity)


def inside_corridor(E, K, distances):
    return E < E_CRIT and K > K_MIN and min(distances) > D_MIN


# ----------------------------
# SINGLE SIMULATION
# ----------------------------
def run_single_seed(seed=0, use_bit_mx=True):
    positions, velocities = init_swarm()
    wind_fields = generate_wind(seed)

    history = []
    min_pair_dist = float("inf")
    max_E = 0.0
    ticks_outside = 0
    collision_count = 0

    for t in range(TIMESTEPS):
        distances = pair_distances(positions)
        min_d = min(distances)
        min_pair_dist = min(min_pair_dist, min_d)

        if min_d < D_MIN:
            collision_count += 1

        E = formation_energy(distances)
        max_E = max(max_E, E)

        K_total, K_heading, K_velocity = coherence_metric(velocities)
        in_sc = inside_corridor(E, K_total, distances)

        if not in_sc:
            ticks_outside += 1

        history.append({
            "timestep": t,
            "time_s": t * DT,
            "use_bit_mx": int(use_bit_mx),
            "x1": positions[0, 0],
            "y1": positions[0, 1],
            "x2": positions[1, 0],
            "y2": positions[1, 1],
            "x3": positions[2, 0],
            "y3": positions[2, 1],
            "d12": distances[0],
            "d23": distances[1],
            "d31": distances[2],
            "min_pair_distance": min_d,
            "E": E,
            "K_total": K_total,
            "K_heading": K_heading,
            "K_velocity": K_velocity,
            "inside_corridor": int(in_sc),
            "collision": int(min_d < D_MIN)
        })

        # ----------------------------
        # CONTROL
        # ----------------------------
        F_control = np.zeros((NUM_DRONES, 2), dtype=float)
        center = np.mean(positions, axis=0)

        # Naive center cohesion
        for i in range(NUM_DRONES):
            vec = center - positions[i]
            norm = np.linalg.norm(vec) + 1e-6
            F_control[i] += K_CENTER * vec / norm

        if use_bit_mx:
            pairs = [(0, 1), (1, 2), (2, 0)]

            for i, j in pairs:
                diff = positions[i] - positions[j]
                d = np.linalg.norm(diff) + 1e-6
                u = diff / d

                # Layer 1: Boundary Guard
                if d < D_REPULSE:
                    F_repulse = (K_REPULSE / (d ** 2)) * u
                    F_control[i] += F_repulse
                    F_control[j] -= F_repulse

                # Layer 3: Shape Restoration spring-damper
                error = d - D_TARGET
                v_rel = velocities[i] - velocities[j]

                F_spring = -K_SPRING * error * u
                F_damping = -C_DAMPER * np.dot(v_rel, u) * u
                F_restore = F_spring + F_damping

                F_control[i] += 0.5 * F_restore
                F_control[j] -= 0.5 * F_restore

            # Layer 2: Elastic Sync
            if E > E_CRIT or K_total < K_MIN:
                v_mean = np.mean(velocities, axis=0)
                for i in range(NUM_DRONES):
                    F_control[i] += K_SYNC * (v_mean - velocities[i])

        # ----------------------------
        # PHYSICS INTEGRATION
        # ----------------------------
        F_wind = wind_fields[t]

        for i in range(NUM_DRONES):
            F_drag = -C_DRAG * velocities[i]
            F_total = F_control[i] + F_wind + F_drag

            mag = np.linalg.norm(F_total)
            if mag > F_MAX:
                F_total = F_total / mag * F_MAX

            acceleration = F_total / M
            velocities[i] += acceleration * DT
            positions[i] += velocities[i] * DT

    summary = {
        "seed": seed,
        "use_bit_mx": int(use_bit_mx),
        "min_pair_distance": min_pair_dist,
        "max_E": max_E,
        "time_outside_corridor_s": ticks_outside * DT,
        "collision_count": collision_count
    }

    return history, summary


# ----------------------------
# EXPORT
# ----------------------------
def export_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def compute_stats(summaries):
    return {
        "mean_min_pair_distance": np.mean([s["min_pair_distance"] for s in summaries]),
        "mean_max_E": np.mean([s["max_E"] for s in summaries]),
        "mean_time_outside_corridor_s": np.mean([s["time_outside_corridor_s"] for s in summaries]),
        "total_collision_count": np.sum([s["collision_count"] for s in summaries])
    }


# ----------------------------
# PLOTS
# ----------------------------
def plot_demo(history_naive, history_bit):
    t = [r["time_s"] for r in history_bit]

    E_naive = [r["E"] for r in history_naive]
    E_bit = [r["E"] for r in history_bit]

    K_naive = [r["K_total"] for r in history_naive]
    K_bit = [r["K_total"] for r in history_bit]

    plt.figure(figsize=(14, 5))

    plt.subplot(1, 2, 1)
    plt.plot(t, E_naive, "--", label="Naive Controller - E")
    plt.plot(t, E_bit, linewidth=2, label="BIT-MX v2.4 - E")
    plt.axhline(E_CRIT, linestyle=":", label="E Critical Boundary")
    plt.title("Formation Deviation Energy")
    plt.xlabel("Time (s)")
    plt.ylabel("E")
    plt.grid(True)
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(t, K_naive, "--", label="Naive Controller - K")
    plt.plot(t, K_bit, linewidth=2, label="BIT-MX v2.4 - K")
    plt.axhline(K_MIN, linestyle=":", label="K Minimum Boundary")
    plt.title("Multi-Faceted Coherence")
    plt.xlabel("Time (s)")
    plt.ylabel("K")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, "bit_mx_v24_metrics.png")
    plt.savefig(out, dpi=180)
    print("Saved:", out)
    plt.show()


def plot_trajectories(history_naive, history_bit):
    plt.figure(figsize=(14, 5))

    plt.subplot(1, 2, 1)
    for i in range(1, 4):
        xs = [r[f"x{i}"] for r in history_naive]
        ys = [r[f"y{i}"] for r in history_naive]
        plt.plot(xs, ys, label=f"Drone {i}")
        plt.scatter(xs[-1], ys[-1])
    plt.title("Naive Controller Trajectories")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True)
    plt.legend()

    plt.subplot(1, 2, 2)
    for i in range(1, 4):
        xs = [r[f"x{i}"] for r in history_bit]
        ys = [r[f"y{i}"] for r in history_bit]
        plt.plot(xs, ys, label=f"Drone {i}")
        plt.scatter(xs[-1], ys[-1])
    plt.title("BIT-MX v2.4 Trajectories")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, "bit_mx_v24_trajectories.png")
    plt.savefig(out, dpi=180)
    print("Saved:", out)
    plt.show()


# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    all_summaries_naive = []
    all_summaries_bit = []

    demo_history_naive = None
    demo_history_bit = None

    for seed in range(NUM_SEEDS):
        h_naive, s_naive = run_single_seed(seed, use_bit_mx=False)
        h_bit, s_bit = run_single_seed(seed, use_bit_mx=True)

        all_summaries_naive.append(s_naive)
        all_summaries_bit.append(s_bit)

        if seed == 0:
            demo_history_naive = h_naive
            demo_history_bit = h_bit

    stats_naive = compute_stats(all_summaries_naive)
    stats_bit = compute_stats(all_summaries_bit)

    export_csv(os.path.join(OUTPUT_DIR, "bit_mx_v24_seed0_naive_log.csv"), demo_history_naive)
    export_csv(os.path.join(OUTPUT_DIR, "bit_mx_v24_seed0_supervisor_log.csv"), demo_history_bit)
    export_csv(os.path.join(OUTPUT_DIR, "bit_mx_v24_summary_naive.csv"), all_summaries_naive)
    export_csv(os.path.join(OUTPUT_DIR, "bit_mx_v24_summary_supervisor.csv"), all_summaries_bit)

    print("\n" + "=" * 80)
    print("BIT-MX v2.4 MULTI-SEED STATISTICAL BENCHMARK REPORT")
    print("=" * 80)
    print(f"Seeds: {NUM_SEEDS}")
    print("\nNaive Controller:")
    print(f"  Mean minimum pair distance: {stats_naive['mean_min_pair_distance']:.3f} m")
    print(f"  Mean maximum E:             {stats_naive['mean_max_E']:.3f}")
    print(f"  Mean time outside corridor: {stats_naive['mean_time_outside_corridor_s']:.3f} s")
    print(f"  Total collision count:      {stats_naive['total_collision_count']}")

    print("\nBIT-MX v2.4 Supervisor:")
    print(f"  Mean minimum pair distance: {stats_bit['mean_min_pair_distance']:.3f} m")
    print(f"  Mean maximum E:             {stats_bit['mean_max_E']:.3f}")
    print(f"  Mean time outside corridor: {stats_bit['mean_time_outside_corridor_s']:.3f} s")
    print(f"  Total collision count:      {stats_bit['total_collision_count']}")

    print("\nStatus: illustrative engineering benchmark, not hardware validation.")
    print("Core statement: BIT-MX protects formation survival topology through Boundary Guard, Elastic Sync, and Shape Restoration.")
    print("=" * 80 + "\n")

    plot_demo(demo_history_naive, demo_history_bit)
    plot_trajectories(demo_history_naive, demo_history_bit)

# bit_x17_3_runtime.py
# BIT-X17.3 — Boundary-Constrained Swarm Corridor Runtime
# Run directly:
#   python bit_x17_3_runtime.py

import os
import csv
import math
import numpy as np


class BitX173Runtime:
    def __init__(
        self,
        num_agents=3,
        d_target=5.0,
        dt=0.1,
        steps=160,
        mass=1.2,
        drag=0.25,
        f_max=25.0,
        k_lattice=12.5,
        c_damping=1.8,
        e_crit=6.0,
        k_min=0.4,
        collision_distance=1.5,
        sensor_noise_std=0.02,
        wind_noise_std=0.15,
    ):
        self.num_agents = num_agents
        self.d_target = d_target
        self.dt = dt
        self.steps = steps
        self.mass = mass
        self.drag = drag
        self.f_max = f_max
        self.k_lattice = k_lattice
        self.c_damping = c_damping
        self.e_crit = e_crit
        self.k_min = k_min
        self.collision_distance = collision_distance
        self.sensor_noise_std = sensor_noise_std
        self.wind_noise_std = wind_noise_std

    def initial_state(self):
        if self.num_agents == 3:
            pos = np.array(
                [
                    [0.0, 0.0],
                    [self.d_target, 0.0],
                    [0.5 * self.d_target, 0.866 * self.d_target],
                ],
                dtype=float,
            )
        else:
            angles = np.linspace(0, 2 * np.pi, self.num_agents, endpoint=False)
            radius = self.d_target
            pos = np.column_stack(
                [radius * np.cos(angles), radius * np.sin(angles)]
            ).astype(float)

        vel = np.tile(np.array([2.5, 0.0]), (self.num_agents, 1)).astype(float)
        return pos, vel

    def pair_indices(self):
        pairs = []
        for i in range(self.num_agents):
            for j in range(i + 1, self.num_agents):
                pairs.append((i, j))
        return pairs

    def compute_metrics(self, pos, vel):
        distances = []

        for i, j in self.pair_indices():
            distances.append(np.linalg.norm(pos[i] - pos[j]))

        distances = np.array(distances, dtype=float)

        # Smooth geometric deviation energy
        E = 0.5 * np.sum((distances - self.d_target) ** 2)

        headings = np.array([math.atan2(v[1], v[0]) for v in vel])
        theta_group = np.mean(headings)
        K = np.mean(np.cos(headings - theta_group))

        min_distance = float(np.min(distances))

        kinetic_energy = 0.5 * self.mass * np.sum(np.linalg.norm(vel, axis=1) ** 2)
        potential_energy = self.k_lattice * E

        return {
            "E": float(E),
            "K": float(K),
            "min_distance": min_distance,
            "kinetic_energy": float(kinetic_energy),
            "potential_energy": float(potential_energy),
        }

    def compute_control_force(self, pos, vel, use_bit=True):
        F_control = np.zeros_like(pos)

        if not use_bit:
            # Naive baseline: weak pull toward center
            center = np.mean(pos, axis=0)

            for i in range(self.num_agents):
                direction = center - pos[i]
                norm = np.linalg.norm(direction) + 1e-9
                F_control[i] += 2.5 * direction / norm

            return F_control, False

        metrics = self.compute_metrics(pos, vel)
        triggered = (metrics["E"] > self.e_crit) or (metrics["K"] < self.k_min)

        # Event-triggered recovery:
        # If the swarm is still inside the corridor, no heavy recovery force is applied.
        if not triggered:
            return F_control, False

        for i, j in self.pair_indices():
            diff = pos[i] - pos[j]
            d_ij = np.linalg.norm(diff) + 1e-9
            u_ij = diff / d_ij

            error = d_ij - self.d_target
            v_rel = vel[i] - vel[j]

            # Boundary recovery operator:
            # F = -k * error * direction - c * projected_relative_velocity * direction
            F_lattice = (
                -self.k_lattice * error * u_ij
                -self.c_damping * np.dot(v_rel, u_ij) * u_ij
            )

            F_control[i] += 0.5 * F_lattice
            F_control[j] -= 0.5 * F_lattice

            # Emergency collision guard
            if d_ij < 2.2:
                repel = (6.0 / (d_ij ** 2)) * u_ij
                F_control[i] += repel
                F_control[j] -= repel

        # Velocity synchronization during recovery
        v_mean = np.mean(vel, axis=0)
        for i in range(self.num_agents):
            F_control[i] += 5.5 * (v_mean - vel[i])

        return F_control, True

    def run(
        self,
        seed=42,
        use_bit=True,
        wind_intensity=8.5,
        wind_start=40,
        wind_end=100,
        return_history=False,
    ):
        rng = np.random.default_rng(seed)

        pos, vel = self.initial_state()

        base_wind = np.array([-1.0, 0.7], dtype=float) * wind_intensity

        max_E = 0.0
        min_distance_seen = float("inf")
        outside_ticks = 0
        collision_ticks = 0
        trigger_ticks = 0
        total_control_effort = 0.0

        history = []

        for step in range(self.steps):
            # sensor noise creates real seed variation
            pos_measured = pos + rng.normal(0.0, self.sensor_noise_std, pos.shape)

            metrics = self.compute_metrics(pos_measured, vel)

            E = metrics["E"]
            K = metrics["K"]
            min_distance = metrics["min_distance"]

            max_E = max(max_E, E)
            min_distance_seen = min(min_distance_seen, min_distance)

            outside = (
                E > self.e_crit
                or K < self.k_min
                or min_distance < self.collision_distance
            )

            if outside:
                outside_ticks += 1

            if min_distance < self.collision_distance:
                collision_ticks += 1

            F_control, triggered = self.compute_control_force(
                pos_measured,
                vel,
                use_bit=use_bit,
            )

            if triggered:
                trigger_ticks += 1

            if wind_start <= step <= wind_end:
                wind_noise = rng.normal(0.0, self.wind_noise_std, 2)
                F_wind = base_wind + wind_noise
            else:
                F_wind = np.zeros(2)

            for i in range(self.num_agents):
                F_total = F_control[i] + F_wind - self.drag * vel[i]

                mag = np.linalg.norm(F_total)
                if mag > self.f_max:
                    F_total = (F_total / mag) * self.f_max

                total_control_effort += np.linalg.norm(F_total) * self.dt

                vel[i] += (F_total / self.mass) * self.dt
                pos[i] += vel[i] * self.dt

            if return_history:
                history.append(
                    {
                        "step": step,
                        "E": E,
                        "K": K,
                        "min_distance": min_distance,
                        "kinetic_energy": metrics["kinetic_energy"],
                        "potential_energy": metrics["potential_energy"],
                        "control_effort": total_control_effort,
                        "triggered": int(triggered),
                        "outside_corridor": int(outside),
                    }
                )

        corridor_occupancy = 100.0 * (self.steps - outside_ticks) / self.steps
        collision_rate = 100.0 * collision_ticks / self.steps
        trigger_rate = 100.0 * trigger_ticks / self.steps

        result = {
            "controller": "BIT-X17.3" if use_bit else "Naive",
            "seed": seed,
            "wind_intensity": wind_intensity,
            "max_E": max_E,
            "min_distance": min_distance_seen,
            "corridor_occupancy": corridor_occupancy,
            "collision_rate": collision_rate,
            "trigger_rate": trigger_rate,
            "control_effort": total_control_effort,
        }

        if return_history:
            return result, history

        return result


def ensure_dirs():
    os.makedirs("csv", exist_ok=True)


def save_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_single_demo():
    print("\n" + "=" * 80)
    print("BIT-X17.3 SINGLE RUNTIME TEST")
    print("=" * 80)

    engine = BitX173Runtime()

    bit_result, history = engine.run(
        seed=42,
        use_bit=True,
        wind_intensity=8.5,
        return_history=True,
    )

    naive_result = engine.run(
        seed=42,
        use_bit=False,
        wind_intensity=8.5,
        return_history=False,
    )

    print("\nBIT-X17.3 Controller Result:")
    for k, v in bit_result.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")

    print("\nNaive Controller Result:")
    for k, v in naive_result.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")

    ensure_dirs()

    history_path = "csv/bit_x17_3_runtime_history_seed42.csv"
    save_csv(
        history_path,
        history,
        [
            "step",
            "E",
            "K",
            "min_distance",
            "kinetic_energy",
            "potential_energy",
            "control_effort",
            "triggered",
            "outside_corridor",
        ],
    )

    print(f"\nRuntime history CSV saved to: {history_path}")


def run_benchmark():
    print("\n" + "=" * 80)
    print("BIT-X17.3 MULTI-SEED BENCHMARK")
    print("=" * 80)

    engine = BitX173Runtime()

    wind_intensities = [5.0, 8.5, 12.0]
    seeds = range(20)

    rows = []

    for wind in wind_intensities:
        for seed in seeds:
            rows.append(engine.run(seed=seed, use_bit=True, wind_intensity=wind))
            rows.append(engine.run(seed=seed, use_bit=False, wind_intensity=wind))

    ensure_dirs()

    benchmark_path = "csv/bit_x17_3_benchmark_results.csv"
    fieldnames = [
        "controller",
        "seed",
        "wind_intensity",
        "max_E",
        "min_distance",
        "corridor_occupancy",
        "collision_rate",
        "trigger_rate",
        "control_effort",
    ]

    save_csv(benchmark_path, rows, fieldnames)

    print(f"\nBenchmark CSV saved to: {benchmark_path}")

    print("\nSummary:")
    print("-" * 80)

    for wind in wind_intensities:
        print(f"\nWind intensity: {wind}")

        for controller in ["BIT-X17.3", "Naive"]:
            subset = [
                r for r in rows
                if r["wind_intensity"] == wind and r["controller"] == controller
            ]

            mean_max_E = np.mean([r["max_E"] for r in subset])
            mean_min_distance = np.mean([r["min_distance"] for r in subset])
            mean_corridor = np.mean([r["corridor_occupancy"] for r in subset])
            mean_collision = np.mean([r["collision_rate"] for r in subset])
            mean_trigger = np.mean([r["trigger_rate"] for r in subset])
            mean_effort = np.mean([r["control_effort"] for r in subset])

            print(
                f"  {controller:10s} | "
                f"Max_E={mean_max_E:8.3f} | "
                f"Min_D={mean_min_distance:7.3f} | "
                f"Corridor={mean_corridor:6.2f}% | "
                f"Collision={mean_collision:6.2f}% | "
                f"Trigger={mean_trigger:6.2f}% | "
                f"Effort={mean_effort:9.2f}"
            )

    print("\nStatus: Research Sandbox Benchmark")
    print("Note: This is a numerical prototype, not a formal mathematical proof.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_single_demo()
    run_benchmark()

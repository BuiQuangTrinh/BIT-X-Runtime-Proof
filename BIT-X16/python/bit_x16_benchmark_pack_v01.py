#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BIT-X16.1 Benchmark Pack v0.1
Morphological State Transition Engine

Core loop:
Perturbation -> Accumulation -> Threshold -> Transition -> Recovery

Benchmarks:
1. Diffusion sweep
2. Threshold sweep
3. Recovery sweep
4. Seed sweep

Outputs:
- bit_x16_benchmark_pack_v01.csv
- bit_x16_benchmark_pack_v01.png
"""

import csv
import numpy as np
import matplotlib.pyplot as plt


GRID_SIZE = 10
TICKS = 90
DT = 0.1

BURST_START = 20
BURST_END = 45

DEFAULT_D = 0.25
DEFAULT_THRESHOLD = 7.5
DEFAULT_RECOVERY = 0.7
DEFAULT_LAMBDA_BURST = 10
DEFAULT_LAMBDA_BASE = 2

DIFFUSION_SWEEP = [0.05, 0.15, 0.25, 0.35, 0.45]
THRESHOLD_SWEEP = [5.5, 6.5, 7.5, 8.5, 9.5]
RECOVERY_SWEEP = [0.3, 0.5, 0.7, 0.9, 1.1]
SEED_SWEEP = [101, 202, 303, 404, 505]


def run_engine(
    seed,
    diffusion_d=DEFAULT_D,
    threshold=DEFAULT_THRESHOLD,
    recovery=DEFAULT_RECOVERY,
    lambda_burst=DEFAULT_LAMBDA_BURST,
    lambda_base=DEFAULT_LAMBDA_BASE,
):
    np.random.seed(seed)

    field = np.zeros((GRID_SIZE, GRID_SIZE))
    state = np.zeros((GRID_SIZE, GRID_SIZE))

    cluster_history = []
    mass_history = []
    coherence_history = []

    for tick in range(TICKS):
        lam = lambda_burst if BURST_START <= tick <= BURST_END else lambda_base
        inputs = np.random.poisson(lam)

        for _ in range(inputs):
            x = np.random.randint(0, GRID_SIZE)
            y = np.random.randint(0, GRID_SIZE)
            field[x, y] += 2.2

        next_field = field.copy()
        state[:, :] = 0.0

        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                laplacian = 0.0
                neighbors = []

                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        laplacian += field[nx, ny] - field[x, y]
                        neighbors.append((nx, ny))

                next_field[x, y] += diffusion_d * laplacian * DT

                if next_field[x, y] > threshold:
                    state[x, y] = 1.0
                    excess = next_field[x, y] - threshold
                    next_field[x, y] = threshold

                    if neighbors:
                        share = excess / len(neighbors)
                        for nx, ny in neighbors:
                            next_field[nx, ny] += share

        field = np.maximum(0.0, next_field - recovery * DT)

        cluster_size = int(np.sum(state > 0.5))
        total_mass = float(np.sum(field))
        coherence = 1.0 - cluster_size / (GRID_SIZE * GRID_SIZE)

        cluster_history.append(cluster_size)
        mass_history.append(total_mass)
        coherence_history.append(coherence)

    peak_cluster = int(np.max(cluster_history))
    final_mass = float(mass_history[-1])
    min_coherence = float(np.min(coherence_history))

    post_burst_mass = mass_history[BURST_END]
    final_recovery_mass = mass_history[-1]
    recovery_score = max(0.0, post_burst_mass - final_recovery_mass)

    return {
        "cluster_history": cluster_history,
        "mass_history": mass_history,
        "coherence_history": coherence_history,
        "peak_cluster": peak_cluster,
        "final_mass": final_mass,
        "min_coherence": min_coherence,
        "recovery_score": recovery_score,
    }


def run_benchmark_pack():
    rows = []
    plot_series = {}

    benchmark_sets = [
        ("diffusion_sweep", "D", DIFFUSION_SWEEP),
        ("threshold_sweep", "threshold", THRESHOLD_SWEEP),
        ("recovery_sweep", "recovery", RECOVERY_SWEEP),
        ("seed_sweep", "seed", SEED_SWEEP),
    ]

    for benchmark_name, param_name, values in benchmark_sets:
        plot_series[benchmark_name] = []

        for value in values:
            if benchmark_name == "diffusion_sweep":
                result = run_engine(seed=2026, diffusion_d=value)
            elif benchmark_name == "threshold_sweep":
                result = run_engine(seed=2026, threshold=value)
            elif benchmark_name == "recovery_sweep":
                result = run_engine(seed=2026, recovery=value)
            else:
                result = run_engine(seed=value)

            rows.append({
                "benchmark": benchmark_name,
                "parameter": param_name,
                "value": value,
                "peak_cluster": result["peak_cluster"],
                "final_mass": round(result["final_mass"], 3),
                "min_coherence": round(result["min_coherence"], 3),
                "recovery_score": round(result["recovery_score"], 3),
            })

            plot_series[benchmark_name].append((value, result))

    return rows, plot_series


rows, plot_series = run_benchmark_pack()


csv_filename = "bit_x16_benchmark_pack_v01.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "benchmark",
            "parameter",
            "value",
            "peak_cluster",
            "final_mass",
            "min_coherence",
            "recovery_score",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"CSV exported: {csv_filename}")


ticks = np.arange(TICKS)
plt.figure(figsize=(16, 10))

plt.subplot(2, 2, 1)
for value, result in plot_series["diffusion_sweep"]:
    plt.plot(ticks, result["cluster_history"], label=f"D={value}")
plt.axvspan(BURST_START, BURST_END, alpha=0.08)
plt.title("Benchmark 1: Diffusion Sweep — Cluster Size")
plt.xlabel("Ticks")
plt.ylabel("Overload Cluster")
plt.legend()
plt.grid(True, alpha=0.25)

plt.subplot(2, 2, 2)
for value, result in plot_series["threshold_sweep"]:
    plt.plot(ticks, result["cluster_history"], label=f"PSI={value}")
plt.axvspan(BURST_START, BURST_END, alpha=0.08)
plt.title("Benchmark 2: Threshold Sweep — Cluster Size")
plt.xlabel("Ticks")
plt.ylabel("Overload Cluster")
plt.legend()
plt.grid(True, alpha=0.25)

plt.subplot(2, 2, 3)
for value, result in plot_series["recovery_sweep"]:
    plt.plot(ticks, result["mass_history"], label=f"GAMMA={value}")
plt.axvspan(BURST_START, BURST_END, alpha=0.08)
plt.title("Benchmark 3: Recovery Sweep — Total Mass")
plt.xlabel("Ticks")
plt.ylabel("Metric Field Mass")
plt.legend()
plt.grid(True, alpha=0.25)

plt.subplot(2, 2, 4)
for value, result in plot_series["seed_sweep"]:
    plt.plot(ticks, result["coherence_history"], label=f"seed={value}")
plt.axvspan(BURST_START, BURST_END, alpha=0.08)
plt.title("Benchmark 4: Seed Sweep — Coherence Stability")
plt.xlabel("Ticks")
plt.ylabel("Coherence")
plt.legend()
plt.grid(True, alpha=0.25)

plt.tight_layout()

plot_filename = "bit_x16_benchmark_pack_v01.png"
plt.savefig(plot_filename, dpi=150)
print(f"Plot exported: {plot_filename}")

plt.show()


print("\nBenchmark summary:")
for row in rows:
    print(row)

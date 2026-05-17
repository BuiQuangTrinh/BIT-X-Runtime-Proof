#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BIT-X16.1 — MORPHOLOGICAL STATE TRANSITION ENGINE v1.1

Core loop:
Perturbation Streams
-> Metric Field Accumulation
-> Threshold Activation
-> Emergent State Cluster
-> Recovery Dynamics

Output:
- bit_x16_runtime_v11.csv
- bit_x16_sweep_plot.png
"""

import csv
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# 1. LAB SETUP
# ============================================================

np.random.seed(161)

GRID_SIZE = 10
TICKS_PER_RUN = 80
DT = 0.1

THRESHOLD_PSI = 6.0
RECOVERY_GAMMA = 0.4

# Sweep hệ số lan truyền / khuếch tán
contagion_sweep = [0.05, 0.15, 0.25, 0.35, 0.45]

experiment_results = []
history_sweep_mass = []
history_sweep_cluster = []
history_sweep_coherence = []


def count_active_cluster(field_state):
    """Đếm số node đang ở trạng thái kích hoạt."""
    return int(np.sum(field_state > 0.5))


def run_single_experiment(d_coeff, run_idx):
    field_joule = np.zeros((GRID_SIZE, GRID_SIZE))
    field_state = np.zeros((GRID_SIZE, GRID_SIZE))

    run_cluster_sizes = []
    run_mass_evolution = []
    run_coherence = []

    for tick in range(TICKS_PER_RUN):
        # 1. Perturbation stream
        lambda_input = 14 if 20 <= tick <= 45 else 2
        inputs = np.random.poisson(lambda_input)

        for _ in range(inputs):
            x = np.random.randint(0, GRID_SIZE)
            y = np.random.randint(0, GRID_SIZE)
            field_joule[x, y] += 2.2

        # 2. Diffusion + threshold transition
        next_joule = field_joule.copy()
        field_state[:, :] = 0.0

        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                laplacian = 0.0
                neighbors = []

                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        laplacian += field_joule[nx, ny] - field_joule[x, y]
                        neighbors.append((nx, ny))

                next_joule[x, y] += d_coeff * laplacian * DT

                # Threshold activation
                if next_joule[x, y] > THRESHOLD_PSI:
                    field_state[x, y] = 1.0

                    excess = next_joule[x, y] - THRESHOLD_PSI
                    next_joule[x, y] = THRESHOLD_PSI

                    if neighbors:
                        share = excess / len(neighbors)
                        for nx, ny in neighbors:
                            next_joule[nx, ny] += share

        # 3. Recovery / cooldown
        field_joule = np.maximum(0.0, next_joule - RECOVERY_GAMMA * DT)

        cluster_size = count_active_cluster(field_state)
        total_mass = float(np.sum(field_joule))
        coherence_index = 1.0 - cluster_size / (GRID_SIZE * GRID_SIZE)

        run_cluster_sizes.append(cluster_size)
        run_mass_evolution.append(total_mass)
        run_coherence.append(coherence_index)

    return {
        "run_idx": run_idx,
        "d_coeff": d_coeff,
        "cluster_sizes": run_cluster_sizes,
        "mass_evolution": run_mass_evolution,
        "coherence": run_coherence,
        "peak_cluster": int(np.max(run_cluster_sizes)),
        "residual_mass": float(run_mass_evolution[-1]),
        "coherence_variance": float(np.var(run_coherence)),
    }


# ============================================================
# 2. PARAMETER SWEEP
# ============================================================

print("BIT-X16.1 Engine v1.1 running parameter sweep...")

for run_idx, d_coeff in enumerate(contagion_sweep):
    result = run_single_experiment(d_coeff, run_idx)

    history_sweep_cluster.append(result["cluster_sizes"])
    history_sweep_mass.append(result["mass_evolution"])
    history_sweep_coherence.append(result["coherence"])

    experiment_results.append({
        "experiment_run_id": result["run_idx"],
        "contagion_rate_D": round(result["d_coeff"], 2),
        "peak_overload_cluster_size": result["peak_cluster"],
        "residual_field_mass": round(result["residual_mass"], 3),
        "coherence_variance_score": round(result["coherence_variance"], 6),
    })


# ============================================================
# 3. EXPORT CSV
# ============================================================

csv_filename = "bit_x16_runtime_v11.csv"

with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=experiment_results[0].keys())
    writer.writeheader()
    writer.writerows(experiment_results)

print(f"CSV exported: {csv_filename}")


# ============================================================
# 4. PLOTS
# ============================================================

ticks_axis = np.arange(TICKS_PER_RUN)

plt.figure(figsize=(14, 6))

plt.subplot(1, 2, 1)
for i, d_val in enumerate(contagion_sweep):
    plt.plot(
        ticks_axis,
        history_sweep_cluster[i],
        linewidth=2,
        label=f"D = {d_val}"
    )

plt.axvspan(20, 45, alpha=0.08, label="Perturbation burst")
plt.title("X16.1 Parameter Sweep: Overload Cluster Sensitivity")
plt.xlabel("Simulation ticks")
plt.ylabel("Overload cluster size")
plt.legend()
plt.grid(True, alpha=0.25)


plt.subplot(1, 2, 2)
for i, d_val in enumerate(contagion_sweep):
    plt.plot(
        ticks_axis,
        history_sweep_mass[i],
        linewidth=2,
        label=f"D = {d_val}"
    )

plt.axvspan(20, 45, alpha=0.08, label="Perturbation burst")
plt.title("X16.1 Recovery Dynamics: Total Field Mass")
plt.xlabel("Simulation ticks")
plt.ylabel("Total metric field mass")
plt.legend()
plt.grid(True, alpha=0.25)

plt.tight_layout()

plot_filename = "bit_x16_sweep_plot.png"
plt.savefig(plot_filename, dpi=150)
print(f"Plot exported: {plot_filename}")

plt.show()


# ============================================================
# 5. PRINT SUMMARY
# ============================================================

print("\nExperiment summary:")
for row in experiment_results:
    print(row)

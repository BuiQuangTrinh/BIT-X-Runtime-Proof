#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BIT-X16.1 Benchmark Suite v0.2
Adaptive Shock Redistribution Runtime

Purpose:
- Validate X16.1 runtime behavior through parameter sweeps.
- Benchmark shock handling, overload cluster size, recovery, and coherence stability.

Outputs:
- x16_benchmark_summary.csv
- x16_benchmark_timeseries.csv
- x16_benchmark_suite_v02.png
"""

import csv
import math
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# 1. BASE CONFIG
# ============================================================

BASE_CONFIG = {
    "seed": 2026,
    "grid_size": 16,
    "ticks": 90,

    "shock_tick": 20,
    "shock_end": 45,
    "shock_center": (8, 8),
    "shock_amount": 24.0,

    "j_critical": 6.0,
    "n_base": 2.0,
    "n_max": 120.0,

    "diffusion_base": 0.16,
    "recovery_rate": 0.50,
    "mitosis_rate": 1.65,
    "process_rate": 0.035,
    "overhead_rate": 0.045,
}


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def order_parameter(field):
    s = np.sum(np.sin(field))
    c = np.sum(np.cos(field))
    return math.sqrt(s * s + c * c) / field.size


def neighbors4(x, y, grid_size):
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < grid_size and 0 <= ny < grid_size:
            yield nx, ny


def topology_zone(x, y, center):
    dx = x - center[0]
    dy = y - center[1]
    angle = math.atan2(dy, dx)
    if angle < 0:
        angle += 2 * math.pi
    return int(angle / (math.pi / 4)) % 8


def topology_params(zone):
    """
    8-zone topology behavior.
    This is only spatial partitioning for routing behavior.
    """
    if zone in [0, 4]:
        # Expansion zones
        return 1.35, 0.95, 1.35
    if zone in [1, 5]:
        # Damping zones
        return 0.75, 1.55, 0.85
    # Balanced zones
    return 1.00, 1.10, 1.00


def volume_coherence(j_field, j_critical):
    overloaded = np.sum(j_field > j_critical)
    return 1.0 - overloaded / j_field.size


def mitosis_coherence(n_field, n_base, n_max):
    excess_agents = np.sum(np.maximum(0.0, n_field - n_base))
    max_excess = n_field.size * (n_max - n_base)
    if max_excess <= 0:
        return 1.0
    return 1.0 - min(1.0, excess_agents / max_excess)


def total_coherence(c_phase, c_align, c_volume, c_mitosis):
    return 0.25 * c_phase + 0.25 * c_align + 0.30 * c_volume + 0.20 * c_mitosis


# ============================================================
# 3. SINGLE SIMULATION
# ============================================================

def run_x16_sim(config, label="run"):
    seed = config["seed"]
    np.random.seed(seed)

    grid_size = config["grid_size"]
    ticks = config["ticks"]

    shock_tick = config["shock_tick"]
    shock_end = config["shock_end"]
    shock_center = config["shock_center"]
    shock_amount = config["shock_amount"]

    j_critical = config["j_critical"]
    n_base = config["n_base"]
    n_max = config["n_max"]

    diffusion_base = config["diffusion_base"]
    recovery_rate = config["recovery_rate"]
    mitosis_rate = config["mitosis_rate"]
    process_rate = config["process_rate"]
    overhead_rate = config["overhead_rate"]

    j = np.zeros((grid_size, grid_size), dtype=float)
    n = np.ones((grid_size, grid_size), dtype=float) * n_base

    phase = np.random.uniform(-np.pi, np.pi, (grid_size, grid_size))
    align = np.random.uniform(-np.pi, np.pi, (grid_size, grid_size))

    center = np.array([(grid_size - 1) / 2.0, (grid_size - 1) / 2.0])

    ts = []

    for tick in range(ticks):

        # Main burst window
        if shock_tick <= tick <= shock_end:
            sx, sy = shock_center
            j[sx, sy] += shock_amount

            # Secondary random impacts around center
            if tick % 3 == 0:
                rx = np.random.randint(max(0, sx - 3), min(grid_size, sx + 4))
                ry = np.random.randint(max(0, sy - 3), min(grid_size, sy + 4))
                j[rx, ry] += shock_amount * 0.35

        c_phase = order_parameter(phase)
        c_align = order_parameter(align)
        c_volume = volume_coherence(j, j_critical)
        c_mitosis = mitosis_coherence(n, n_base, n_max)
        c_total = total_coherence(c_phase, c_align, c_volume, c_mitosis)

        next_j = j.copy()
        next_n = n.copy()
        next_phase = phase.copy()
        next_align = align.copy()

        for x in range(grid_size):
            for y in range(grid_size):
                current_j = j[x, y]
                current_n = n[x, y]
                zone = topology_zone(x, y, center)
                diffusion_mult, processing_mult, mitosis_mult = topology_params(zone)

                if current_j > 0.05:

                    # Agent multiplication / dynamic scaling
                    if current_j > j_critical:
                        excess = current_j - j_critical
                        target_agents = n_base + mitosis_rate * mitosis_mult * (excess ** 1.45)
                        next_n[x, y] = min(n_max, max(current_n, target_agents))

                    overhead = 1.0 + overhead_rate * math.log(current_n + 1.0)

                    processing_power = (
                        current_n
                        * process_rate
                        * processing_mult
                        * (0.70 + c_total)
                        / overhead
                    )

                    next_j[x, y] = max(0.0, next_j[x, y] - processing_power)

                    # Coupling: phase and alignment
                    p_glue = 0.0
                    a_glue = 0.0
                    count = 0

                    for nx, ny in neighbors4(x, y, grid_size):
                        p_glue += math.sin(phase[nx, ny] - phase[x, y])
                        a_glue += math.sin(align[nx, ny] - align[x, y])
                        count += 1

                    if count > 0:
                        next_phase[x, y] += 0.06 * p_glue
                        next_align[x, y] += 0.05 * a_glue

                    # Diffusion / redistribution
                    if current_j > j_critical:
                        excess = max(0.0, current_j - j_critical)
                        spread_amount = excess * diffusion_base * diffusion_mult

                        next_j[x, y] = max(0.0, next_j[x, y] - spread_amount)

                        neigh = list(neighbors4(x, y, grid_size))
                        if neigh:
                            share = spread_amount / len(neigh)
                            for nx, ny in neigh:
                                next_j[nx, ny] += share

                else:
                    # Agent deprovisioning
                    if current_n > n_base:
                        next_n[x, y] = max(n_base, current_n - 0.65)

        # Natural recovery
        next_j = np.maximum(0.0, next_j - recovery_rate)

        j = next_j
        n = next_n
        phase = next_phase
        align = next_align

        total_mass = float(np.sum(j))
        peak_stress = float(np.max(j))
        overload_cluster = int(np.sum(j > j_critical))
        peak_agents = float(np.max(n))

        ts.append({
            "label": label,
            "tick": tick,
            "total_mass": total_mass,
            "peak_stress": peak_stress,
            "overload_cluster": overload_cluster,
            "peak_agents": peak_agents,
            "c_phase": c_phase,
            "c_align": c_align,
            "c_volume": c_volume,
            "c_mitosis": c_mitosis,
            "c_total": c_total,
        })

    # Summary metrics
    recovery_time = None
    for row in ts:
        if row["tick"] > shock_end and row["peak_stress"] <= j_critical:
            recovery_time = row["tick"] - shock_end
            break

    if recovery_time is None:
        recovery_time = ticks - shock_end

    summary = {
        "label": label,
        "seed": seed,
        "diffusion_base": diffusion_base,
        "j_critical": j_critical,
        "recovery_rate": recovery_rate,
        "max_total_mass": max(r["total_mass"] for r in ts),
        "max_peak_stress": max(r["peak_stress"] for r in ts),
        "max_overload_cluster": max(r["overload_cluster"] for r in ts),
        "max_peak_agents": max(r["peak_agents"] for r in ts),
        "min_c_total": min(r["c_total"] for r in ts),
        "final_c_total": ts[-1]["c_total"],
        "recovery_time_after_burst": recovery_time,
    }

    return ts, summary


# ============================================================
# 4. BENCHMARK SUITE
# ============================================================

all_ts = []
all_summary = []

# Benchmark 1: Diffusion sweep
for d in [0.05, 0.15, 0.25, 0.35, 0.45]:
    cfg = dict(BASE_CONFIG)
    cfg["diffusion_base"] = d
    label = f"diffusion_D={d}"
    ts, summary = run_x16_sim(cfg, label)
    all_ts.extend(ts)
    all_summary.append(summary)

# Benchmark 2: Threshold sweep
for psi in [5.5, 6.5, 7.5, 8.5, 9.5]:
    cfg = dict(BASE_CONFIG)
    cfg["j_critical"] = psi
    label = f"threshold_PSI={psi}"
    ts, summary = run_x16_sim(cfg, label)
    all_ts.extend(ts)
    all_summary.append(summary)

# Benchmark 3: Recovery sweep
for gamma in [0.3, 0.5, 0.7, 0.9, 1.1]:
    cfg = dict(BASE_CONFIG)
    cfg["recovery_rate"] = gamma
    label = f"recovery_GAMMA={gamma}"
    ts, summary = run_x16_sim(cfg, label)
    all_ts.extend(ts)
    all_summary.append(summary)

# Benchmark 4: Seed sweep
for seed in [101, 202, 303, 404, 505]:
    cfg = dict(BASE_CONFIG)
    cfg["seed"] = seed
    label = f"seed={seed}"
    ts, summary = run_x16_sim(cfg, label)
    all_ts.extend(ts)
    all_summary.append(summary)


# ============================================================
# 5. EXPORT CSV
# ============================================================

summary_csv = "x16_benchmark_summary.csv"
timeseries_csv = "x16_benchmark_timeseries.csv"

with open(summary_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(all_summary[0].keys()))
    writer.writeheader()
    writer.writerows(all_summary)

with open(timeseries_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(all_ts[0].keys()))
    writer.writeheader()
    writer.writerows(all_ts)

print(f"Exported: {summary_csv}")
print(f"Exported: {timeseries_csv}")


# ============================================================
# 6. PLOT HELPERS
# ============================================================

def get_series(label, key):
    rows = [r for r in all_ts if r["label"] == label]
    rows = sorted(rows, key=lambda x: x["tick"])
    return [r["tick"] for r in rows], [r[key] for r in rows]


# ============================================================
# 7. BENCHMARK PLOTS
# ============================================================

plt.figure(figsize=(16, 10))

# Plot A: Diffusion sweep
plt.subplot(2, 2, 1)
for d in [0.05, 0.15, 0.25, 0.35, 0.45]:
    label = f"diffusion_D={d}"
    x, y = get_series(label, "overload_cluster")
    plt.plot(x, y, linewidth=1.8, label=f"D={d}")
plt.axvspan(BASE_CONFIG["shock_tick"], BASE_CONFIG["shock_end"], alpha=0.12)
plt.title("Benchmark 1: Diffusion Sweep — Overload Cluster")
plt.xlabel("Ticks")
plt.ylabel("Overload Cluster")
plt.legend()
plt.grid(True, alpha=0.25)

# Plot B: Threshold sweep
plt.subplot(2, 2, 2)
for psi in [5.5, 6.5, 7.5, 8.5, 9.5]:
    label = f"threshold_PSI={psi}"
    x, y = get_series(label, "overload_cluster")
    plt.plot(x, y, linewidth=1.8, label=f"PSI={psi}")
plt.axvspan(BASE_CONFIG["shock_tick"], BASE_CONFIG["shock_end"], alpha=0.12)
plt.title("Benchmark 2: Threshold Sweep — Overload Cluster")
plt.xlabel("Ticks")
plt.ylabel("Overload Cluster")
plt.legend()
plt.grid(True, alpha=0.25)

# Plot C: Recovery sweep
plt.subplot(2, 2, 3)
for gamma in [0.3, 0.5, 0.7, 0.9, 1.1]:
    label = f"recovery_GAMMA={gamma}"
    x, y = get_series(label, "total_mass")
    plt.plot(x, y, linewidth=1.8, label=f"GAMMA={gamma}")
plt.axvspan(BASE_CONFIG["shock_tick"], BASE_CONFIG["shock_end"], alpha=0.12)
plt.title("Benchmark 3: Recovery Sweep — Total Mass")
plt.xlabel("Ticks")
plt.ylabel("Metric Field Mass")
plt.legend()
plt.grid(True, alpha=0.25)

# Plot D: Seed sweep
plt.subplot(2, 2, 4)
for seed in [101, 202, 303, 404, 505]:
    label = f"seed={seed}"
    x, y = get_series(label, "c_total")
    plt.plot(x, y, linewidth=1.8, label=f"seed={seed}")
plt.axvspan(BASE_CONFIG["shock_tick"], BASE_CONFIG["shock_end"], alpha=0.12)
plt.title("Benchmark 4: Seed Sweep — Coherence Stability")
plt.xlabel("Ticks")
plt.ylabel("C_total")
plt.ylim(0, 1.05)
plt.legend()
plt.grid(True, alpha=0.25)

plt.tight_layout()
plot_name = "x16_benchmark_suite_v02.png"
plt.savefig(plot_name, dpi=180)
print(f"Exported: {plot_name}")

plt.show()


# ============================================================
# 8. PRINT SUMMARY
# ============================================================

print("\n=== BIT-X16.1 Benchmark Suite v0.2 Summary ===")
for row in all_summary:
    print(
        f"{row['label']} | "
        f"max_cluster={row['max_overload_cluster']} | "
        f"max_peak={row['max_peak_stress']:.2f} | "
        f"recovery={row['recovery_time_after_burst']} | "
        f"min_C={row['min_c_total']:.3f}"
    )

print("\nDone.")

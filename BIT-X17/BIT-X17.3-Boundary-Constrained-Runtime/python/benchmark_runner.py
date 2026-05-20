import csv
import os
import numpy as np

from bit_x17_3_runtime import BitX173Runtime


def ensure_dirs():
    os.makedirs("../csv", exist_ok=True)
    os.makedirs("../plots", exist_ok=True)


def run_benchmark():
    ensure_dirs()

    engine = BitX173Runtime(
        num_agents=3,
        d_target=5.0,
        steps=160,
        e_crit=6.0,
        k_min=0.4,
    )

    wind_intensities = [5.0, 8.5, 12.0]
    seeds = range(20)

    rows = []

    for wind in wind_intensities:
        for seed in seeds:
            bit_result = engine.run(seed=seed, use_bit=True, wind_intensity=wind)
            naive_result = engine.run(seed=seed, use_bit=False, wind_intensity=wind)

            bit_result["controller"] = "BIT-X17.3"
            naive_result["controller"] = "Naive"

            rows.append(bit_result)
            rows.append(naive_result)

    csv_path = "../csv/bit_x17_3_benchmark_results.csv"

    fieldnames = [
        "controller",
        "seed",
        "use_bit",
        "wind_intensity",
        "max_E",
        "min_distance",
        "corridor_occupancy",
        "collision_rate",
        "control_effort",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("\nBIT-X17.3 Benchmark Completed")
    print(f"CSV saved to: {csv_path}\n")

    print_summary(rows)


def print_summary(rows):
    controllers = sorted(set(r["controller"] for r in rows))
    winds = sorted(set(r["wind_intensity"] for r in rows))

    print("=" * 80)
    print("BIT-X17.3 Boundary-Constrained Runtime Benchmark Summary")
    print("=" * 80)

    for wind in winds:
        print(f"\nWind intensity: {wind}")
        for controller in controllers:
            subset = [
                r for r in rows
                if r["controller"] == controller and r["wind_intensity"] == wind
            ]

            mean_max_E = np.mean([r["max_E"] for r in subset])
            mean_min_d = np.mean([r["min_distance"] for r in subset])
            mean_corridor = np.mean([r["corridor_occupancy"] for r in subset])
            mean_collision = np.mean([r["collision_rate"] for r in subset])
            mean_effort = np.mean([r["control_effort"] for r in subset])

            print(
                f"  {controller:10s} | "
                f"Mean Max E: {mean_max_E:8.3f} | "
                f"Mean Min Dist: {mean_min_d:6.3f} | "
                f"Corridor: {mean_corridor:6.2f}% | "
                f"Collision: {mean_collision:6.2f}% | "
                f"Effort: {mean_effort:8.2f}"
            )

    print("\nStatus: Research Sandbox Benchmark")
    print("Note: This is a numerical prototype, not a formal mathematical proof.")
    print("=" * 80)


def export_history_example():
    engine = BitX173Runtime()
    result, history = engine.run(
        seed=42,
        use_bit=True,
        wind_intensity=8.5,
        return_history=True,
    )

    history_path = "../csv/bit_x17_3_runtime_history_seed42.csv"

    fieldnames = [
        "step",
        "E",
        "K",
        "min_distance",
        "kinetic_energy",
        "potential_energy",
        "control_effort",
        "triggered",
    ]

    with open(history_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(history)

    print(f"\nRuntime history saved to: {history_path}")


if __name__ == "__main__":
    run_benchmark()
    export_history_example()

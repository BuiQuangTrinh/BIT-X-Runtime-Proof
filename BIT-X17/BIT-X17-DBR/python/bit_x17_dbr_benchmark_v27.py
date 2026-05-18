import os
import csv
import time
from collections import Counter

import numpy as np
import matplotlib.pyplot as plt


class BitX17DbrBenchmarkV27:
    """
    BIT-X17-DBR Benchmark v2.7 Realism Runtime

    DBR = Dynamic Boundary Relaxation

    Purpose:
        - Run multiple adaptive boundary regulation contexts.
        - Export telemetry CSV.
        - Generate benchmark plots.
        - Add realism features:
            1. Shock events
            2. Small runtime noise
            3. Moving average smoothing
            4. Final Joule energy heatmaps
            5. State transition count chart

    Note:
        Omega is an illustrative sandbox snapshot, not a universal constant.
    """

    def __init__(self, seed=42):
        np.random.seed(seed)

        self.size = 8
        self.n_nodes = self.size * self.size
        self.dt = 0.05
        self.phi = 0.6180339887

        self.f_max_threshold = 0.618
        self.odi_min_threshold = 0.382

        self.benchmark_results = {}
        self.final_energy_maps = {}

        os.makedirs("csv", exist_ok=True)
        os.makedirs("plots", exist_ok=True)

    @staticmethod
    def moving_average(values, window=5):
        values = np.array(values, dtype=float)
        if len(values) < window:
            return values
        kernel = np.ones(window) / window
        smoothed = np.convolve(values, kernel, mode="same")
        return smoothed

    def apply_context_shock(self, tick, context_name, joule_energy):
        """
        Inject context-specific shock events.
        This makes the runtime less perfectly smooth and more like a real adaptive system.
        """
        if context_name == "STARTUP_STRESS" and tick in [35, 60]:
            shock = np.random.uniform(8.0, 18.0, (self.size, self.size))
            joule_energy += shock

        elif context_name == "AI_SWARM_ROUTING" and tick == 45:
            shock = np.random.uniform(2.0, 6.0, (self.size, self.size))
            joule_energy += shock

        elif context_name == "SOCIAL_CRISIS" and tick in [25, 40, 55, 70]:
            shock = np.random.uniform(10.0, 25.0, (self.size, self.size))
            joule_energy += shock

        return joule_energy

    def run_single_context(self, profile):
        context_name = profile["context_name"]
        print(f"\n[EXECUTION ACTIVE] Context: {context_name}")

        phases = np.random.uniform(-0.02, 0.02, (self.size, self.size))
        joule_energy = np.zeros((self.size, self.size))
        valve_timers = np.zeros((self.size, self.size))
        valve_open_mask = np.zeros((self.size, self.size))

        initial_load = profile["base_load"]

        # Boundary projection: split load to upper/lower boundaries.
        joule_energy[0:2, :] = initial_load * self.phi
        joule_energy[6:8, :] = initial_load * (1.0 - self.phi)

        beta_local = profile["local_diffusion_rate"]
        delta_local = profile["local_leak_rate"]
        willingness = profile["intrinsic_willingness"]

        for r in range(self.size):
            for c in range(self.size):
                valve_timers[r, c] = int(10 + joule_energy[r, c] * self.phi * 0.1)

        epoch_log = []

        for tick in range(1, 101):
            joule_energy = self.apply_context_shock(tick, context_name, joule_energy)

            next_joule = np.zeros((self.size, self.size))
            c_phase = np.abs(np.sum(np.exp(1j * phases))) / self.n_nodes

            # Measurement layer, normalized 0.0 - 1.0
            f_idx = float(np.clip(np.mean(joule_energy) / 400.0, 0.0, 1.0))

            odi_noise = np.random.normal(0.0, profile.get("odi_noise", 0.002))
            odi = float(np.clip(c_phase * (1.0 - f_idx) + odi_noise, 0.0, 1.0))

            mi_noise = np.random.normal(0.0, profile.get("mi_noise", 0.002))
            mi = float(
                np.clip(
                    np.exp(-self.phi * f_idx * 2.0) * willingness + mi_noise,
                    0.0,
                    1.0,
                )
            )

            # State transition
            if f_idx > self.f_max_threshold and mi < self.odi_min_threshold:
                state_name = "HOLD_STATION"
                beta_eff = 0.0
            elif odi < self.odi_min_threshold:
                state_name = "IDENTIFY"
                beta_eff = beta_local * 0.1
            elif tick < 12:
                state_name = "BOUND_PROJ"
                beta_eff = beta_local * 0.5
            else:
                state_name = "DISCHARGE"
                beta_eff = beta_local * (odi + self.phi)

            # Laplacian diffusion / discharge dynamics
            for r in range(self.size):
                for c in range(self.size):
                    r_up = (r - 1) % self.size
                    r_down = (r + 1) % self.size
                    c_left = (c - 1) % self.size
                    c_right = (c + 1) % self.size

                    if tick >= valve_timers[r, c] and state_name == "DISCHARGE":
                        valve_open_mask[r, c] = 1.0

                    if valve_open_mask[r, c] == 0.0:
                        next_joule[r, c] = joule_energy[r, c]
                    else:
                        laplacian_j = (
                            joule_energy[r_up, c]
                            + joule_energy[r_down, c]
                            + joule_energy[r, c_left]
                            + joule_energy[r, c_right]
                            - 4.0 * joule_energy[r, c]
                        )

                        next_joule[r, c] = joule_energy[r, c] + (
                            beta_eff * laplacian_j
                            - delta_local * joule_energy[r, c]
                        ) * self.dt

                        next_joule[r, c] = max(0.0, next_joule[r, c])

            joule_energy = next_joule

            if np.mean(joule_energy) < 0.05 and tick > 35:
                state_name = "RECOVERY"

            omega_snapshot = float(
                0.3 * c_phase + 0.7 * (1.0 / (1.0 + np.mean(joule_energy) * 0.01))
            )

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            entry = {
                "timestamp": timestamp,
                "tick": tick,
                "odi": odi,
                "f_friction": f_idx,
                "mi_drive": mi,
                "state": state_name,
                "omega_sandbox": omega_snapshot,
                "mean_joule_energy": float(np.mean(joule_energy)),
            }
            epoch_log.append(entry)

            if tick in [1, 15, 25, 35, 50, 70, 100] or state_name == "RECOVERY":
                print(
                    f"[{timestamp}] TICK_{tick:03d} | "
                    f"ODI: {odi:.4f} | "
                    f"F: {f_idx:.4f} | "
                    f"MI: {mi:.4f} | "
                    f"STATE: {state_name:<12} | "
                    f"Omega_snap: {omega_snapshot:.6f}"
                )

                if state_name == "RECOVERY":
                    break

        self.benchmark_results[context_name] = epoch_log
        self.final_energy_maps[context_name] = joule_energy.copy()
        self.export_to_csv(context_name, epoch_log)

    def export_to_csv(self, context_name, log_data):
        filename = f"csv/dbr_telemetry_{context_name.lower()}_v27.csv"

        fieldnames = [
            "timestamp",
            "tick",
            "odi",
            "f_friction",
            "mi_drive",
            "state",
            "omega_sandbox",
            "mean_joule_energy",
        ]

        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(log_data)

        print(f"[CSV SUCCESS] Saved: {filename}")

    def generate_comparison_plots(self):
        plt.figure(figsize=(14, 10))

        # Plot 1: Omega trajectories with moving average
        plt.subplot(2, 1, 1)
        for context_name, log_data in self.benchmark_results.items():
            ticks = [e["tick"] for e in log_data]
            omegas = [e["omega_sandbox"] for e in log_data]
            smooth = self.moving_average(omegas, window=5)
            plt.plot(ticks, omegas, alpha=0.25, linewidth=1.0)
            plt.plot(ticks, smooth, label="Omega MA(5) - " + context_name, linewidth=2.5)

        plt.title("BIT-X17-DBR v2.7: Omega Recovery Trajectories with Shock Events")
        plt.xlabel("Tick")
        plt.ylabel("Omega Snapshot")
        plt.grid(True, linestyle=":")
        plt.legend()

        # Plot 2: F vs ODI phase-space path
        plt.subplot(2, 1, 2)
        for context_name, log_data in self.benchmark_results.items():
            fs = [e["f_friction"] for e in log_data]
            odis = [e["odi"] for e in log_data]
            plt.plot(fs, odis, "o--", label="Trajectory Path - " + context_name, alpha=0.7)

        plt.title("DBR v2.7 Phase Space: Reality Friction F vs Orientation Direction ODI")
        plt.xlabel("Reality Friction Index F")
        plt.ylabel("Orientation Direction Index ODI")
        plt.grid(True, linestyle=":")
        plt.legend()

        plt.tight_layout()
        plot_path = "plots/dbr_v27_trajectory_benchmark_map.png"
        plt.savefig(plot_path, dpi=300)
        print(f"[PLOT SUCCESS] Saved: {plot_path}")
        plt.show()

    def generate_heatmaps(self):
        context_names = list(self.final_energy_maps.keys())
        n = len(context_names)

        plt.figure(figsize=(5 * n, 4))

        for i, context_name in enumerate(context_names, start=1):
            plt.subplot(1, n, i)
            plt.imshow(self.final_energy_maps[context_name])
            plt.title(context_name)
            plt.colorbar(label="Final Joule Energy")

        plt.tight_layout()
        path = "plots/dbr_v27_final_energy_heatmaps.png"
        plt.savefig(path, dpi=300)
        print(f"[HEATMAP SUCCESS] Saved: {path}")
        plt.show()

    def generate_state_count_chart(self):
        plt.figure(figsize=(12, 6))

        all_states = [
            "BOUND_PROJ",
            "HOLD_STATION",
            "IDENTIFY",
            "DISCHARGE",
            "RECOVERY",
        ]

        x = np.arange(len(all_states))
        width = 0.25

        for idx, (context_name, log_data) in enumerate(self.benchmark_results.items()):
            counts = Counter([e["state"] for e in log_data])
            values = [counts.get(state, 0) for state in all_states]
            plt.bar(x + idx * width, values, width, label=context_name)

        plt.xticks(x + width, all_states, rotation=20)
        plt.title("BIT-X17-DBR v2.7: State Transition Counts by Context")
        plt.xlabel("System State")
        plt.ylabel("Tick Count")
        plt.grid(True, axis="y", linestyle=":")
        plt.legend()

        plt.tight_layout()
        path = "plots/dbr_v27_state_transition_counts.png"
        plt.savefig(path, dpi=300)
        print(f"[STATE COUNT SUCCESS] Saved: {path}")
        plt.show()


def main():
    contexts_pool = [
        {
            "context_name": "STARTUP_STRESS",
            "base_load": 320.0,
            "local_diffusion_rate": 0.22,
            "local_leak_rate": 0.05,
            "intrinsic_willingness": 0.95,
            "odi_noise": 0.003,
            "mi_noise": 0.003,
        },
        {
            "context_name": "AI_SWARM_ROUTING",
            "base_load": 140.0,
            "local_diffusion_rate": 0.28,
            "local_leak_rate": 0.04,
            "intrinsic_willingness": 1.0,
            "odi_noise": 0.001,
            "mi_noise": 0.001,
        },
        {
            "context_name": "SOCIAL_CRISIS",
            "base_load": 260.0,
            "local_diffusion_rate": 0.08,
            "local_leak_rate": 0.07,
            "intrinsic_willingness": 0.42,
            "odi_noise": 0.006,
            "mi_noise": 0.006,
        },
    ]

    benchmark = BitX17DbrBenchmarkV27(seed=42)

    for context in contexts_pool:
        benchmark.run_single_context(context)

    benchmark.generate_comparison_plots()
    benchmark.generate_heatmaps()
    benchmark.generate_state_count_chart()

    print("\nDONE.")
    print("Generated files:")
    print("- csv/dbr_telemetry_startup_stress_v27.csv")
    print("- csv/dbr_telemetry_ai_swarm_routing_v27.csv")
    print("- csv/dbr_telemetry_social_crisis_v27.csv")
    print("- plots/dbr_v27_trajectory_benchmark_map.png")
    print("- plots/dbr_v27_final_energy_heatmaps.png")
    print("- plots/dbr_v27_state_transition_counts.png")


if __name__ == "__main__":
    main()

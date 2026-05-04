"""
BIT-X6.5 v0.1 — Boundary Information Navigation
Author: Bùi Quang Trịnh
Framework: Boundary Information Theory (BIT)

Purpose:
This script simulates a simplified boundary-centric navigation score
for deep space transit optimization.

It models:

1. Phase alignment
2. Boundary stability
3. Energy gain
4. Mission risk
5. Timing variance
6. Boundary navigation score B_nav
7. Corridor state

Outputs:
- boundary_navigation_log.csv
- bit_x6_5_boundary_navigation_output.png
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ------------------------------------------------------------
# 1. Simulation settings
# ------------------------------------------------------------

np.random.seed(42)

N = 180
time = np.arange(N)

EPSILON_BIT = 0.0225


# ------------------------------------------------------------
# 2. Simulate phase alignment A_phase
# ------------------------------------------------------------

phase_alignment = np.zeros(N)

for t in range(N):
    noise = np.random.normal(0, 0.03)

    # Mission enters better alignment around the middle region.
    base = 0.45 + 0.45 * np.exp(-((t - 95) ** 2) / (2 * 35 ** 2))

    phase_alignment[t] = np.clip(base + noise, 0.05, 1.0)


# ------------------------------------------------------------
# 3. Simulate position, velocity, and timing error
# ------------------------------------------------------------

position_error = np.zeros(N)
velocity_error = np.zeros(N)
timing_error = np.zeros(N)

for t in range(N):
    # Errors are lower near the corridor center.
    corridor_factor = np.exp(-((t - 95) ** 2) / (2 * 32 ** 2))

    position_error[t] = np.clip(0.08 - 0.055 * corridor_factor + np.random.normal(0, 0.006), 0.005, 0.15)
    velocity_error[t] = np.clip(0.07 - 0.048 * corridor_factor + np.random.normal(0, 0.006), 0.005, 0.15)
    timing_error[t] = np.clip(0.09 - 0.060 * corridor_factor + np.random.normal(0, 0.007), 0.005, 0.18)


# ------------------------------------------------------------
# 4. Compute boundary stability S_boundary
# ------------------------------------------------------------

lambda_r = 2.2
lambda_v = 2.0
lambda_t = 2.6

boundary_stability = 1 / (
    1
    + lambda_r * position_error
    + lambda_v * velocity_error
    + lambda_t * timing_error
)


# ------------------------------------------------------------
# 5. Energy gain and return feasibility
# ------------------------------------------------------------

energy_gain = np.zeros(N)
return_feasibility = np.zeros(N)

for t in range(N):
    corridor_factor = np.exp(-((t - 95) ** 2) / (2 * 40 ** 2))

    energy_gain[t] = np.clip(0.35 + 0.45 * corridor_factor + np.random.normal(0, 0.035), 0.05, 1.0)
    return_feasibility[t] = np.clip(0.45 + 0.35 * corridor_factor + np.random.normal(0, 0.03), 0.05, 1.0)


# ------------------------------------------------------------
# 6. Delta-v demand, risk, and trajectory variance
# ------------------------------------------------------------

delta_v = np.zeros(N)
mission_risk = np.zeros(N)
trajectory_variance = np.zeros(N)

for t in range(N):
    corridor_factor = np.exp(-((t - 95) ** 2) / (2 * 35 ** 2))

    delta_v[t] = np.clip(1.25 - 0.45 * corridor_factor + np.random.normal(0, 0.04), 0.35, 1.8)
    mission_risk[t] = np.clip(0.85 - 0.45 * corridor_factor + np.random.normal(0, 0.04), 0.15, 1.3)
    trajectory_variance[t] = np.clip(0.80 - 0.42 * corridor_factor + np.random.normal(0, 0.035), 0.12, 1.2)


# ------------------------------------------------------------
# 7. Compute boundary navigation score B_nav
# ------------------------------------------------------------

boundary_navigation_score = (
    phase_alignment
    * boundary_stability
    * energy_gain
    * return_feasibility
) / (
    delta_v
    * mission_risk
    * trajectory_variance
)


# ------------------------------------------------------------
# 8. Compute deviation from corridor sensitivity
# ------------------------------------------------------------

combined_error = (
    position_error
    + velocity_error
    + timing_error
) / 3

epsilon_deviation = combined_error - EPSILON_BIT


# ------------------------------------------------------------
# 9. Classify corridor state
# ------------------------------------------------------------

q1 = np.percentile(boundary_navigation_score, 35)
q2 = np.percentile(boundary_navigation_score, 65)
q3 = np.percentile(boundary_navigation_score, 85)

corridor_state = []
state_numeric = []

for score in boundary_navigation_score:
    if score < q1:
        corridor_state.append("outside")
        state_numeric.append(1)
    elif score < q2:
        corridor_state.append("edge")
        state_numeric.append(2)
    elif score < q3:
        corridor_state.append("corridor")
        state_numeric.append(3)
    else:
        corridor_state.append("core")
        state_numeric.append(4)


# ------------------------------------------------------------
# 10. Save CSV log
# ------------------------------------------------------------

df = pd.DataFrame({
    "time": time,
    "phase_alignment": phase_alignment,
    "position_error": position_error,
    "velocity_error": velocity_error,
    "timing_error": timing_error,
    "combined_error": combined_error,
    "epsilon_bit": EPSILON_BIT,
    "epsilon_deviation": epsilon_deviation,
    "boundary_stability": boundary_stability,
    "energy_gain": energy_gain,
    "return_feasibility": return_feasibility,
    "delta_v": delta_v,
    "mission_risk": mission_risk,
    "trajectory_variance": trajectory_variance,
    "boundary_navigation_score": boundary_navigation_score,
    "corridor_state": corridor_state,
    "state_numeric": state_numeric
})

df.to_csv("boundary_navigation_log.csv", index=False)


# ------------------------------------------------------------
# 11. Print summary
# ------------------------------------------------------------

print("BIT-X6.5 Boundary Information Navigation simulation completed.")
print("")
print("Summary metrics:")
print(f"Mean phase alignment:          {np.mean(phase_alignment):.4f}")
print(f"Mean boundary stability:       {np.mean(boundary_stability):.4f}")
print(f"Mean energy gain:              {np.mean(energy_gain):.4f}")
print(f"Mean navigation score B_nav:   {np.mean(boundary_navigation_score):.4f}")
print(f"Max navigation score B_nav:    {np.max(boundary_navigation_score):.4f}")
print(f"Mean combined error:           {np.mean(combined_error):.4f}")
print(f"ε_BIT threshold:               {EPSILON_BIT:.4f}")
print("")
print("Generated files:")
print("- boundary_navigation_log.csv")
print("- bit_x6_5_boundary_navigation_output.png")


# ------------------------------------------------------------
# 12. Plot four-layer navigation chart
# ------------------------------------------------------------

plt.figure(figsize=(12, 11))

# Layer 1 — Phase alignment
plt.subplot(4, 1, 1)
plt.plot(time, phase_alignment)
plt.title("Layer 1 — Phase Alignment A_phase")
plt.ylabel("A_phase")
plt.ylim(0, 1.05)
plt.grid(True, alpha=0.3)

# Layer 2 — Boundary stability
plt.subplot(4, 1, 2)
plt.plot(time, boundary_stability)
plt.title("Layer 2 — Boundary Stability S_boundary")
plt.ylabel("S_boundary")
plt.ylim(0, 1.05)
plt.grid(True, alpha=0.3)

# Layer 3 — Boundary navigation score
plt.subplot(4, 1, 3)
plt.plot(time, boundary_navigation_score)
plt.axhline(q1, linestyle="--", label="Edge threshold")
plt.axhline(q2, linestyle="--", label="Corridor threshold")
plt.axhline(q3, linestyle="--", label="Core threshold")
plt.title("Layer 3 — Boundary Navigation Score B_nav")
plt.ylabel("B_nav")
plt.legend()
plt.grid(True, alpha=0.3)

# Layer 4 — Corridor state
plt.subplot(4, 1, 4)
plt.step(time, state_numeric, where="mid")
plt.yticks(
    [1, 2, 3, 4],
    ["outside", "edge", "corridor", "core"]
)
plt.title("Layer 4 — Corridor State")
plt.xlabel("Time")
plt.ylabel("State")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("bit_x6_5_boundary_navigation_output.png", dpi=200)

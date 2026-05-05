# BIT-X6.6 v0.1 — Boundary Mission Control
# Adaptive Multi-Objective Control Under Dynamic Boundary Conditions
#
# Boundary Information Theory (BIT)
# Author: Bùi Quang Trịnh (Vietnam)
# Companions: OpenAI GPT & Google Gemini
#
# This is a conceptual / experimental simulation.
# It is not production control logic, mission design software, financial advice,
# aerospace guidance, AI safety certification, or engineering validation.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# 1. Simulation setup
# -----------------------------

np.random.seed(42)

N = 240
t = np.arange(N)

OUTPUT_CSV = "boundary_mission_control_log.csv"
OUTPUT_PNG = "bit_x6_6_boundary_mission_control_output.png"


# -----------------------------
# 2. Helper functions
# -----------------------------

def clip01(x):
    """Clip values into the range [0, 1]."""
    return np.clip(x, 0.0, 1.0)


def moving_average(x, window=7):
    """Simple moving average with edge-safe padding."""
    return pd.Series(x).rolling(window=window, min_periods=1).mean().values


def classify_control_state(score, stability, energy, risk_control, goal_alignment, uncertainty):
    """
    Classify mission control state.

    Higher score is better.
    Lower stability, energy, risk control, or goal alignment increases danger.
    Higher uncertainty increases danger.
    """

    if stability < 0.22 or energy < 0.18 or risk_control < 0.18 or goal_alignment < 0.25:
        return "abort"

    if uncertainty > 0.72 or score < 0.35:
        return "recover"

    if score < 0.50:
        return "protect"

    if score < 0.68:
        return "adjust"

    return "optimal"


def action_from_state(state):
    """Map mission control state into action."""
    action_map = {
        "optimal": "continue",
        "adjust": "adaptive_correction",
        "protect": "reduce_speed_or_load",
        "recover": "recovery_maneuver",
        "abort": "safe_stop",
    }
    return action_map[state]


def state_to_number(state):
    """Numeric encoding for plotting."""
    state_map = {
        "optimal": 4,
        "adjust": 3,
        "protect": 2,
        "recover": 1,
        "abort": 0,
    }
    return state_map[state]


# -----------------------------
# 3. Generate mission signals
# -----------------------------

# Mission stability S:
# Starts stable, then experiences disturbance zones.
base_stability = 0.82 - 0.0015 * t
disturbance_1 = 0.22 * np.exp(-((t - 70) / 18) ** 2)
disturbance_2 = 0.34 * np.exp(-((t - 155) / 26) ** 2)
disturbance_3 = 0.18 * np.exp(-((t - 210) / 14) ** 2)
noise_stability = np.random.normal(0, 0.025, N)

stability = clip01(
    base_stability
    - disturbance_1
    - disturbance_2
    - disturbance_3
    + noise_stability
)

# Energy margin E:
# Slowly decreases as mission continues, with correction costs.
energy_margin = 0.90 - 0.0022 * t
energy_drain_events = (
    0.10 * np.exp(-((t - 90) / 22) ** 2)
    + 0.15 * np.exp(-((t - 170) / 30) ** 2)
)
noise_energy = np.random.normal(0, 0.018, N)

energy = clip01(energy_margin - energy_drain_events + noise_energy)

# Raw risk:
# Higher during boundary disturbance windows.
raw_risk = (
    0.18
    + 0.26 * np.exp(-((t - 70) / 16) ** 2)
    + 0.42 * np.exp(-((t - 155) / 24) ** 2)
    + 0.28 * np.exp(-((t - 210) / 13) ** 2)
    + np.random.normal(0, 0.025, N)
)
raw_risk = clip01(raw_risk)

# Risk control R:
# Higher is safer, defined as inverse of raw risk.
risk_control = clip01(1.0 - raw_risk)

# Goal alignment G:
# Drifts downward when risk and instability increase.
goal_drift = (
    0.08 * np.sin(t / 18)
    + 0.20 * np.exp(-((t - 150) / 28) ** 2)
    + 0.12 * np.exp(-((t - 205) / 16) ** 2)
)
goal_alignment = clip01(0.88 - goal_drift + np.random.normal(0, 0.02, N))

# Correction cost C:
# Higher when instability and risk are high.
correction_cost = clip01(
    0.18
    + 0.38 * (1 - stability)
    + 0.32 * raw_risk
    + np.random.normal(0, 0.018, N)
)

# Variance V:
# Represents mission fluctuation / instability.
variance = clip01(
    moving_average(np.abs(np.gradient(stability)), window=9) * 7.0
    + 0.12 * raw_risk
)

# Uncertainty U:
# Higher when stability, energy, and goal alignment weaken.
uncertainty = clip01(
    0.15
    + 0.30 * (1 - stability)
    + 0.22 * (1 - energy)
    + 0.25 * (1 - goal_alignment)
    + 0.15 * raw_risk
    + np.random.normal(0, 0.02, N)
)


# -----------------------------
# 4. Adaptive mission-control weights
# -----------------------------

# Initial weights
W_s = np.zeros(N)  # stability weight
W_e = np.zeros(N)  # energy weight
W_r = np.zeros(N)  # risk-control weight
W_g = np.zeros(N)  # goal-alignment weight

for i in range(N):
    # Base importance
    ws = 1.00
    we = 0.90
    wr = 1.00
    wg = 0.90

    # Adaptive priority rules
    if raw_risk[i] > 0.45:
        wr += 0.55

    if stability[i] < 0.55:
        ws += 0.50

    if energy[i] < 0.45:
        we += 0.45

    if goal_alignment[i] < 0.60:
        wg += 0.45

    # Normalize weights so they remain comparable
    total = ws + we + wr + wg
    W_s[i] = ws / total
    W_e[i] = we / total
    W_r[i] = wr / total
    W_g[i] = wg / total


# -----------------------------
# 5. Boundary Mission Control score
# -----------------------------

# Core conceptual score:
#
# M_control = (W_s*S + W_e*E + W_r*R + W_g*G) / (C + V + U)
#
# To keep score readable in [0, 1], denominator is stabilized.

benefit = (
    W_s * stability
    + W_e * energy
    + W_r * risk_control
    + W_g * goal_alignment
)

penalty = correction_cost + variance + uncertainty

mission_control_score_raw = benefit / (1.0 + penalty)
mission_control_score = clip01(mission_control_score_raw)


# -----------------------------
# 6. Control state and action
# -----------------------------

control_states = []
control_actions = []
state_numbers = []

for i in range(N):
    state = classify_control_state(
        score=mission_control_score[i],
        stability=stability[i],
        energy=energy[i],
        risk_control=risk_control[i],
        goal_alignment=goal_alignment[i],
        uncertainty=uncertainty[i],
    )
    action = action_from_state(state)

    control_states.append(state)
    control_actions.append(action)
    state_numbers.append(state_to_number(state))

state_numbers = np.array(state_numbers)


# -----------------------------
# 7. Build output table
# -----------------------------

df = pd.DataFrame({
    "t": t,
    "stability_S": stability,
    "energy_margin_E": energy,
    "raw_risk": raw_risk,
    "risk_control_R": risk_control,
    "goal_alignment_G": goal_alignment,
    "correction_cost_C": correction_cost,
    "variance_V": variance,
    "uncertainty_U": uncertainty,
    "weight_stability_Ws": W_s,
    "weight_energy_We": W_e,
    "weight_risk_Wr": W_r,
    "weight_goal_Wg": W_g,
    "mission_control_score": mission_control_score,
    "control_state": control_states,
    "control_action": control_actions,
    "control_state_number": state_numbers,
})

df.to_csv(OUTPUT_CSV, index=False)


# -----------------------------
# 8. Plot result
# -----------------------------

plt.figure(figsize=(14, 12))

# Layer 1 — Mission condition variables
plt.subplot(4, 1, 1)
plt.plot(t, stability, label="Stability S")
plt.plot(t, energy, label="Energy Margin E")
plt.plot(t, risk_control, label="Risk Control R")
plt.plot(t, goal_alignment, label="Goal Alignment G")
plt.ylim(0, 1.05)
plt.ylabel("Condition")
plt.title("BIT-X6.6 Boundary Mission Control — Mission Conditions")
plt.legend(loc="lower left")
plt.grid(True, alpha=0.3)

# Layer 2 — Adaptive weights
plt.subplot(4, 1, 2)
plt.plot(t, W_s, label="W_s Stability")
plt.plot(t, W_e, label="W_e Energy")
plt.plot(t, W_r, label="W_r Risk")
plt.plot(t, W_g, label="W_g Goal")
plt.ylim(0, 0.55)
plt.ylabel("Adaptive Weight")
plt.title("Adaptive Mission-Control Weights")
plt.legend(loc="upper left")
plt.grid(True, alpha=0.3)

# Layer 3 — Mission Control Score
plt.subplot(4, 1, 3)
plt.plot(t, mission_control_score, label="Mission Control Score")
plt.axhline(0.68, linestyle="--", linewidth=1, label="Optimal Threshold")
plt.axhline(0.50, linestyle="--", linewidth=1, label="Protect Threshold")
plt.axhline(0.35, linestyle="--", linewidth=1, label="Recover Threshold")
plt.ylim(0, 1.05)
plt.ylabel("M_control")
plt.title("Boundary Mission Control Score")
plt.legend(loc="lower left")
plt.grid(True, alpha=0.3)

# Layer 4 — Control state
plt.subplot(4, 1, 4)
plt.step(t, state_numbers, where="mid", label="Control State")
plt.yticks(
    [0, 1, 2, 3, 4],
    ["abort", "recover", "protect", "adjust", "optimal"]
)
plt.ylim(-0.5, 4.5)
plt.xlabel("Time Step")
plt.ylabel("State")
plt.title("Mission Control State")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=180)
plt.close()


# -----------------------------
# 9. Print summary
# -----------------------------

state_counts = df["control_state"].value_counts().to_dict()
action_counts = df["control_action"].value_counts().to_dict()

print("BIT-X6.6 Boundary Mission Control simulation complete.")
print(f"Saved CSV: {OUTPUT_CSV}")
print(f"Saved PNG: {OUTPUT_PNG}")
print()
print("Control state counts:")
for k, v in state_counts.items():
    print(f"  {k}: {v}")

print()
print("Control action counts:")
for k, v in action_counts.items():
    print(f"  {k}: {v}")

print()
print("Final mission control score:", round(float(mission_control_score[-1]), 4))
print("Final control state:", control_states[-1])
print("Final control action:", control_actions[-1])

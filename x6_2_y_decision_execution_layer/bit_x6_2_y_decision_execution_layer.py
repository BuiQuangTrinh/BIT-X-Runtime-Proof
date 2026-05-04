"""
BIT-X6.2-Y v0.1 — Decision / Execution Layer
Author: Bùi Quang Trịnh (Vietnam)
Framework: Boundary Information Theory (BIT)

Purpose:
This script simulates a lightweight decision/execution layer.

It maps boundary diagnostic states into safe execution actions:

stable   -> continue
warning  -> reduce_load
critical -> safe_stop

Outputs:
- decision_execution_log.csv
- bit_x6_2_y_decision_execution_output.png
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ------------------------------------------------------------
# 1. Simulation settings
# ------------------------------------------------------------

np.random.seed(42)

N = 160
time = np.arange(N)


# ------------------------------------------------------------
# 2. Simulate Boundary Interaction Index Ξ
# ------------------------------------------------------------

xi = np.zeros(N)

for t in range(N):
    noise = np.random.normal(0, 2.0)

    if t < 55:
        base = 15 + 0.04 * t
    elif t < 105:
        base = 18 + 0.22 * (t - 55)
    else:
        base = 29 + 0.55 * (t - 105)

    xi[t] = max(0, base + noise)


# ------------------------------------------------------------
# 3. Define diagnostic thresholds
# ------------------------------------------------------------

warning_threshold = 28
critical_threshold = 42


# ------------------------------------------------------------
# 4. Convert diagnostics into execution actions
# ------------------------------------------------------------

states = []
actions = []
action_score = []

for value in xi:
    if value < warning_threshold:
        states.append("stable")
        actions.append("continue")
        action_score.append(1)

    elif value < critical_threshold:
        states.append("warning")
        actions.append("reduce_load")
        action_score.append(2)

    else:
        states.append("critical")
        actions.append("safe_stop")
        action_score.append(3)


# ------------------------------------------------------------
# 5. Simulate system load after execution decision
# ------------------------------------------------------------

system_load = np.zeros(N)
system_load[0] = 1.0

for t in range(1, N):
    if actions[t] == "continue":
        delta = np.random.normal(0.005, 0.01)

    elif actions[t] == "reduce_load":
        delta = np.random.normal(-0.015, 0.01)

    else:
        delta = np.random.normal(-0.035, 0.015)

    system_load[t] = np.clip(system_load[t - 1] + delta, 0.2, 1.2)


# ------------------------------------------------------------
# 6. Save CSV log
# ------------------------------------------------------------

df = pd.DataFrame({
    "time": time,
    "boundary_interaction_xi": xi,
    "state": states,
    "execution_action": actions,
    "action_score": action_score,
    "system_load": system_load
})

df.to_csv("decision_execution_log.csv", index=False)


# ------------------------------------------------------------
# 7. Plot result
# ------------------------------------------------------------

plt.figure(figsize=(12, 9))

# Layer 1 — Boundary Interaction Index
plt.subplot(3, 1, 1)
plt.plot(time, xi)
plt.axhline(warning_threshold, linestyle="--", label="Warning threshold")
plt.axhline(critical_threshold, linestyle="--", label="Critical threshold")
plt.title("Layer 1 — Boundary Interaction Index Ξ")
plt.ylabel("Ξ")
plt.legend()
plt.grid(True, alpha=0.3)

# Layer 2 — Execution Action
plt.subplot(3, 1, 2)
plt.step(time, action_score, where="mid")
plt.yticks([1, 2, 3], ["continue", "reduce_load", "safe_stop"])
plt.title("Layer 2 — Decision / Execution Action")
plt.ylabel("Action")
plt.grid(True, alpha=0.3)

# Layer 3 — System Load
plt.subplot(3, 1, 3)
plt.plot(time, system_load)
plt.title("Layer 3 — System Load After Decision")
plt.xlabel("Time")
plt.ylabel("Load")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("bit_x6_2_y_decision_execution_output.png", dpi=200)

print("BIT-X6.2-Y Decision / Execution simulation completed.")
print("Generated files:")
print("- decision_execution_log.csv")
print("- bit_x6_2_y_decision_execution_output.png")

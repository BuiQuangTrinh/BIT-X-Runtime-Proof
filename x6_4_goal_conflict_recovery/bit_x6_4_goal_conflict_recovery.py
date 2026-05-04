"""
BIT-X6.4 v0.1 — Goal Conflict Recovery
Author: Bùi Quang Trịnh (Vietnam)
Framework: Boundary Information Theory (BIT)

Purpose:
This script simulates goal conflict recovery in an adaptive agent.

It models the case where a user goal depends on memory that may be
missing, delayed, or uncertain.

Outputs:
- goal_conflict_recovery_log.csv
- bit_x6_4_goal_conflict_recovery_output.png
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

MAX_DELAY = 20


# ------------------------------------------------------------
# 2. Simulate goal dependency
# ------------------------------------------------------------

goal_dependency = np.zeros(N)

for t in range(N):
    noise = np.random.normal(0, 0.03)

    if t < 45:
        base = 0.20
    elif t < 90:
        base = 0.45 + 0.004 * (t - 45)
    elif t < 130:
        base = 0.68 + 0.003 * (t - 90)
    else:
        base = 0.82 + 0.002 * (t - 130)

    goal_dependency[t] = np.clip(base + noise, 0.0, 1.0)


# ------------------------------------------------------------
# 3. Simulate memory confidence
# ------------------------------------------------------------

memory_confidence = np.zeros(N)

for t in range(N):
    noise = np.random.normal(0, 0.025)

    if t < 50:
        base = 0.92
    elif t < 95:
        base = 0.85 - 0.006 * (t - 50)
    elif t < 135:
        base = 0.58 - 0.004 * (t - 95)
    else:
        base = 0.40 - 0.003 * (t - 135)

    memory_confidence[t] = np.clip(base + noise, 0.05, 1.0)


# ------------------------------------------------------------
# 4. Simulate temporal delay in memory retrieval
# ------------------------------------------------------------

temporal_delay = np.zeros(N)

for t in range(N):
    noise = np.random.normal(0, 0.8)

    if t < 55:
        base = 3
    elif t < 105:
        base = 5 + 0.12 * (t - 55)
    else:
        base = 11 + 0.10 * (t - 105)

    temporal_delay[t] = np.clip(base + noise, 1, MAX_DELAY)


# ------------------------------------------------------------
# 5. Compute goal conflict score
# ------------------------------------------------------------

delay_factor = 1 + temporal_delay / MAX_DELAY

conflict_score = goal_dependency * (1 - memory_confidence) * delay_factor

# Smooth the conflict score to represent agent-level assessment.
rolling_conflict = (
    pd.Series(conflict_score)
    .rolling(window=8, min_periods=1)
    .mean()
    .values
)


# ------------------------------------------------------------
# 6. Define thresholds
# ------------------------------------------------------------

memory_needed_threshold = 0.18
conflict_detected_threshold = 0.36
confirmation_required_threshold = 0.55


# ------------------------------------------------------------
# 7. Classify recovery state and action
# ------------------------------------------------------------

recovery_state = []
recovery_action = []
action_numeric = []

for value in rolling_conflict:
    if value < memory_needed_threshold:
        recovery_state.append("clear")
        recovery_action.append("execute")
        action_numeric.append(1)

    elif value < conflict_detected_threshold:
        recovery_state.append("memory_needed")
        recovery_action.append("retrieve_memory")
        action_numeric.append(2)

    elif value < confirmation_required_threshold:
        recovery_state.append("conflict_detected")
        recovery_action.append("compare_context")
        action_numeric.append(3)

    else:
        recovery_state.append("confirmation_required")
        recovery_action.append("ask_confirmation")
        action_numeric.append(4)


# ------------------------------------------------------------
# 8. Simulate execution safety
# ------------------------------------------------------------

# Higher value means safer behavior.
# The agent becomes safer when it avoids direct execution under conflict.
execution_safety = np.zeros(N)

for t in range(N):
    if recovery_action[t] == "execute":
        execution_safety[t] = 1.0 - rolling_conflict[t]

    elif recovery_action[t] == "retrieve_memory":
        execution_safety[t] = 0.78

    elif recovery_action[t] == "compare_context":
        execution_safety[t] = 0.86

    else:
        execution_safety[t] = 0.94

execution_safety = np.clip(execution_safety, 0.0, 1.0)


# ------------------------------------------------------------
# 9. Save CSV log
# ------------------------------------------------------------

df = pd.DataFrame({
    "time": time,
    "goal_dependency": goal_dependency,
    "memory_confidence": memory_confidence,
    "temporal_delay": temporal_delay,
    "delay_factor": delay_factor,
    "conflict_score": conflict_score,
    "rolling_conflict": rolling_conflict,
    "recovery_state": recovery_state,
    "recovery_action": recovery_action,
    "action_numeric": action_numeric,
    "execution_safety": execution_safety
})

df.to_csv("goal_conflict_recovery_log.csv", index=False)


# ------------------------------------------------------------
# 10. Print summary
# ------------------------------------------------------------

print("BIT-X6.4 Goal Conflict Recovery simulation completed.")
print("")
print("Summary metrics:")
print(f"Mean goal dependency:       {np.mean(goal_dependency):.4f}")
print(f"Mean memory confidence:     {np.mean(memory_confidence):.4f}")
print(f"Mean temporal delay:        {np.mean(temporal_delay):.4f}")
print(f"Mean conflict score:        {np.mean(rolling_conflict):.4f}")
print(f"Max conflict score:         {np.max(rolling_conflict):.4f}")
print(f"Mean execution safety:      {np.mean(execution_safety):.4f}")
print("")
print("Generated files:")
print("- goal_conflict_recovery_log.csv")
print("- bit_x6_4_goal_conflict_recovery_output.png")


# ------------------------------------------------------------
# 11. Plot four-layer recovery chart
# ------------------------------------------------------------

plt.figure(figsize=(12, 11))

# Layer 1 — Goal dependency
plt.subplot(4, 1, 1)
plt.plot(time, goal_dependency)
plt.title("Layer 1 — Goal Dependency")
plt.ylabel("Dependency")
plt.ylim(0, 1.05)
plt.grid(True, alpha=0.3)

# Layer 2 — Memory confidence
plt.subplot(4, 1, 2)
plt.plot(time, memory_confidence)
plt.title("Layer 2 — Memory Confidence")
plt.ylabel("Confidence")
plt.ylim(0, 1.05)
plt.grid(True, alpha=0.3)

# Layer 3 — Goal conflict score
plt.subplot(4, 1, 3)
plt.plot(time, rolling_conflict)
plt.axhline(memory_needed_threshold, linestyle="--", label="Memory needed")
plt.axhline(conflict_detected_threshold, linestyle="--", label="Conflict detected")
plt.axhline(confirmation_required_threshold, linestyle="--", label="Confirmation required")
plt.title("Layer 3 — Goal Conflict Score")
plt.ylabel("Conflict")
plt.legend()
plt.grid(True, alpha=0.3)

# Layer 4 — Recovery action
plt.subplot(4, 1, 4)
plt.step(time, action_numeric, where="mid")
plt.yticks(
    [1, 2, 3, 4],
    ["execute", "retrieve_memory", "compare_context", "ask_confirmation"]
)
plt.title("Layer 4 — Recovery Action")
plt.xlabel("Time")
plt.ylabel("Action")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("bit_x6_4_goal_conflict_recovery_output.png", dpi=200)

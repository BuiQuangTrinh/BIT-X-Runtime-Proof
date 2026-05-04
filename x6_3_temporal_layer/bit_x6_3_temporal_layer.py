"""
BIT-X6.3 v0.1 — Temporal Boundary Layer
Author: Bùi Quang Trịnh (Vietnam)
Framework: Boundary Information Theory (BIT)

Purpose:
This script simulates temporal boundary drift.

It compares:

1. Incoming signal S(t)
2. Delayed system response R(t - τ)
3. Temporal Boundary Error TBE(t)
4. Temporal warning / critical regimes

Core idea:
A system may fail not because it lacks information,
but because its response arrives too late.

Outputs:
- temporal_boundary_log.csv
- bit_x6_3_temporal_boundary_output.png
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

BASE_DELAY = 3
MAX_DELAY = 18


# ------------------------------------------------------------
# 2. Generate incoming signal S(t)
# ------------------------------------------------------------

signal = np.zeros(N)

for t in range(N):
    noise = np.random.normal(0, 0.08)

    # Stable oscillation phase
    if t < 60:
        signal[t] = np.sin(t / 8) + noise

    # Transition phase
    elif t < 115:
        signal[t] = np.sin(t / 7) + 0.006 * (t - 60) + noise

    # Instability phase
    else:
        signal[t] = np.sin(t / 5) + 0.015 * (t - 115) + noise


# ------------------------------------------------------------
# 3. Simulate growing response delay τ(t)
# ------------------------------------------------------------

delay = np.zeros(N, dtype=int)

for t in range(N):
    if t < 55:
        delay[t] = BASE_DELAY

    elif t < 110:
        delay[t] = BASE_DELAY + int((t - 55) / 9)

    else:
        delay[t] = BASE_DELAY + int((t - 110) / 4)

    delay[t] = min(delay[t], MAX_DELAY)


# ------------------------------------------------------------
# 4. Generate delayed response R(t - τ)
# ------------------------------------------------------------

response = np.zeros(N)

for t in range(N):
    delayed_index = max(0, t - delay[t])

    # Response is delayed and slightly smoothed
    if t == 0:
        response[t] = signal[delayed_index]
    else:
        response[t] = 0.85 * response[t - 1] + 0.15 * signal[delayed_index]


# ------------------------------------------------------------
# 5. Compute Temporal Boundary Error TBE(t)
# ------------------------------------------------------------

temporal_boundary_error = np.abs(signal - response)

rolling_tbe = (
    pd.Series(temporal_boundary_error)
    .rolling(window=10, min_periods=1)
    .mean()
    .values
)

warning_threshold = np.percentile(rolling_tbe, 70)
critical_threshold = np.percentile(rolling_tbe, 88)


# ------------------------------------------------------------
# 6. Temporal state classification
# ------------------------------------------------------------

temporal_state = []
state_numeric = []

for value in rolling_tbe:
    if value < warning_threshold:
        temporal_state.append("synchronized")
        state_numeric.append(1)

    elif value < critical_threshold:
        temporal_state.append("drifting")
        state_numeric.append(2)

    else:
        temporal_state.append("desynchronized")
        state_numeric.append(3)


# ------------------------------------------------------------
# 7. Recovery pressure index
# ------------------------------------------------------------

# Recovery pressure increases when delay and error rise together.
recovery_pressure = rolling_tbe * (1 + delay / MAX_DELAY)

recovery_warning = np.percentile(recovery_pressure, 70)
recovery_critical = np.percentile(recovery_pressure, 88)


# ------------------------------------------------------------
# 8. Save CSV log
# ------------------------------------------------------------

df = pd.DataFrame({
    "time": time,
    "incoming_signal": signal,
    "delayed_response": response,
    "delay_tau": delay,
    "temporal_boundary_error": temporal_boundary_error,
    "rolling_tbe": rolling_tbe,
    "recovery_pressure": recovery_pressure,
    "temporal_state": temporal_state,
    "state_numeric": state_numeric
})

df.to_csv("temporal_boundary_log.csv", index=False)


# ------------------------------------------------------------
# 9. Print summary
# ------------------------------------------------------------

print("BIT-X6.3 Temporal Boundary Layer simulation completed.")
print("")
print("Temporal metrics:")
print(f"Mean delay τ:              {np.mean(delay):.2f}")
print(f"Max delay τ:               {np.max(delay)}")
print(f"Mean TBE:                  {np.mean(rolling_tbe):.4f}")
print(f"Max TBE:                   {np.max(rolling_tbe):.4f}")
print(f"Warning threshold TBE:     {warning_threshold:.4f}")
print(f"Critical threshold TBE:    {critical_threshold:.4f}")
print("")
print("Generated files:")
print("- temporal_boundary_log.csv")
print("- bit_x6_3_temporal_boundary_output.png")


# ------------------------------------------------------------
# 10. Plot temporal boundary system
# ------------------------------------------------------------

plt.figure(figsize=(12, 11))

# Layer 1 — Signal vs response
plt.subplot(4, 1, 1)
plt.plot(time, signal, label="Incoming Signal S(t)")
plt.plot(time, response, label="Delayed Response R(t - τ)")
plt.title("Layer 1 — Incoming Signal vs Delayed Response")
plt.ylabel("Signal")
plt.legend()
plt.grid(True, alpha=0.3)

# Layer 2 — Response delay
plt.subplot(4, 1, 2)
plt.plot(time, delay)
plt.title("Layer 2 — Response Delay τ(t)")
plt.ylabel("Delay")
plt.grid(True, alpha=0.3)

# Layer 3 — Temporal Boundary Error
plt.subplot(4, 1, 3)
plt.plot(time, rolling_tbe)
plt.axhline(warning_threshold, linestyle="--", label="Warning threshold")
plt.axhline(critical_threshold, linestyle="--", label="Critical threshold")
plt.title("Layer 3 — Temporal Boundary Error TBE(t)")
plt.ylabel("TBE")
plt.legend()
plt.grid(True, alpha=0.3)

# Layer 4 — Temporal state
plt.subplot(4, 1, 4)
plt.step(time, state_numeric, where="mid")
plt.yticks(
    [1, 2, 3],
    ["synchronized", "drifting", "desynchronized"]
)
plt.title("Layer 4 — Temporal Boundary State")
plt.xlabel("Time")
plt.ylabel("State")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("bit_x6_3_temporal_boundary_output.png", dpi=200)

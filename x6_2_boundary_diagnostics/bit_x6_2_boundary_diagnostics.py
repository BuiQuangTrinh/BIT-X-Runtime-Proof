"""
BIT-X6.2 — Boundary Diagnostics Simulation
Author: Bùi Quang Trịnh (Vietnam)
Framework: Boundary Information Theory (BIT)

Purpose:
This script simulates a three-layer boundary diagnostic system:

Layer 1 — Observable output signal
Layer 2 — Effective adaptive capacity alpha_eff
Layer 3 — Boundary Interaction Index Xi

The goal is not to predict any real-world market or system directly.
This is a conceptual simulation showing how boundary-aware diagnostics
may detect internal weakening before visible collapse.

Outputs:
- sample_output.csv
- bit_x6_2_full_system_output.png
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

BASE_PRICE = 100.0
BASE_ALPHA = 0.0225


# ------------------------------------------------------------
# 2. Generate observable output layer
# ------------------------------------------------------------

price = np.zeros(N)
price[0] = BASE_PRICE

for t in range(1, N):
    noise = np.random.normal(0, 0.25)

    # Stable phase
    if t < 80:
        drift = 0.00

    # Stress accumulation phase
    elif t < 115:
        drift = 0.05

    # Boundary failure phase
    else:
        drift = -0.45

    price[t] = price[t - 1] + drift + noise


# ------------------------------------------------------------
# 3. Generate effective adaptive capacity layer
# ------------------------------------------------------------

alpha_eff = np.zeros(N)
alpha_eff[0] = BASE_ALPHA

for t in range(1, N):
    noise = np.random.normal(0, 0.00003)

    # Gradual weakening under accumulated pressure
    weakening = 0.000004 * max(0, t - 40)

    alpha_eff[t] = BASE_ALPHA - weakening + noise

    # Keep value inside a reasonable conceptual range
    alpha_eff[t] = np.clip(alpha_eff[t], 0.0195, 0.0225)


# ------------------------------------------------------------
# 4. Boundary stress and Boundary Interaction Index
# ------------------------------------------------------------

price_change = np.abs(np.diff(price, prepend=price[0]))

rolling_stress = pd.Series(price_change).rolling(window=12, min_periods=1).mean().values

capacity_gap = BASE_ALPHA - alpha_eff

xi = 1000 * rolling_stress * (1 + capacity_gap * 100000)

# Warning thresholds
xi_warning = np.percentile(xi, 75)
xi_critical = np.percentile(xi, 90)


# ------------------------------------------------------------
# 5. Generate diagnostic state labels
# ------------------------------------------------------------

states = []

for value in xi:
    if value < xi_warning:
        states.append("stable")
    elif value < xi_critical:
        states.append("warning")
    else:
        states.append("critical")


# ------------------------------------------------------------
# 6. Save CSV output
# ------------------------------------------------------------

df = pd.DataFrame({
    "time": time,
    "price": price,
    "alpha_eff": alpha_eff,
    "rolling_stress": rolling_stress,
    "boundary_interaction_xi": xi,
    "state": states
})

df.to_csv("sample_output.csv", index=False)


# ------------------------------------------------------------
# 7. Plot full diagnostic system
# ------------------------------------------------------------

plt.figure(figsize=(12, 9))

# Layer 1
plt.subplot(3, 1, 1)
plt.plot(time, price)
plt.title("Layer 1 — Price")
plt.ylabel("Output")
plt.grid(True, alpha=0.3)

# Layer 2
plt.subplot(3, 1, 2)
plt.plot(time, alpha_eff)
plt.title("Layer 2 — Effective Adaptive Capacity α_eff")
plt.ylabel("α_eff")
plt.grid(True, alpha=0.3)

# Layer 3
plt.subplot(3, 1, 3)
plt.plot(time, xi)
plt.axhline(xi_warning, linestyle="--", label="Warning threshold")
plt.axhline(xi_critical, linestyle="--", label="Critical threshold")
plt.title("Layer 3 — Boundary Interaction Index Ξ")
plt.xlabel("Time")
plt.ylabel("Ξ")
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("bit_x6_2_full_system_output.png", dpi=200)

print("BIT-X6.2 Boundary Diagnostics simulation completed.")
print("Generated files:")
print("- sample_output.csv")
print("- bit_x6_2_full_system_output.png")

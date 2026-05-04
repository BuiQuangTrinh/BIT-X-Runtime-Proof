"""
BIT-X6.2-D v0.1 — Validation / Deployment Layer
Author: Bùi Quang Trịnh (Vietnam)
Framework: Boundary Information Theory (BIT)

Purpose:
This script validates whether boundary-aware decisions reduce risk
during unstable regimes.

It compares:

1. Baseline exposure
2. BIT-controlled exposure
3. Drawdown reduction
4. False alarm rate
5. Missed danger rate
6. Stability score

Outputs:
- validation_deployment_log.csv
- bit_x6_2_d_validation_output.png
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
# 2. Simulate price / external signal
# ------------------------------------------------------------

price = np.zeros(N)
price[0] = BASE_PRICE

for t in range(1, N):
    noise = np.random.normal(0, 0.35)

    if t < 70:
        drift = 0.02
    elif t < 115:
        drift = 0.08
    else:
        drift = -0.50

    price[t] = price[t - 1] + drift + noise


# ------------------------------------------------------------
# 3. Compute simplified diagnostic layer A
# ------------------------------------------------------------

price_change = np.abs(np.diff(price, prepend=price[0]))

rolling_stress = (
    pd.Series(price_change)
    .rolling(window=12, min_periods=1)
    .mean()
    .values
)

alpha_eff = np.zeros(N)
alpha_eff[0] = BASE_ALPHA

for t in range(1, N):
    weakening = 0.0000045 * max(0, t - 40)
    noise = np.random.normal(0, 0.000025)

    alpha_eff[t] = BASE_ALPHA - weakening + noise
    alpha_eff[t] = np.clip(alpha_eff[t], 0.0195, 0.0225)

capacity_gap = BASE_ALPHA - alpha_eff

xi = 1000 * rolling_stress * (1 + capacity_gap * 100000)

warning_threshold = np.percentile(xi, 70)
critical_threshold = np.percentile(xi, 88)


# ------------------------------------------------------------
# 4. Decision layer Y
# ------------------------------------------------------------

decision_state = []
exposure = []

for value in xi:
    if value < warning_threshold:
        decision_state.append("allow")
        exposure.append(1.00)

    elif value < critical_threshold:
        decision_state.append("reduce")
        exposure.append(0.60)

    elif value < critical_threshold * 1.25:
        decision_state.append("restrict")
        exposure.append(0.30)

    else:
        decision_state.append("freeze")
        exposure.append(0.00)

exposure = np.array(exposure)


# ------------------------------------------------------------
# 5. Baseline vs BIT-controlled return
# ------------------------------------------------------------

returns = np.diff(price, prepend=price[0]) / np.maximum(price, 1e-9)

baseline_equity = np.zeros(N)
bit_equity = np.zeros(N)

baseline_equity[0] = 1.0
bit_equity[0] = 1.0

for t in range(1, N):
    baseline_equity[t] = baseline_equity[t - 1] * (1 + returns[t])
    bit_equity[t] = bit_equity[t - 1] * (1 + exposure[t] * returns[t])


# ------------------------------------------------------------
# 6. Validation metrics
# ------------------------------------------------------------

def max_drawdown(equity_curve):
    running_max = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - running_max) / running_max
    return drawdown.min(), drawdown


baseline_mdd, baseline_drawdown = max_drawdown(baseline_equity)
bit_mdd, bit_drawdown = max_drawdown(bit_equity)

if baseline_mdd != 0:
    stability_score = 1 - (abs(bit_mdd) / abs(baseline_mdd))
else:
    stability_score = 0.0


# ------------------------------------------------------------
# 7. False alarm and missed danger
# ------------------------------------------------------------

future_window = 8
danger_drop_threshold = -0.035

false_alarms = 0
warnings = 0
missed_dangers = 0
danger_events = 0

for t in range(N - future_window):
    future_return = (price[t + future_window] - price[t]) / price[t]

    warned = decision_state[t] in ["reduce", "restrict", "freeze"]
    danger = future_return <= danger_drop_threshold

    if warned:
        warnings += 1
        if not danger:
            false_alarms += 1

    if danger:
        danger_events += 1
        if not warned:
            missed_dangers += 1

false_alarm_rate = false_alarms / warnings if warnings > 0 else 0.0
missed_danger_rate = missed_dangers / danger_events if danger_events > 0 else 0.0


# ------------------------------------------------------------
# 8. Save validation log
# ------------------------------------------------------------

decision_numeric = {
    "allow": 1,
    "reduce": 2,
    "restrict": 3,
    "freeze": 4
}

df = pd.DataFrame({
    "time": time,
    "price": price,
    "alpha_eff": alpha_eff,
    "rolling_stress": rolling_stress,
    "boundary_interaction_xi": xi,
    "decision_state": decision_state,
    "decision_numeric": [decision_numeric[s] for s in decision_state],
    "exposure": exposure,
    "baseline_equity": baseline_equity,
    "bit_equity": bit_equity,
    "baseline_drawdown": baseline_drawdown,
    "bit_drawdown": bit_drawdown
})

df.to_csv("validation_deployment_log.csv", index=False)


# ------------------------------------------------------------
# 9. Print summary
# ------------------------------------------------------------

print("BIT-X6.2-D Validation / Deployment simulation completed.")
print("")
print("Validation metrics:")
print(f"Baseline max drawdown: {baseline_mdd:.4f}")
print(f"BIT max drawdown:      {bit_mdd:.4f}")
print(f"Stability score:       {stability_score:.4f}")
print(f"False alarm rate:      {false_alarm_rate:.4f}")
print(f"Missed danger rate:    {missed_danger_rate:.4f}")
print("")
print("Generated files:")
print("- validation_deployment_log.csv")
print("- bit_x6_2_d_validation_output.png")


# ------------------------------------------------------------
# 10. Plot four-layer validation chart
# ------------------------------------------------------------

plt.figure(figsize=(12, 11))

# Layer 1 — Price
plt.subplot(4, 1, 1)
plt.plot(time, price)
plt.title("Layer 1 — Price / External Signal")
plt.ylabel("Price")
plt.grid(True, alpha=0.3)

# Layer 2 — Adaptive capacity
plt.subplot(4, 1, 2)
plt.plot(time, alpha_eff)
plt.title("Layer 2 — Effective Adaptive Capacity α_eff")
plt.ylabel("α_eff")
plt.grid(True, alpha=0.3)

# Layer 3 — Boundary Interaction Index
plt.subplot(4, 1, 3)
plt.plot(time, xi)
plt.axhline(warning_threshold, linestyle="--", label="Warning threshold")
plt.axhline(critical_threshold, linestyle="--", label="Critical threshold")
plt.title("Layer 3 — Boundary Interaction Index Ξ")
plt.ylabel("Ξ")
plt.legend()
plt.grid(True, alpha=0.3)

# Layer 4 — Decision state
plt.subplot(4, 1, 4)
plt.step(
    time,
    [decision_numeric[s] for s in decision_state],
    where="mid"
)
plt.yticks(
    [1, 2, 3, 4],
    ["allow", "reduce", "restrict", "freeze"]
)
plt.title("Layer 4 — Decision State Y")
plt.xlabel("Time")
plt.ylabel("Decision")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("bit_x6_2_d_validation_output.png", dpi=200)

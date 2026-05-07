import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# BIT-X8.3 v0.2
# Earth–Moon Curved Boundary Corridor Simulation
# Author: Bui Quang Trinh (Vietnam)
# Companions: OpenAI GPT & Google Gemini
# ============================================================


G = 6.67430e-11

M_earth = 5.972e24
M_moon = 7.342e22

distance_earth_moon = 384_400_000  # meters

earth_pos = np.array([0.0, 0.0])
moon_pos = np.array([distance_earth_moon, 0.0])


num_steps = 900
dt = 60 * 10  # 10 minutes per step

spacecraft_pos = np.array([7_000_000.0, 2_000_000.0])
spacecraft_vel = np.array([1050.0, 80.0])


corridor_width = 45_000_000
corridor_amplitude = 28_000_000

safe_pressure_threshold = 0.65
critical_pressure_threshold = 0.85

max_speed = 1250.0


def gravity_acceleration(pos, body_pos, body_mass):
    r_vec = body_pos - pos
    r = np.linalg.norm(r_vec)

    if r < 1:
        return np.array([0.0, 0.0])

    return G * body_mass * r_vec / (r ** 3)


def corridor_center_y(x):
    progress = np.clip(
        x / distance_earth_moon,
        0.0,
        1.0
    )

    return corridor_amplitude * np.sin(np.pi * progress)


def corridor_slope(x):
    progress = np.clip(
        x / distance_earth_moon,
        0.0,
        1.0
    )

    return (
        corridor_amplitude
        * np.pi
        / distance_earth_moon
        * np.cos(np.pi * progress)
    )


def boundary_pressure(pos, vel):
    x, y = pos

    center_y = corridor_center_y(x)

    y_error = abs(y - center_y)
    y_pressure = y_error / corridor_width

    slope = corridor_slope(x)
    tangent = np.array([1.0, slope])
    tangent = tangent / np.linalg.norm(tangent)

    normal = np.array([-tangent[1], tangent[0]])

    normal_velocity = abs(np.dot(vel, normal))
    velocity_pressure = normal_velocity / 1200.0

    dist_earth = np.linalg.norm(pos - earth_pos)
    dist_moon = np.linalg.norm(pos - moon_pos)

    balance_ratio = min(dist_earth, dist_moon) / max(dist_earth, dist_moon)
    balance_pressure = 1 - balance_ratio

    pressure = (
        0.50 * y_pressure
        + 0.35 * velocity_pressure
        + 0.15 * balance_pressure
    )

    return max(0.0, min(1.0, pressure))


def corridor_correction(pos, vel, pressure):
    x, y = pos
    center_y = corridor_center_y(x)

    y_error = y - center_y

    correction = np.array([0.0, 0.0])

    if pressure > safe_pressure_threshold:
        pull_strength = 0.0025 * pressure
        damping_strength = 0.0012

        correction[1] += -pull_strength * np.sign(y_error)
        correction[1] += -damping_strength * vel[1]

    return correction


def limit_speed(vel):
    speed = np.linalg.norm(vel)

    if speed > max_speed:
        return vel * (max_speed / speed)

    return vel


log = []

for step in range(num_steps):
    acc_earth = gravity_acceleration(
        spacecraft_pos,
        earth_pos,
        M_earth
    )

    acc_moon = gravity_acceleration(
        spacecraft_pos,
        moon_pos,
        M_moon
    )

    total_acc = acc_earth + acc_moon

    pressure = boundary_pressure(
        spacecraft_pos,
        spacecraft_vel
    )

    correction_acc = corridor_correction(
        spacecraft_pos,
        spacecraft_vel,
        pressure
    )

    total_acc += correction_acc

    spacecraft_vel = spacecraft_vel + total_acc * dt
    spacecraft_vel = limit_speed(spacecraft_vel)

    spacecraft_pos = spacecraft_pos + spacecraft_vel * dt

    distance_to_moon = np.linalg.norm(
        spacecraft_pos - moon_pos
    )

    distance_to_earth = np.linalg.norm(
        spacecraft_pos - earth_pos
    )

    center_y = corridor_center_y(spacecraft_pos[0])
    corridor_error = spacecraft_pos[1] - center_y

    if pressure < safe_pressure_threshold:
        status = "STABLE_CORRIDOR"
    elif pressure < critical_pressure_threshold:
        status = "BOUNDARY_WARNING"
    else:
        status = "CRITICAL_DRIFT"

    log.append({
        "step": step,
        "time_hours": step * dt / 3600,
        "x_m": spacecraft_pos[0],
        "y_m": spacecraft_pos[1],
        "corridor_center_y_m": center_y,
        "corridor_error_m": corridor_error,
        "vx_m_s": spacecraft_vel[0],
        "vy_m_s": spacecraft_vel[1],
        "speed_m_s": np.linalg.norm(spacecraft_vel),
        "distance_to_earth_m": distance_to_earth,
        "distance_to_moon_m": distance_to_moon,
        "boundary_pressure": pressure,
        "status": status
    })


df = pd.DataFrame(log)

csv_file = "bit_x8_3_v02_curved_corridor_log.csv"
df.to_csv(csv_file, index=False)


x_curve = np.linspace(
    0,
    distance_earth_moon,
    500
)

y_curve = np.array([
    corridor_center_y(x)
    for x in x_curve
])

upper_curve = y_curve + corridor_width
lower_curve = y_curve - corridor_width


plt.figure(figsize=(12, 6))

plt.plot(
    df["x_m"] / 1e6,
    df["y_m"] / 1e6,
    label="Spacecraft Trajectory"
)

plt.plot(
    x_curve / 1e6,
    y_curve / 1e6,
    linestyle="--",
    label="Curved Corridor Center"
)

plt.plot(
    x_curve / 1e6,
    upper_curve / 1e6,
    linestyle=":",
    label="Upper Corridor Boundary"
)

plt.plot(
    x_curve / 1e6,
    lower_curve / 1e6,
    linestyle=":",
    label="Lower Corridor Boundary"
)

plt.scatter(
    earth_pos[0] / 1e6,
    earth_pos[1] / 1e6,
    s=160,
    label="Earth"
)

plt.scatter(
    moon_pos[0] / 1e6,
    moon_pos[1] / 1e6,
    s=100,
    label="Moon"
)

plt.title("BIT-X8.3 v0.2 — Earth–Moon Curved Boundary Corridor")
plt.xlabel("X Position (million meters)")
plt.ylabel("Y Position (million meters)")
plt.legend()
plt.grid(True)
plt.tight_layout()

plot_file = "result_plot_x8_3_v02_curved_corridor.png"
plt.savefig(plot_file, dpi=300)
plt.show()


plt.figure(figsize=(12, 5))

plt.plot(
    df["time_hours"],
    df["boundary_pressure"],
    label="Boundary Pressure"
)

plt.axhline(
    y=safe_pressure_threshold,
    linestyle="--",
    label="Safe Threshold"
)

plt.axhline(
    y=critical_pressure_threshold,
    linestyle="--",
    label="Critical Threshold"
)

plt.title("BIT-X8.3 v0.2 — Boundary Pressure Over Time")
plt.xlabel("Time (hours)")
plt.ylabel("Boundary Pressure")
plt.ylim(0, 1)
plt.legend()
plt.grid(True)
plt.tight_layout()

pressure_plot_file = "result_pressure_x8_3_v02.png"
plt.savefig(pressure_plot_file, dpi=300)
plt.show()


print("BIT-X8.3 v0.2 Simulation Complete")
print(f"Saved CSV: {csv_file}")
print(f"Saved Trajectory Plot: {plot_file}")
print(f"Saved Pressure Plot: {pressure_plot_file}")

print("\nFinal Status:")
print(df.iloc[-1][[
    "time_hours",
    "x_m",
    "y_m",
    "corridor_error_m",
    "distance_to_moon_m",
    "boundary_pressure",
    "status"
]])

print("\nStatus Counts:")
print(df["status"].value_counts())

print("\nMinimum Distance to Moon (m):")
print(df["distance_to_moon_m"].min())

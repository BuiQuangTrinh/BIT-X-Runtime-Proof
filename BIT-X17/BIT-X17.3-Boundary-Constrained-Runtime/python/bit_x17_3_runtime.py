import numpy as np


class BitX173Runtime:
    """
    BIT-X17.3
    Boundary-Constrained Swarm Corridor Runtime

    Research sandbox for:
    - boundary-triggered recovery
    - geometric constraint restoration
    - damping-based energy dissipation
    - swarm corridor stabilization
    """

    def __init__(
        self,
        num_agents=3,
        d_target=5.0,
        dt=0.1,
        steps=160,
        mass=1.2,
        drag=0.25,
        f_max=25.0,
        k_lattice=12.5,
        c_damping=1.8,
        e_crit=6.0,
        k_min=0.4,
        collision_distance=1.5,
        sensor_noise_std=0.02,
        wind_noise_std=0.15,
    ):
        self.num_agents = num_agents
        self.d_target = d_target
        self.dt = dt
        self.steps = steps
        self.mass = mass
        self.drag = drag
        self.f_max = f_max
        self.k_lattice = k_lattice
        self.c_damping = c_damping
        self.e_crit = e_crit
        self.k_min = k_min
        self.collision_distance = collision_distance
        self.sensor_noise_std = sensor_noise_std
        self.wind_noise_std = wind_noise_std

    def initial_state(self):
        if self.num_agents == 3:
            pos = np.array([
                [0.0, 0.0],
                [self.d_target, 0.0],
                [0.5 * self.d_target, 0.866 * self.d_target],
            ], dtype=float)
        else:
            angles = np.linspace(0, 2 * np.pi, self.num_agents, endpoint=False)
            radius = self.d_target
            pos = np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])

        vel = np.tile(np.array([2.5, 0.0]), (self.num_agents, 1)).astype(float)
        return pos, vel

    def pair_indices(self):
        pairs = []
        for i in range(self.num_agents):
            for j in range(i + 1, self.num_agents):
                pairs.append((i, j))
        return pairs

    def compute_metrics(self, pos, vel):
        pairs = self.pair_indices()
        distances = []

        for i, j in pairs:
            distances.append(np.linalg.norm(pos[i] - pos[j]))

        distances = np.array(distances)

        # Smooth geometric deviation energy
        E = 0.5 * np.sum((distances - self.d_target) ** 2)

        headings = np.array([np.arctan2(v[1], v[0]) for v in vel])
        theta_group = np.mean(headings)
        K = np.mean(np.cos(headings - theta_group))

        min_d = float(np.min(distances))

        kinetic_energy = 0.5 * self.mass * np.sum(np.linalg.norm(vel, axis=1) ** 2)
        potential_energy = E * self.k_lattice

        return {
            "E": E,
            "K": K,
            "min_distance": min_d,
            "kinetic_energy": kinetic_energy,
            "potential_energy": potential_energy,
        }

    def control_force(self, pos, vel, use_bit=True):
        F = np.zeros_like(pos)

        if not use_bit:
            # Naive controller: weak pull toward center
            center = np.mean(pos, axis=0)
            for i in range(self.num_agents):
                direction = center - pos[i]
                norm = np.linalg.norm(direction) + 1e-9
                F[i] += 2.5 * direction / norm
            return F

        metrics = self.compute_metrics(pos, vel)
        trigger = (metrics["E"] > self.e_crit) or (metrics["K"] < self.k_min)

        # Boundary-constrained recovery activates mainly when needed
        if not trigger:
            return F

        for i, j in self.pair_indices():
            diff = pos[i] - pos[j]
            d_ij = np.linalg.norm(diff) + 1e-9
            u_ij = diff / d_ij

            error = d_ij - self.d_target
            v_rel = vel[i] - vel[j]

            F_lattice = (
                -self.k_lattice * error * u_ij
                -self.c_damping * np.dot(v_rel, u_ij) * u_ij
            )

            F[i] += 0.5 * F_lattice
            F[j] -= 0.5 * F_lattice

            # Emergency collision guard
            if d_ij < 2.2:
                repel = (6.0 / (d_ij ** 2)) * u_ij
                F[i] += repel
                F[j] -= repel

        # Velocity synchronization during recovery
        v_mean = np.mean(vel, axis=0)
        for i in range(self.num_agents):
            F[i] += 5.5 * (v_mean - vel[i])

        return F

    def run(
        self,
        seed=42,
        use_bit=True,
        wind_intensity=8.5,
        wind_start=40,
        wind_end=100,
        return_history=False,
    ):
        rng = np.random.default_rng(seed)
        pos, vel = self.initial_state()

        history = []
        max_E = 0.0
        min_distance_seen = float("inf")
        collision_ticks = 0
        outside_ticks = 0
        total_control_effort = 0.0

        base_wind = np.array([-1.0, 0.7]) * wind_intensity

        for t in range(self.steps):
            pos_measured = pos + rng.normal(0, self.sensor_noise_std, pos.shape)

            metrics = self.compute_metrics(pos_measured, vel)

            E = metrics["E"]
            K = metrics["K"]
            min_d = metrics["min_distance"]

            max_E = max(max_E, E)
            min_distance_seen = min(min_distance_seen, min_d)

            if min_d < self.collision_distance:
                collision_ticks += 1

            if E > self.e_crit or K < self.k_min or min_d < self.collision_distance:
                outside_ticks += 1

            F_control = self.control_force(pos_measured, vel, use_bit=use_bit)

            if wind_start <= t <= wind_end:
                wind_noise = rng.normal(0, self.wind_noise_std, 2)
                F_wind = base_wind + wind_noise
            else:
                F_wind = np.zeros(2)

            for i in range(self.num_agents):
                F_total = F_control[i] + F_wind - self.drag * vel[i]

                mag = np.linalg.norm(F_total)
                if mag > self.f_max:
                    F_total = (F_total / mag) * self.f_max

                total_control_effort += np.linalg.norm(F_total) * self.dt

                vel[i] += (F_total / self.mass) * self.dt
                pos[i] += vel[i] * self.dt

            if return_history:
                history.append({
                    "step": t,
                    "E": E,
                    "K": K,
                    "min_distance": min_d,
                    "kinetic_energy": metrics["kinetic_energy"],
                    "potential_energy": metrics["potential_energy"],
                    "control_effort": total_control_effort,
                    "triggered": int(E > self.e_crit or K < self.k_min),
                })

        corridor_occupancy = 100.0 * (self.steps - outside_ticks) / self.steps
        collision_rate = 100.0 * collision_ticks / self.steps

        result = {
            "seed": seed,
            "use_bit": use_bit,
            "wind_intensity": wind_intensity,
            "max_E": max_E,
            "min_distance": min_distance_seen,
            "corridor_occupancy": corridor_occupancy,
            "collision_rate": collision_rate,
            "control_effort": total_control_effort,
        }

        if return_history:
            return result, history

        return result

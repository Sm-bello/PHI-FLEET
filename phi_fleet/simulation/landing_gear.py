"""
Physics simulation of an Aircraft Oleo-Pneumatic Landing Gear Shock Strut.

Models non-linear gas compression (polytropic gas law), hydraulic orifice damping,
seal friction, and thermal dissipation during touchdown and rollout cycles.
"""

import math
import random
from typing import Dict, Any
from phi_fleet.simulation.base import BaseAssetSimulator, TelemetryFrame


class LandingGearSimulator(BaseAssetSimulator):
    def __init__(self, asset_id: str, sampling_dt: float = 0.02):
        super().__init__(asset_id, sampling_dt)
        # Nominal physical parameters (Oleo-pneumatic strut)
        self.p0_nominal = 45.0          # Nominal nitrogen precharge (bar)
        self.V0 = 0.012                 # Initial chamber volume (m^3)
        self.Ah = 0.015                 # Hydraulic piston area (m^2)
        self.gamma = 1.35               # Polytropic gas expansion index
        self.Cd = 0.70                  # Orifice discharge coefficient
        self.Ao_nominal = 0.00015       # Metering orifice area (m^2)
        self.rho_oil = 870.0            # Hydraulic oil density (kg/m^3)
        self.M_sprung = 14500.0         # Aircraft corner mass (kg)

        self.reset()

    def reset(self, initial_degradation: float = 0.0) -> None:
        self.current_time = 0.0
        self.degradation = initial_degradation
        self.stroke = 0.08              # Initial taxi/touchdown stroke (m)
        self.stroke_vel = 0.0           # Velocity (m/s)
        self.strut_temp = 20.0          # Initial temperature (°C)
        self.cycle_count = 0


    def step(self, operating_conditions: Dict[str, float]) -> TelemetryFrame:
        """
        Advance one simulation step.
        Operating conditions:
          - 'sink_rate': touchdown vertical velocity (m/s)
          - 'ambient_temp': outside air temperature (°C)
          - 'aircraft_weight_factor': 0.8 to 1.3 (payload variation)
        """
        self.current_time += self.dt
        sink_rate = operating_conditions.get("sink_rate", 2.2)
        amb_temp = operating_conditions.get("ambient_temp", 22.0)
        weight_factor = operating_conditions.get("aircraft_weight_factor", 1.0)

        # Degradation impacts physical parameters:
        # 1. Nitrogen seal micro-leakage: p0 drops up to 35%
        # 2. Hydraulic oil viscosity degradation & metering pin wear: changes effective damping
        p0_effective = self.p0_nominal * (1.0 - 0.35 * self.degradation)
        Ao_effective = self.Ao_nominal * (1.0 + 0.15 * self.degradation)

        # Touchdown dynamic excitation profile
        t_phase = self.current_time % 10.0  # 10s landing/touchdown sequence
        if t_phase < 1.5:
            # Impact stroke compression
            target_stroke = 0.28 * weight_factor * (sink_rate / 2.5) * math.sin(math.pi * t_phase / 1.5)
        elif t_phase < 5.0:
            # Taxiing oscillation
            decay = math.exp(-(t_phase - 1.5) * 0.8)
            target_stroke = 0.10 * weight_factor + 0.05 * decay * math.sin(6.0 * (t_phase - 1.5))
        else:
            # Steady rollout / taxi
            target_stroke = 0.08 * weight_factor + 0.005 * math.sin(1.5 * t_phase)

        # Update stroke & velocity with dynamic response
        target_stroke = max(0.001, min(0.38, target_stroke))
        new_vel = (target_stroke - self.stroke) / self.dt
        self.stroke = target_stroke
        self.stroke_vel = new_vel

        # 1. Pneumatic spring force (Polytropic gas compression)
        # F_gas = p0 * Ah * (V0 / (V0 - Ah * s))^gamma
        vol_current = max(0.002, self.V0 - self.Ah * self.stroke)
        p_gas_pa = (p0_effective * 1e5) * ((self.V0 / vol_current) ** self.gamma)
        F_gas = p_gas_pa * self.Ah  # (N)

        # 2. Hydraulic damping force
        # F_oil = 0.5 * rho * Ah^3 / (Cd * Ao)^2 * vel^2 * sgn(vel)
        orifice_const = (self.Cd * Ao_effective) ** 2
        F_oil = 0.5 * self.rho_oil * (self.Ah ** 3) * (self.stroke_vel ** 2) / orifice_const
        if self.stroke_vel < 0:
            F_oil = -F_oil

        # 3. Total reaction load (kN)
        F_total_kn = (F_gas + F_oil) / 1000.0

        # 4. Strut Temperature model (°C) - viscous heating & environmental convection
        heat_gen = 0.00008 * abs(F_oil * self.stroke_vel)
        heat_dissipation = 0.08 * (self.strut_temp - amb_temp)
        self.strut_temp += (heat_gen - heat_dissipation) * self.dt

        # Sensor measurement noise
        noise_p = random.gauss(0, 0.4)
        noise_s = random.gauss(0, 0.8)
        noise_l = random.gauss(0, 1.2)
        noise_t = random.gauss(0, 0.3)

        measurements = {
            "strut_pressure_bar": (p_gas_pa / 1e5) + noise_p,
            "strut_displacement_mm": (self.stroke * 1000.0) + noise_s,
            "reaction_load_kn": max(0.0, F_total_kn + noise_l),
            "strut_temperature_c": self.strut_temp + noise_t,
        }

        return TelemetryFrame(
            timestamp_s=round(self.current_time, 4),
            asset_id=self.asset_id,
            asset_class="aircraft_landing_gear",
            measurements=measurements,
            operating_conditions={
                "sink_rate": sink_rate,
                "ambient_temp": amb_temp,
                "aircraft_weight_factor": weight_factor,
            },
            true_degradation=self.degradation,
            metadata={"cycle": self.cycle_count},
        )

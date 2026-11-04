"""
Physics simulation of a UAV Brushless DC (BLDC) Electric Propulsion Motor.

Models electromechanical torque generation, aerodynamic propeller drag torque,
phase winding Joule heating, convective airflow cooling, and bearing friction degradation.
"""

import math
import random
from typing import Dict, Any
from phi_fleet.simulation.base import BaseAssetSimulator, TelemetryFrame


class UAVElectricMotorSimulator(BaseAssetSimulator):
    def __init__(self, asset_id: str, sampling_dt: float = 0.02):
        super().__init__(asset_id, sampling_dt)
        # Nominal BLDC Motor parameters
        self.Kv = 920.0                 # RPM per Volt
        self.Rm_nominal = 0.045         # Phase winding resistance (Ohms)
        self.Kt = 60.0 / (2.0 * math.pi * self.Kv)  # Torque constant (N*m/A)
        self.Ke = self.Kt               # Back-EMF constant (V/(rad/s))
        self.J_rotor = 0.00045          # Rotor + prop inertia (kg*m^2)
        self.B_viscous = 0.00008        # Nominal bearing viscous friction
        self.C_thermal = 35.0           # Thermal capacitance (J/K)
        self.R_thermal = 1.45           # Thermal resistance to cooling air (K/W)

        self.reset()

    def reset(self, initial_degradation: float = 0.0) -> None:
        self.current_time = 0.0
        self.degradation = initial_degradation
        # Pre-initialize to steady cruise state (throttle ~68%, ~6200 RPM)
        nominal_rpm = 6200.0
        self.omega_rad_s = nominal_rpm * (2.0 * math.pi / 60.0)
        self.motor_temp = 42.0 + 25.0 * initial_degradation
        self.current_a = 14.5 + 8.0 * initial_degradation


    def step(self, operating_conditions: Dict[str, float]) -> TelemetryFrame:
        """
        Advance one simulation step.
        Operating conditions:
          - 'throttle_pct': 0% to 100%
          - 'airspeed_m_s': UAV forward velocity (0 to 35 m/s)
          - 'ambient_temp': Outdoor ambient temperature (°C)
          - 'air_density': Air density kg/m^3 (default 1.225)
        """
        self.current_time += self.dt
        throttle = operating_conditions.get("throttle_pct", 65.0)
        airspeed = operating_conditions.get("airspeed_m_s", 16.0)
        amb_temp = operating_conditions.get("ambient_temp", 24.0)
        rho_air = operating_conditions.get("air_density", 1.225)

        # Physical Degradation Dynamics:
        # 1. Thermal aging of magnet wire & inter-turn micro-shorts increase phase resistance
        # 2. Raceway spalling / bearing damage increases friction torque
        Rm_effective = self.Rm_nominal * (1.0 + 0.85 * self.degradation)
        B_effective = self.B_viscous * (1.0 + 3.0 * (self.degradation ** 2))

        # Applied Voltage from ESC (assumed 6S LiPo nominal bus ~22.2V)
        V_bus = 22.2
        V_applied = (throttle / 100.0) * V_bus

        # Aerodynamic Propeller Load Torque (tau_aero = Cp * rho * n^2 * D^5)
        # Simplified: tau_aero proportional to omega^2 and forward advance ratio
        D_prop = 0.28  # 11 inch propeller (m)
        rpm = self.omega_rad_s * (60.0 / (2.0 * math.pi))
        n_rev_s = rpm / 60.0
        # Aerodynamic load torque (Nm)
        tau_aero = 0.038 * rho_air * (max(0.0, n_rev_s) ** 2) * (D_prop ** 5)
        # Advance ratio reduction on torque
        if airspeed > 0 and n_rev_s > 0:
            J_advance = airspeed / (n_rev_s * D_prop)
            tau_aero = max(0.001, tau_aero * (1.0 - 0.4 * min(1.5, J_advance)))

        # Electromechanical state equations
        # Back-EMF: V_emf = Ke * omega
        V_emf = self.Ke * self.omega_rad_s
        I_ideal = max(0.0, (V_applied - V_emf) / Rm_effective)
        self.current_a = I_ideal

        # Torque equation: J * domega/dt = Kt * I - B * omega - tau_aero
        tau_elec = self.Kt * self.current_a
        tau_net = tau_elec - (B_effective * self.omega_rad_s) - tau_aero
        d_omega = (tau_net / self.J_rotor) * self.dt
        self.omega_rad_s = max(0.0, self.omega_rad_s + d_omega)

        # Thermal dynamics: Joule heating (I^2 * R) minus forced convection cooling
        # Airflow velocity enhances convective cooling
        cooling_factor = 1.0 + 0.05 * airspeed
        R_th_effective = self.R_thermal / cooling_factor
        P_joule = (self.current_a ** 2) * Rm_effective
        heat_loss = (self.motor_temp - amb_temp) / R_th_effective
        self.motor_temp += ((P_joule - heat_loss) / self.C_thermal) * self.dt

        # Bearing Vibration (m/s^2 RMS)
        # Baseline rotor vibration + bearing degradation harmonics
        base_vib = 1.8 + 0.0006 * rpm
        vib_deg = 8.5 * (self.degradation ** 2)
        vibration_rms = base_vib + vib_deg

        # Measurement noise
        measurements = {
            "motor_rpm": (self.omega_rad_s * 60.0 / (2.0 * math.pi)) + random.gauss(0, 15.0),
            "phase_current_a": self.current_a + random.gauss(0, 0.25),
            "winding_temp_c": self.motor_temp + random.gauss(0, 0.4),
            "bearing_vibration_ms2": vibration_rms + random.gauss(0, 0.18),
        }

        return TelemetryFrame(
            timestamp_s=round(self.current_time, 4),
            asset_id=self.asset_id,
            asset_class="uav_electric_motor",
            measurements=measurements,
            operating_conditions={
                "throttle_pct": throttle,
                "airspeed_m_s": airspeed,
                "ambient_temp": amb_temp,
                "air_density": rho_air,
            },
            true_degradation=self.degradation,
            metadata={"rpm": measurements["motor_rpm"]},
        )

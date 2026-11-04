"""
Physics simulation of an Aircraft Turbofan Engine Subsystem.

Models core thermodynamic energy balance, compressor/turbine isentropic efficiencies,
Exhaust Gas Temperature (EGT) margin decay, and high-pressure rotor shaft vibration.
"""

import math
import random
from typing import Dict, Any
from phi_fleet.simulation.base import BaseAssetSimulator, TelemetryFrame


class TurbofanEngineSimulator(BaseAssetSimulator):
    def __init__(self, asset_id: str, sampling_dt: float = 0.05):
        super().__init__(asset_id, sampling_dt)
        # Nominal baseline parameters
        self.nominal_egt_base = 620.0       # Base cruise EGT (°C)
        self.nominal_vib_base = 1.15        # Base RMS vibration (mm/s)
        self.nominal_efficiency = 0.89     # Nominal isentropic efficiency
        self.operating_cycles = 120

        self.reset()

    def reset(self, initial_degradation: float = 0.0) -> None:
        self.current_time = 0.0
        self.degradation = initial_degradation
        # Pre-initialize to nominal cruise equilibrium
        amb_temp = -48.0
        throttle = 82.0
        eff = self.nominal_efficiency - 0.08 * initial_degradation
        self.egt_state = amb_temp + 580.0 * (throttle / 100.0) + (1.0 - eff) * 950.0
        base_vib = 0.8 + 1.2 * (throttle / 100.0) ** 2
        self.vibration_state = base_vib + 3.5 * (initial_degradation ** 1.5)


    def step(self, operating_conditions: Dict[str, float]) -> TelemetryFrame:
        """
        Advance one simulation step.
        Operating conditions:
          - 'throttle_pct': Core power command (40% to 100%)
          - 'altitude_m': Flight altitude in meters (0 to 11000m)
          - 'ambient_temp': Static air temperature (°C)
        """
        self.current_time += self.dt
        throttle = operating_conditions.get("throttle_pct", 85.0)
        altitude = operating_conditions.get("altitude_m", 9500.0)
        amb_temp = operating_conditions.get("ambient_temp", -45.0)

        # Standard atmospheric temperature lapse & pressure ratio approximation
        theta_amb = (amb_temp + 273.15) / 288.15
        delta_p = math.exp(-altitude / 7400.0)

        # Physical Degradation Dynamics:
        # Blade erosion and compressor tip rub decrease thermal efficiency by up to 8%
        # Bearing wear and unbalance increase rotor shaft vibration amplitude by up to 280%
        eta_loss = 0.08 * self.degradation
        eff_actual = self.nominal_efficiency - eta_loss

        # Fuel Flow required to meet demanded thrust (kg/s)
        # As efficiency drops, fuel flow must rise non-linearly:
        Wf_nominal = 0.45 * (throttle / 100.0) ** 1.8 * delta_p
        Wf_actual = Wf_nominal * (self.nominal_efficiency / eff_actual)

        # Exhaust Gas Temperature (EGT) thermodynamic model:
        # T_egt proportional to fuel-air ratio and compressor exit temperature
        egt_theoretical = (
            amb_temp + 580.0 * (throttle / 100.0) + (1.0 - eff_actual) * 950.0
        )
        # Thermal inertia lag (first-order low-pass)
        tau_thermal = 3.0
        self.egt_state += (egt_theoretical - self.egt_state) * (self.dt / tau_thermal)

        # High-Pressure Rotor Vibration (mm/s RMS)
        # Dependent on core rotational speed (throttle) + bearing wear degradation
        base_vib = 0.8 + 1.2 * (throttle / 100.0) ** 2
        degradation_vib_boost = 3.5 * (self.degradation ** 1.5)
        self.vibration_state = base_vib + degradation_vib_boost

        # Add stochastic sensor noise
        egt_noise = random.gauss(0, 1.8)
        vib_noise = random.gauss(0, 0.08)
        wf_noise = random.gauss(0, 0.015)

        measurements = {
            "egt_celsius": self.egt_state + egt_noise,
            "core_vibration_mms": max(0.2, self.vibration_state + vib_noise),
            "fuel_flow_kg_s": max(0.05, Wf_actual + wf_noise),
            "operating_cycles": float(self.operating_cycles),
        }

        return TelemetryFrame(
            timestamp_s=round(self.current_time, 4),
            asset_id=self.asset_id,
            asset_class="aircraft_turbofan",
            measurements=measurements,
            operating_conditions={
                "throttle_pct": throttle,
                "altitude_m": altitude,
                "ambient_temp": amb_temp,
            },
            true_degradation=self.degradation,
            metadata={"operating_cycles": self.operating_cycles},
        )

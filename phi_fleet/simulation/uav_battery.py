"""
Physics simulation of a UAV Lithium-Ion Polymer Battery Pack.

Implements a Thevenin equivalent circuit model (ECM), non-linear Open Circuit Voltage (OCV),
charge transfer polarization, irreversible & entropic heat generation, and capacity fade.
"""

import math
import random
from typing import Dict, Any
from phi_fleet.simulation.base import BaseAssetSimulator, TelemetryFrame


class UAVBatterySimulator(BaseAssetSimulator):
    def __init__(self, asset_id: str, sampling_dt: float = 0.05):
        super().__init__(asset_id, sampling_dt)
        # Nominal 6S LiPo pack specs (22.2V nominal, 6000 mAh)
        self.Q_max_nominal_ah = 6.0      # 6.0 Ah
        self.R0_nominal = 0.018          # Ohmic series resistance (Ohms)
        self.R1_nominal = 0.012          # Polarization resistance (Ohms)
        self.C1 = 1200.0                 # Polarization capacitance (Farads)
        self.C_thermal = 280.0           # Thermal capacity (J/K)
        self.R_thermal = 3.2             # Convective resistance (K/W)

        self.reset()

    def reset(self, initial_degradation: float = 0.0) -> None:
        self.current_time = 0.0
        self.degradation = initial_degradation
        self.soc = 0.98                  # State of Charge (1.0 = 100%)
        self.V_polarization = 0.0        # Polarization capacitor voltage
        self.pack_temp = 25.0            # (°C)


    def _open_circuit_voltage(self, soc: float) -> float:
        """Empirical OCV(SOC) curve for 6S LiPo pack."""
        # 6 cells in series; per-cell curve: 3.2V (empty) to 4.2V (full)
        cell_ocv = 3.42 + 0.55 * soc + 0.18 * (soc ** 3) + 0.05 * math.log(max(0.005, soc))
        return 6.0 * max(3.0, min(4.25, cell_ocv))

    def step(self, operating_conditions: Dict[str, float]) -> TelemetryFrame:
        """
        Advance one simulation step.
        Operating conditions:
          - 'current_demand_a': discharge current in Amperes (0 to 60A)
          - 'ambient_temp': outdoor ambient temperature (°C)
        """
        self.current_time += self.dt
        I_load = operating_conditions.get("current_demand_a", 18.5)
        amb_temp = operating_conditions.get("ambient_temp", 22.0)

        # Degradation Dynamics:
        # 1. SEI Layer thickening and lithium plating increase R0 up to 2.4x
        # 2. Loss of active lithium material fades capacity Q_max down by up to 35%
        R0_effective = self.R0_nominal * (1.0 + 1.4 * self.degradation)
        R1_effective = self.R1_nominal * (1.0 + 0.9 * self.degradation)
        Q_max_effective = self.Q_max_nominal_ah * (1.0 - 0.35 * self.degradation)

        # Update Polarization RC circuit: dVp/dt = -Vp/(R1*C1) + I/C1
        tau_rc = R1_effective * self.C1
        dVp = (-self.V_polarization / tau_rc + (I_load / self.C1)) * self.dt
        self.V_polarization += dVp

        # Terminal Voltage: V_term = Voc - I * R0 - V_pol
        Voc = self._open_circuit_voltage(self.soc)
        V_term = Voc - (I_load * R0_effective) - self.V_polarization

        # Coulomb counting SOC update
        d_soc = -(I_load * self.dt) / (Q_max_effective * 3600.0)
        self.soc = max(0.01, min(1.0, self.soc + d_soc))

        # Thermal generation: Joule heat (I^2 * R0 + Vp^2 / R1) + entropic reaction heat
        P_joule = (I_load ** 2) * R0_effective + (self.V_polarization ** 2) / max(0.001, R1_effective)
        P_dissipation = (self.pack_temp - amb_temp) / self.R_thermal
        self.pack_temp += ((P_joule - P_dissipation) / self.C_thermal) * self.dt

        # Sensor noise
        v_noise = random.gauss(0, 0.04)
        i_noise = random.gauss(0, 0.15)
        t_noise = random.gauss(0, 0.25)

        measurements = {
            "terminal_voltage_v": max(17.5, V_term + v_noise),
            "discharge_current_a": max(0.0, I_load + i_noise),
            "pack_temperature_c": self.pack_temp + t_noise,
            "remaining_capacity_ah": (self.soc * Q_max_effective) + random.gauss(0, 0.02),
        }

        return TelemetryFrame(
            timestamp_s=round(self.current_time, 4),
            asset_id=self.asset_id,
            asset_class="uav_battery",
            measurements=measurements,
            operating_conditions={
                "current_demand_a": I_load,
                "ambient_temp": amb_temp,
            },
            true_degradation=self.degradation,
            metadata={"soc": self.soc, "q_max_effective": Q_max_effective},
        )

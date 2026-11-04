"""
Multi-Asset Fleet Simulation Orchestrator.

Manages synchronized telemetry streaming across heterogeneous aerospace platforms:
3 Commercial Transport Aircraft (Landing Gear + Turbofan) and civilian UAV squadrons
(Electric Propulsion Motors + Li-Ion Battery Packs).
"""

from typing import Dict, List, Any
from phi_fleet.simulation.base import BaseAssetSimulator, TelemetryFrame
from phi_fleet.simulation.landing_gear import LandingGearSimulator
from phi_fleet.simulation.turbofan import TurbofanEngineSimulator
from phi_fleet.simulation.uav_motor import UAVElectricMotorSimulator
from phi_fleet.simulation.uav_battery import UAVBatterySimulator


class FleetSimulationOrchestrator:
    """
    Coordinates multi-asset simulation environment for fleet-level telemetry replay.
    """

    def __init__(self):
        self.simulators: Dict[str, BaseAssetSimulator] = {}
        self._init_default_fleet()

    def _init_default_fleet(self):
        # 1. Commercial Aircraft Fleet
        # Aircraft 1 (SkyLink-701): Landing Gear with slight nitrogen seal leakage (deg=0.35)
        lg_1 = LandingGearSimulator("AIRCRAFT-701-LG")
        lg_1.reset(initial_degradation=0.35)
        self.simulators["AIRCRAFT-701-LG"] = lg_1

        # Aircraft 1 (SkyLink-701): Turbofan engine healthy (deg=0.05)
        eng_1 = TurbofanEngineSimulator("AIRCRAFT-701-ENG")
        eng_1.reset(initial_degradation=0.05)
        self.simulators["AIRCRAFT-701-ENG"] = eng_1

        # Aircraft 2 (SkyLink-702): Turbofan engine with blade creep & erosion (deg=0.55)
        eng_2 = TurbofanEngineSimulator("AIRCRAFT-702-ENG")
        eng_2.reset(initial_degradation=0.55)
        self.simulators["AIRCRAFT-702-ENG"] = eng_2

        # Aircraft 3 (SkyLink-703): Baseline healthy landing gear
        lg_3 = LandingGearSimulator("AIRCRAFT-703-LG")
        lg_3.reset(initial_degradation=0.02)
        self.simulators["AIRCRAFT-703-LG"] = lg_3

        # 2. UAV Fleet (Civilian / Inspection UAS)
        # UAV-Alpha (AeroViper-01): Motor with inter-turn insulation degradation (deg=0.48)
        uav_m1 = UAVElectricMotorSimulator("UAV-ALPHA-MOTOR")
        uav_m1.reset(initial_degradation=0.48)
        self.simulators["UAV-ALPHA-MOTOR"] = uav_m1

        # UAV-Alpha (AeroViper-01): Healthy battery pack (deg=0.08)
        uav_b1 = UAVBatterySimulator("UAV-ALPHA-BATT")
        uav_b1.reset(initial_degradation=0.08)
        self.simulators["UAV-ALPHA-BATT"] = uav_b1

        # UAV-Beta (AeroViper-02): Operating in cold alpine regime, high battery degradation (deg=0.62)
        uav_b2 = UAVBatterySimulator("UAV-BETA-BATT")
        uav_b2.reset(initial_degradation=0.62)
        self.simulators["UAV-BETA-BATT"] = uav_b2

        # UAV-Gamma (AeroViper-03): High ambient heat desert patrol, motor bearing wear (deg=0.38)
        uav_m3 = UAVElectricMotorSimulator("UAV-GAMMA-MOTOR")
        uav_m3.reset(initial_degradation=0.38)
        self.simulators["UAV-GAMMA-MOTOR"] = uav_m3

    def step_fleet(self, conditions_map: Dict[str, Dict[str, float]]) -> Dict[str, TelemetryFrame]:
        """
        Advance all asset simulations by one time step with respective operating environments.
        """
        fleet_frames: Dict[str, TelemetryFrame] = {}

        for asset_id, sim in self.simulators.items():
            # Get asset-specific operating condition or fall back to default
            cond = conditions_map.get(asset_id, {})
            # Contextual defaults if not provided
            if sim.__class__.__name__ == "LandingGearSimulator" and "sink_rate" not in cond:
                cond.update({"sink_rate": 2.1, "ambient_temp": 18.0, "aircraft_weight_factor": 1.05})
            elif sim.__class__.__name__ == "TurbofanEngineSimulator" and "throttle_pct" not in cond:
                cond.update({"throttle_pct": 82.0, "altitude_m": 10200.0, "ambient_temp": -48.0})
            elif sim.__class__.__name__ == "UAVElectricMotorSimulator" and "throttle_pct" not in cond:
                cond.update({"throttle_pct": 68.0, "airspeed_m_s": 18.0, "ambient_temp": 25.0, "air_density": 1.21})
            elif sim.__class__.__name__ == "UAVBatterySimulator" and "current_demand_a" not in cond:
                cond.update({"current_demand_a": 20.0, "ambient_temp": 25.0})

            frame = sim.step(cond)
            fleet_frames[asset_id] = frame

        return fleet_frames

    def get_asset_classes(self) -> Dict[str, str]:
        return {
            asset_id: sim.__class__.__name__
            for asset_id, sim in self.simulators.items()
        }

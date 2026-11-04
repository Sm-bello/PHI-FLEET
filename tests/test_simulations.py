"""
Unit tests for aerospace asset physics simulators.
"""

import pytest
from phi_fleet.simulation.landing_gear import LandingGearSimulator
from phi_fleet.simulation.turbofan import TurbofanEngineSimulator
from phi_fleet.simulation.uav_motor import UAVElectricMotorSimulator
from phi_fleet.simulation.uav_battery import UAVBatterySimulator
from phi_fleet.simulation.fleet_generator import FleetSimulationOrchestrator


def test_landing_gear_simulation():
    sim = LandingGearSimulator("TEST-LG")
    frame = sim.step({"sink_rate": 2.2, "ambient_temp": 20.0, "aircraft_weight_factor": 1.0})
    assert frame.asset_id == "TEST-LG"
    assert frame.asset_class == "aircraft_landing_gear"
    assert "strut_pressure_bar" in frame.measurements
    assert "strut_displacement_mm" in frame.measurements
    assert frame.measurements["strut_pressure_bar"] > 30.0


def test_turbofan_simulation():
    sim = TurbofanEngineSimulator("TEST-ENG")
    frame = sim.step({"throttle_pct": 85.0, "altitude_m": 10000.0, "ambient_temp": -50.0})
    assert frame.asset_id == "TEST-ENG"
    assert frame.asset_class == "aircraft_turbofan"
    assert "egt_celsius" in frame.measurements
    assert frame.measurements["egt_celsius"] > 400.0


def test_uav_motor_simulation():
    sim = UAVElectricMotorSimulator("TEST-MOTOR")
    frame = sim.step({"throttle_pct": 70.0, "airspeed_m_s": 18.0, "ambient_temp": 22.0})
    assert frame.asset_id == "TEST-MOTOR"
    assert frame.asset_class == "uav_electric_motor"
    assert "motor_rpm" in frame.measurements
    assert frame.measurements["motor_rpm"] > 2000.0


def test_uav_battery_simulation():
    sim = UAVBatterySimulator("TEST-BATT")
    frame = sim.step({"current_demand_a": 20.0, "ambient_temp": 22.0})
    assert frame.asset_id == "TEST-BATT"
    assert frame.asset_class == "uav_battery"
    assert "terminal_voltage_v" in frame.measurements
    assert frame.measurements["terminal_voltage_v"] > 18.0


def test_fleet_orchestrator():
    orch = FleetSimulationOrchestrator()
    frames = orch.step_fleet({})
    assert len(frames) == 8
    assert "AIRCRAFT-701-LG" in frames
    assert "UAV-ALPHA-MOTOR" in frames

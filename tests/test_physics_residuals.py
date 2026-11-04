"""
Unit tests for the physics residual engine and evidential uncertainty.
"""

from phi_fleet.simulation.landing_gear import LandingGearSimulator
from phi_fleet.simulation.turbofan import TurbofanEngineSimulator
from phi_fleet.twin.residual_engine import PhysicsResidualEngine
from phi_fleet.twin.uncertainty import EvidentialDisentanglementEngine
from phi_fleet.config import HealthStatus


def test_turbofan_residual_healthy_vs_degraded():
    res_eng = PhysicsResidualEngine()
    unc_eng = EvidentialDisentanglementEngine()

    # Healthy engine
    sim_healthy = TurbofanEngineSimulator("ENG-HEALTHY")
    sim_healthy.reset(initial_degradation=0.02)
    for _ in range(15):
        frame_h = sim_healthy.step({"throttle_pct": 82.0, "altitude_m": 10200.0, "ambient_temp": -48.0})
    res_h = res_eng.compute_residuals(frame_h)
    unc_h = unc_eng.evaluate(frame_h.asset_class, frame_h.operating_conditions, res_h["normalized_residuals"], res_h["composite_divergence"])

    assert res_h["composite_divergence"] < 2.0
    assert unc_h["health_status"] == HealthStatus.NOMINAL

    # Degraded engine
    sim_degraded = TurbofanEngineSimulator("ENG-DEGRADED")
    sim_degraded.reset(initial_degradation=0.60)
    for _ in range(15):
        frame_d = sim_degraded.step({"throttle_pct": 82.0, "altitude_m": 10200.0, "ambient_temp": -48.0})
    res_d = res_eng.compute_residuals(frame_d)
    unc_d = unc_eng.evaluate(frame_d.asset_class, frame_d.operating_conditions, res_d["normalized_residuals"], res_d["composite_divergence"])

    assert res_d["composite_divergence"] > 3.0
    assert unc_d["health_status"] in (HealthStatus.DEGRADED, HealthStatus.CRITICAL)


def test_epistemic_uncertainty_ood():
    unc_eng = EvidentialDisentanglementEngine(epistemic_threshold=0.30)
    # Severe out-of-distribution altitude (16,000m, beyond commercial envelope 11,500m)
    res_mock = {"egt_celsius": 1.0, "core_vibration_mms": 0.5}
    unc = unc_eng.evaluate(
        "aircraft_turbofan",
        {"altitude_m": 17500.0, "throttle_pct": 85.0, "ambient_temp": -50.0},
        res_mock,
        composite_divergence=1.5,
    )
    assert unc["epistemic_uncertainty"] > 0.30
    assert unc["health_status"] == HealthStatus.UNKNOWN_OOD

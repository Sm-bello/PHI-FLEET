"""
Unit tests for prognostics, conformal RUL intervals, and decision support.
"""

from phi_fleet.prognostics.health_index import HealthIndexCalculator
from phi_fleet.prognostics.rul_estimator import ConformalRULPredictor
from phi_fleet.prognostics.diagnostics import DiagnosticEvidenceEngine
from phi_fleet.prognostics.decision_support import DecisionSupportEngine


def test_conformal_rul_bounds():
    predictor = ConformalRULPredictor(confidence_level=0.90)
    rul = predictor.predict_rul(
        asset_id="TEST-ENG",
        asset_class="aircraft_turbofan",
        health_index_pct=85.0,
        epistemic_uncertainty=0.05,
        aleatoric_uncertainty=0.10,
        global_degradation_rate=0.03,
    )

    assert rul.lower_bound_rul_hours < rul.median_rul_hours < rul.upper_bound_rul_hours
    assert rul.lower_bound_rul_hours > 0.0


def test_diagnostic_and_maintenance_directive():
    raw_res = {"strut_pressure_bar": -7.5, "reaction_load_kn": -5.0, "strut_temperature_c": 1.2}
    norm_res = {"strut_pressure_bar": -6.25, "reaction_load_kn": -0.11, "strut_temperature_c": 0.48}

    ev = DiagnosticEvidenceEngine.generate_evidence(
        "AIRCRAFT-701-LG",
        "aircraft_landing_gear",
        raw_res,
        norm_res,
        estimated_degradation=0.45,
    )

    assert "Nitrogen" in ev.primary_failure_mode or "Leakage" in ev.primary_failure_mode
    assert ev.severity_level in ("WARNING", "CRITICAL")

    predictor = ConformalRULPredictor()
    rul = predictor.predict_rul("AIRCRAFT-701-LG", "aircraft_landing_gear", 55.0, 0.05, 0.08, 0.03)
    rec = DecisionSupportEngine.generate_recommendation(rul, ev)

    assert rec.dispatch_status in ("DISPATCH_WITH_LIMITATION", "GROUNDED")
    assert "ATA-32" in rec.work_order_code

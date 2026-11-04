"""
Physics Residual Engine.

Computes the physics residual vector r(t) = y_obs(t) - y_phys(t) between observed telemetry
and the first-principles digital twin baseline, followed by normalized statistical scaling.
"""

import math
from typing import Dict, Any, Tuple
from phi_fleet.simulation.base import TelemetryFrame
from phi_fleet.twin.physics_estimator import PhysicsEstimator


class PhysicsResidualEngine:
    def __init__(self):
        self.estimator = PhysicsEstimator()

        # Nominal sensor standard deviations (used for Z-score normalization)
        self.nominal_sigmas: Dict[str, Dict[str, float]] = {
            "aircraft_landing_gear": {
                "strut_pressure_bar": 1.2,
                "reaction_load_kn": 45.0,  # dynamic touchdown impact variations
                "strut_temperature_c": 2.5,
            },
            "aircraft_turbofan": {
                "egt_celsius": 5.0,
                "core_vibration_mms": 0.20,
                "fuel_flow_kg_s": 0.03,
            },
            "uav_electric_motor": {
                "motor_rpm": 80.0,
                "phase_current_a": 1.2,
                "winding_temp_c": 2.5,
                "bearing_vibration_ms2": 0.40,
            },
            "uav_battery": {
                "terminal_voltage_v": 0.25,
                "pack_temperature_c": 1.5,
            },
        }

    def compute_residuals(self, frame: TelemetryFrame) -> Dict[str, Any]:
        """
        Computes raw and normalized residuals:
        r_i = y_obs,i - y_phys,i
        z_i = r_i / sigma_nom,i
        """
        predicted = self.estimator.predict(
            frame.asset_class,
            frame.operating_conditions,
            frame.measurements,
        )

        sigmas = self.nominal_sigmas.get(frame.asset_class, {})
        raw_residuals: Dict[str, float] = {}
        normalized_residuals: Dict[str, float] = {}
        squared_divergence = 0.0
        n_channels = 0

        for key, pred_val in predicted.items():
            if key in frame.measurements:
                obs_val = frame.measurements[key]
                diff = obs_val - pred_val
                raw_residuals[key] = diff

                sigma = sigmas.get(key, 1.0)
                z = diff / max(1e-5, sigma)
                normalized_residuals[key] = z

                squared_divergence += z ** 2
                n_channels += 1

        # Mahalanobis-like composite residual divergence metric
        composite_divergence = math.sqrt(squared_divergence / max(1, n_channels))

        # Check statistical significance (e.g., > 2.0 sigma)
        is_statistically_significant = composite_divergence > 2.0

        return {
            "asset_id": frame.asset_id,
            "asset_class": frame.asset_class,
            "timestamp_s": frame.timestamp_s,
            "raw_residuals": raw_residuals,
            "normalized_residuals": normalized_residuals,
            "composite_divergence": composite_divergence,
            "is_statistically_significant": is_statistically_significant,
            "predicted_nominal": predicted,
        }

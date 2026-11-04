"""
Heterogeneous Invariant Degradation Representation Manifold.

Projects asset-specific physics residuals (e.g., landing gear pressure loss,
turbofan EGT margin decay, BLDC motor phase resistance rise, battery impedance growth)
into a shared 4-dimensional physical invariant degradation manifold:
  z = [z_thermal_stress, z_mechanical_wear, z_energy_dissipation, z_fatigue_rate]

Enables cross-platform federated transfer without assuming identical component physics.
"""

import math
from typing import Dict, List, Tuple
import numpy as np


class InvariantDegradationProjector:
    """
    Asset-to-Invariant latent manifold mapper and federated degradation predictor.
    """

    def __init__(self, latent_dim: int = 4):
        self.latent_dim = latent_dim

        # Asset-specific projection weights W_class : (latent_dim x num_features)
        # Pre-aligned to physical dimensions: [thermal, mechanical, energy, cyclic fatigue]
        self.channel_mappings = {
            "aircraft_landing_gear": [
                "strut_temperature_c",
                "reaction_load_kn",
                "strut_pressure_bar",
            ],
            "aircraft_turbofan": [
                "egt_celsius",
                "core_vibration_mms",
                "fuel_flow_kg_s",
            ],
            "uav_electric_motor": [
                "winding_temp_c",
                "bearing_vibration_ms2",
                "phase_current_a",
            ],
            "uav_battery": [
                "pack_temperature_c",
                "discharge_current_a",
                "terminal_voltage_v",
            ],
        }

    def project_to_latent(self, asset_class: str, normalized_residuals: Dict[str, float]) -> np.ndarray:
        """
        Projects normalized physics residuals into the universal invariant latent vector z.
        """
        channels = self.channel_mappings.get(asset_class, [])
        r_vec = np.array([abs(normalized_residuals.get(ch, 0.0)) for ch in channels], dtype=np.float64)

        if len(r_vec) < 3:
            r_vec = np.pad(r_vec, (0, 3 - len(r_vec)), "constant")

        # Invariant coordinates:
        # z_0: thermal stress manifestation
        z_thermal = r_vec[0]
        # z_1: mechanical / kinematic disturbance
        z_mechanical = r_vec[1]
        # z_2: energetic dissipation / impedance anomaly
        z_energy = r_vec[2]
        # z_3: composite cross-stress product (thermo-mechanical interaction)
        z_fatigue = math.sqrt(z_thermal * z_mechanical + z_energy ** 2)

        z = np.array([z_thermal, z_mechanical, z_energy, z_fatigue], dtype=np.float64)
        return z

    @staticmethod
    def physics_loss(predicted_rate: float, true_observed_rate: float) -> float:
        """
        Physics-informed loss enforcing non-negativity of degradation progression
        (2nd law of thermodynamics / damage irreversibility: dD/dt >= 0).
        """
        mse = (predicted_rate - true_observed_rate) ** 2
        # Severe penalty if predicted degradation rate violates monotonicity
        monotonicity_penalty = 100.0 * max(0.0, -predicted_rate) ** 2
        return float(mse + monotonicity_penalty)

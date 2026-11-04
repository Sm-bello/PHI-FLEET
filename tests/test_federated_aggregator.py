"""
Unit tests for federated learning aggregator (FedPhys) and invariant projection.
"""

import numpy as np
from phi_fleet.federated.protocol import ClientModelUpdate
from phi_fleet.federated.server_aggregator import FleetFederatedServer
from phi_fleet.federated.invariant_space import InvariantDegradationProjector


def test_invariant_space_projection():
    projector = InvariantDegradationProjector(latent_dim=4)
    residuals = {"strut_pressure_bar": -4.2, "reaction_load_kn": 1.5, "strut_temperature_c": 3.0}
    z = projector.project_to_latent("aircraft_landing_gear", residuals)
    assert len(z) == 4
    assert all(zi >= 0 for zi in z)


def test_fedphys_aggregation_downweights_high_epistemic_client():
    server = FleetFederatedServer(latent_dim=4, lambda_physics=2.0)

    # Client A: low epistemic uncertainty, low physics loss
    upd_a = ClientModelUpdate(
        client_id="CLIENT-A",
        asset_class="aircraft_turbofan",
        num_samples=50,
        epistemic_uncertainty=0.05,
        physics_loss=0.02,
        weight_vector=[0.1, 0.1, 0.1, 0.1],
        bias_scalar=0.01,
    )

    # Client B: extreme epistemic uncertainty (OOD)
    upd_b = ClientModelUpdate(
        client_id="CLIENT-B",
        asset_class="uav_battery",
        num_samples=50,
        epistemic_uncertainty=0.95,
        physics_loss=0.02,
        weight_vector=[0.9, 0.9, 0.9, 0.9],
        bias_scalar=0.05,
    )

    result = server.aggregate([upd_a, upd_b])
    assert result.round_number == 1
    # Client A must have drastically higher weight than Client B
    assert result.aggregation_weights["CLIENT-A"] > 0.85
    assert result.aggregation_weights["CLIENT-B"] < 0.15

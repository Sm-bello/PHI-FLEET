"""
Fleet Federated Server Aggregator (FedPhys).

Coordinates uncertainty-weighted and physics-consistency-constrained model aggregation
across heterogeneous aircraft and UAV digital twins.
"""

import math
from typing import List, Dict, Any
import numpy as np
from phi_fleet.federated.protocol import ClientModelUpdate, GlobalModelParameters


class FleetFederatedServer:
    """
    Central Fleet Intelligence Aggregator.
    Implements FedPhys: aggregates model weights proportional to physics consistency
    and inversely proportional to epistemic uncertainty.
    """

    def __init__(self, latent_dim: int = 4, lambda_physics: float = 2.0):
        self.latent_dim = latent_dim
        self.lambda_physics = lambda_physics
        self.round_number = 0

        # Global consensus parameters on invariant manifold
        self.global_weights = np.array([0.05, 0.08, 0.04, 0.12], dtype=np.float64)
        self.global_bias = 0.01
        self.history: List[GlobalModelParameters] = []

    def aggregate(self, client_updates: List[ClientModelUpdate]) -> GlobalModelParameters:
        """
        FedPhys Aggregation:
        w_k proportional to N_k * (1 - u_epistemic_k) * exp(-lambda * L_phys_k)
        """
        self.round_number += 1

        if not client_updates:
            param = GlobalModelParameters(
                round_number=self.round_number,
                global_weights=self.global_weights.tolist(),
                global_bias=float(self.global_bias),
                fleet_consensus_loss=0.0,
                contributing_clients=[],
                aggregation_weights={},
            )
            self.history.append(param)
            return param

        raw_scores = []
        for upd in client_updates:
            # Epistemic certainty multiplier
            certainty = max(0.01, 1.0 - upd.epistemic_uncertainty)
            # Physics consistency exponential factor
            phys_factor = math.exp(-self.lambda_physics * min(10.0, upd.physics_loss))
            # Sample size weighting
            sample_weight = math.sqrt(max(1, upd.num_samples))

            score = certainty * phys_factor * sample_weight
            raw_scores.append(score)

        total_score = sum(raw_scores)
        normalized_weights = [s / max(1e-6, total_score) for s in raw_scores]

        # Weighted parameter aggregation
        agg_w = np.zeros(self.latent_dim, dtype=np.float64)
        agg_b = 0.0
        total_loss = 0.0
        weights_dict: Dict[str, float] = {}

        for upd, alpha in zip(client_updates, normalized_weights):
            w_vec = np.array(upd.weight_vector, dtype=np.float64)
            agg_w += alpha * w_vec
            agg_b += alpha * upd.bias_scalar
            total_loss += alpha * upd.physics_loss
            weights_dict[upd.client_id] = round(alpha, 4)

        # Update global parameters
        self.global_weights = agg_w
        self.global_bias = agg_b

        result = GlobalModelParameters(
            round_number=self.round_number,
            global_weights=self.global_weights.tolist(),
            global_bias=float(self.global_bias),
            fleet_consensus_loss=float(total_loss),
            contributing_clients=[u.client_id for u in client_updates],
            aggregation_weights=weights_dict,
        )
        self.history.append(result)
        return result

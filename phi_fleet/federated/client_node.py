"""
Federated Client Node.

Runs locally on the aerospace asset or ground control station edge twin.
Processes local telemetry, projects residuals to invariant latent space,
trains local model under physics constraints, and returns uncertainty-stamped updates.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from phi_fleet.simulation.base import TelemetryFrame
from phi_fleet.twin.residual_engine import PhysicsResidualEngine
from phi_fleet.twin.uncertainty import EvidentialDisentanglementEngine
from phi_fleet.federated.invariant_space import InvariantDegradationProjector
from phi_fleet.federated.protocol import ClientModelUpdate


class FleetClientNode:
    """
    Edge digital twin client representing a single aerospace asset.
    """

    def __init__(self, asset_id: str, asset_class: str, latent_dim: int = 4):
        self.asset_id = asset_id
        self.asset_class = asset_class
        self.latent_dim = latent_dim

        self.residual_engine = PhysicsResidualEngine()
        self.evidential_engine = EvidentialDisentanglementEngine()
        self.projector = InvariantDegradationProjector(latent_dim)

        # Local model parameters for degradation rate predictor: y_hat = w . z + b
        self.weights = np.array([0.05, 0.08, 0.04, 0.12], dtype=np.float64)
        self.bias = 0.01

        # Local buffer of recent observations
        self.buffer_z: List[np.ndarray] = []
        self.buffer_rate: List[float] = []
        self.epistemic_history: List[float] = []

    def ingest_frame(self, frame: TelemetryFrame) -> Dict[str, Any]:
        """
        Processes a telemetry frame through residual calculation and evidential filtering.
        """
        # Step 1: Compute physics residuals
        res = self.residual_engine.compute_residuals(frame)

        # Step 2: Evidential uncertainty disentanglement
        unc = self.evidential_engine.evaluate(
            frame.asset_class,
            frame.operating_conditions,
            res["normalized_residuals"],
            res["composite_divergence"],
        )

        # Step 3: Project to invariant latent manifold
        z = self.projector.project_to_latent(frame.asset_class, res["normalized_residuals"])

        # Target degradation progression proxy
        deg_rate = unc["estimated_degradation"] * 0.05

        self.buffer_z.append(z)
        self.buffer_rate.append(deg_rate)
        self.epistemic_history.append(unc["epistemic_uncertainty"])

        # Keep buffer bounded
        if len(self.buffer_z) > 100:
            self.buffer_z.pop(0)
            self.buffer_rate.pop(0)
            self.epistemic_history.pop(0)

        return {
            "residual_info": res,
            "uncertainty_info": unc,
            "latent_z": z.tolist(),
        }

    def train_local_epoch(self, epochs: int = 3, lr: float = 0.01) -> ClientModelUpdate:
        """
        Performs local gradient steps on the invariant latent space using physics-regularized loss.
        """
        if not self.buffer_z:
            return ClientModelUpdate(
                client_id=self.asset_id,
                asset_class=self.asset_class,
                num_samples=0,
                epistemic_uncertainty=0.1,
                physics_loss=0.0,
                weight_vector=self.weights.tolist(),
                bias_scalar=float(self.bias),
            )

        Z = np.array(self.buffer_z)
        Y = np.array(self.buffer_rate)
        n = len(Y)

        total_physics_loss = 0.0

        for _ in range(epochs):
            # Predictions: y_hat = Z . w + b
            y_pred = Z @ self.weights + self.bias
            errors = y_pred - Y

            # Monotonicity gradient penalty: penalize if y_pred < 0
            mono_penalties = np.where(y_pred < 0, 100.0 * y_pred, 0.0)

            # Gradients
            grad_w = (Z.T @ (errors + mono_penalties)) / n
            grad_b = float(np.sum(errors + mono_penalties) / n)

            # Gradient descent step
            self.weights -= lr * grad_w
            self.bias -= lr * grad_b

            # Calculate epoch physics loss
            total_physics_loss = sum(
                self.projector.physics_loss(float(p), float(t))
                for p, t in zip(y_pred, Y)
            ) / max(1, n)

        mean_epistemic = float(np.mean(self.epistemic_history)) if self.epistemic_history else 0.05

        return ClientModelUpdate(
            client_id=self.asset_id,
            asset_class=self.asset_class,
            num_samples=n,
            epistemic_uncertainty=mean_epistemic,
            physics_loss=float(total_physics_loss),
            weight_vector=self.weights.tolist(),
            bias_scalar=float(self.bias),
            metadata={"mean_observed_rate": float(np.mean(Y))},
        )

    def update_parameters(self, global_weights: List[float], global_bias: float) -> None:
        """Receive aggregated federated parameters from fleet coordinator."""
        self.weights = np.array(global_weights, dtype=np.float64)
        self.bias = float(global_bias)

"""
PHI-FLEET: Physics-Hybrid Intelligence for Federated Aerospace Fleet Health.

A unified, physics-constrained digital twin framework hosting heterogeneous aerospace
asset twins across commercial transport aircraft, military platforms, and autonomous UAVs.

Author & Principal Architect: Mohammed Bello Sani (Sm-bello)
License: Apache-2.0
"""

__version__ = "0.1.0"
__author__ = "Mohammed Bello Sani"
__email__ = "bellosani2drescue@gmail.com"
__github__ = "https://github.com/Sm-bello/PHI-FLEET"

from phi_fleet.config import FleetConfig, AssetConfig
from phi_fleet.simulation.fleet_generator import FleetSimulationOrchestrator
from phi_fleet.twin.physics_estimator import PhysicsEstimator
from phi_fleet.twin.residual_engine import PhysicsResidualEngine
from phi_fleet.federated.server_aggregator import FleetFederatedServer
from phi_fleet.prognostics.rul_estimator import ConformalRULPredictor

__all__ = [
    "FleetConfig",
    "AssetConfig",
    "FleetSimulationOrchestrator",
    "PhysicsEstimator",
    "PhysicsResidualEngine",
    "FleetFederatedServer",
    "ConformalRULPredictor",
]

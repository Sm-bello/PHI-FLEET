"""
Federated learning and cross-platform intelligence module for PHI-FLEET.
"""

from phi_fleet.federated.protocol import ClientModelUpdate, GlobalModelParameters
from phi_fleet.federated.invariant_space import InvariantDegradationProjector
from phi_fleet.federated.client_node import FleetClientNode
from phi_fleet.federated.server_aggregator import FleetFederatedServer

__all__ = [
    "ClientModelUpdate",
    "GlobalModelParameters",
    "InvariantDegradationProjector",
    "FleetClientNode",
    "FleetFederatedServer",
]

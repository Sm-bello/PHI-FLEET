"""
Federated communication protocols and data exchange structures.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field


class ClientModelUpdate(BaseModel):
    client_id: str
    asset_class: str
    num_samples: int
    epistemic_uncertainty: float
    physics_loss: float
    weight_vector: List[float]
    bias_scalar: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GlobalModelParameters(BaseModel):
    round_number: int
    global_weights: List[float]
    global_bias: float
    fleet_consensus_loss: float
    contributing_clients: List[str]
    aggregation_weights: Dict[str, float]

"""
Base abstractions for aerospace asset dynamic simulations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class TelemetryFrame(BaseModel):
    timestamp_s: float
    asset_id: str
    asset_class: str
    measurements: Dict[str, float]
    operating_conditions: Dict[str, float]
    true_degradation: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAssetSimulator(ABC):
    """
    Abstract base class for high-fidelity physics asset simulators.
    Simulates multiphysics dynamic equations under variable operating conditions
    and injects degradation over operating cycles/time.
    """

    def __init__(self, asset_id: str, sampling_dt: float = 0.02):
        self.asset_id = asset_id
        self.dt = sampling_dt
        self.current_time = 0.0
        self.degradation = 0.0  # 0.0 = factory new, 1.0 = failure limit

    @abstractmethod
    def step(self, operating_conditions: Dict[str, float]) -> TelemetryFrame:
        """Advance simulation by dt under the specified operating environment."""
        pass

    @abstractmethod
    def reset(self, initial_degradation: float = 0.0) -> None:
        """Reset simulator state."""
        pass

    def inject_degradation(self, delta: float) -> None:
        """Incrementally advance internal physical degradation."""
        self.degradation = min(1.0, max(0.0, self.degradation + delta))

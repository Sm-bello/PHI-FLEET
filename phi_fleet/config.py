"""
Configuration definitions for the PHI-FLEET digital twin ecosystem.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AssetClass(str, Enum):
    AIRCRAFT_LANDING_GEAR = "aircraft_landing_gear"
    AIRCRAFT_TURBOFAN = "aircraft_turbofan"
    UAV_ELECTRIC_MOTOR = "uav_electric_motor"
    UAV_BATTERY = "uav_battery"


class HealthStatus(str, Enum):
    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    UNKNOWN_OOD = "UNKNOWN_OUT_OF_DISTRIBUTION"


class AssetConfig(BaseModel):
    asset_id: str
    asset_class: AssetClass
    platform_name: str
    sampling_rate_hz: float = 50.0
    nominal_parameters: Dict[str, float] = Field(default_factory=dict)
    operating_envelope: Dict[str, tuple] = Field(default_factory=dict)


class FleetConfig(BaseModel):
    fleet_name: str = "AeroFleet-Heterogeneous-Alpha"
    federated_rounds: int = 5
    local_epochs_per_round: int = 3
    epistemic_threshold: float = 0.25
    physics_residual_threshold: float = 2.5
    conformal_alpha: float = 0.10  # 90% confidence intervals
    assets: List[AssetConfig] = Field(default_factory=list)

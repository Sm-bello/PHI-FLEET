"""
Component Health Index (HI) Computation.

Fuses physics residual divergence, evidential certainty, and true degradation proxies
into a standardized aerospace health score:
  100% = Factory Pristine / Airworthy
    0% = Functional Failure Limit
"""

import math
from typing import Dict, Any


class HealthIndexCalculator:
    @staticmethod
    def compute_hi(estimated_degradation: float, composite_divergence: float) -> float:
        """
        Maps physical degradation and residual divergence into continuous Health Index [0, 100%].
        """
        # Base physical health
        base_health = max(0.0, 1.0 - estimated_degradation)

        # Mild penalty for dynamic residual instability if divergence > 2.0 sigma
        divergence_penalty = 0.02 * max(0.0, composite_divergence - 2.0)
        health_score = max(0.0, min(1.0, base_health - divergence_penalty))

        return round(health_score * 100.0, 1)

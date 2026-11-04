"""
Engineering Decision Support Engine.

Translates diagnostic evidence and RUL distributions into actionable maintenance work orders,
MEL (Minimum Equipment List) dispatch decisions, and airworthiness engineering advisories.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from phi_fleet.prognostics.rul_estimator import RULPrediction
from phi_fleet.prognostics.diagnostics import DiagnosticEvidence


class MaintenanceRecommendation(BaseModel):
    asset_id: str
    asset_class: str
    dispatch_status: str  # "AIRWORTHY", "DISPATCH_WITH_LIMITATION", "GROUNDED"
    recommended_action: str
    urgency_window_hours: float
    work_order_code: str
    rationale: str


class DecisionSupportEngine:
    @staticmethod
    def generate_recommendation(
        rul_info: RULPrediction,
        diag_evidence: DiagnosticEvidence,
    ) -> MaintenanceRecommendation:
        asset_id = rul_info.asset_id
        asset_class = rul_info.asset_class
        safe_rul = rul_info.lower_bound_rul_hours

        if diag_evidence.severity_level == "CRITICAL" or safe_rul < 25.0:
            status = "GROUNDED"
            urgency = min(safe_rul, 12.0)
            if asset_class == "aircraft_landing_gear":
                action = "Immediate strut de-servicing, nitrogen seal overhaul, and dynamic pressure leak test."
                code = "ATA-32-AOG-01"
            elif asset_class == "aircraft_turbofan":
                action = "Borescope inspection of HPT Stage 1 nozzle guide vanes & blade tip clearance verification."
                code = "ATA-72-AOG-03"
            elif asset_class == "uav_electric_motor":
                action = "Replace propulsion motor assembly; inspect ESC telemetry logs for phase over-current."
                code = "UAS-PROP-REPL-01"
            else:  # uav_battery
                action = "Battery pack decommission and electrochemical capacity recertification."
                code = "UAS-BATT-RECYC-02"

            rationale = (
                f"Critical failure threshold breached. Lower-bound conservative RUL is {safe_rul:.1f} hours. "
                "Airworthiness margins do not permit commercial sortie dispatch."
            )

        elif diag_evidence.severity_level == "WARNING" or safe_rul < 150.0:
            status = "DISPATCH_WITH_LIMITATION"
            urgency = safe_rul
            if asset_class == "aircraft_landing_gear":
                action = "Schedule nitrogen recharge and gland nut torque check at next overnight maintenance turn."
                code = "ATA-32-LINE-02"
            elif asset_class == "aircraft_turbofan":
                action = "Perform compressor water wash and recalibrate EGT thermocouples within 50 flight hours."
                code = "ATA-72-LINE-04"
            elif asset_class == "uav_electric_motor":
                action = "Inspect motor bearing end-play and measure phase-to-phase winding resistance."
                code = "UAS-PROP-INSP-03"
            else:  # uav_battery
                action = "Enforce max discharge C-rate limitation (<= 2.5C); avoid freezing ambient sorties."
                code = "UAS-BATT-LIMIT-01"

            rationale = (
                f"Component in active degradation progression. Safe remaining operating window: {safe_rul:.1f} hours. "
                "Dispatch allowed under standard line maintenance deferral."
            )

        else:
            status = "AIRWORTHY"
            urgency = safe_rul
            action = "Continue scheduled fleet health monitoring. No corrective unscheduled maintenance required."
            code = "OPS-NOMINAL"
            rationale = "Operating within 90% confidence airworthiness margins."

        return MaintenanceRecommendation(
            asset_id=asset_id,
            asset_class=asset_class,
            dispatch_status=status,
            recommended_action=action,
            urgency_window_hours=round(urgency, 1),
            work_order_code=code,
            rationale=rationale,
        )

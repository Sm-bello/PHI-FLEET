"""
Explainable Diagnostic Evidence Generator.

Attribute anomalous physics residuals to specific mechanical, thermodynamic,
or electromechanical root causes with quantitative diagnostic evidence.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field


class DiagnosticEvidence(BaseModel):
    asset_id: str
    asset_class: str
    primary_failure_mode: str
    severity_level: str
    contributing_channels: List[Dict[str, Any]]
    physical_mechanism: str
    confidence_score: float


class DiagnosticEvidenceEngine:
    """
    Translates raw physics residuals into human-interpretable aerospace engineering evidence.
    """

    @staticmethod
    def generate_evidence(
        asset_id: str,
        asset_class: str,
        raw_residuals: Dict[str, float],
        normalized_residuals: Dict[str, float],
        estimated_degradation: float,
    ) -> DiagnosticEvidence:
        # Rank channels by absolute normalized residual
        sorted_channels = sorted(
            normalized_residuals.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        top_channel, top_z = sorted_channels[0] if sorted_channels else ("none", 0.0)

        # Physical attribution logic
        if asset_class == "aircraft_landing_gear":
            if "strut_pressure_bar" in raw_residuals and raw_residuals["strut_pressure_bar"] < -1.5:
                mode = "Oleo-Pneumatic Chamber Nitrogen Gas Depressurization / Seal Leakage"
                mech = (
                    f"Observed strut pressure is {abs(raw_residuals['strut_pressure_bar']):.2f} bar below "
                    "isentropic polytropic compression baseline. Indicates static nitrogen micro-leakage at main seal."
                )
            elif "strut_temperature_c" in raw_residuals and raw_residuals["strut_temperature_c"] > 3.0:
                mode = "Hydraulic Orifice Choking & Seal Friction Degradation"
                mech = "Elevated temperature indicates excessive viscous shear heating through worn metering pin."
            else:
                mode = "Nominal Landing Gear Operation"
                mech = "Residuals remain within normal operational aero-load tolerances."

        elif asset_class == "aircraft_turbofan":
            if "egt_celsius" in raw_residuals and raw_residuals["egt_celsius"] > 10.0:
                mode = "High-Pressure Turbine (HPT) Thermal Erosion & Tip Clearance Growth"
                mech = (
                    f"EGT is {raw_residuals['egt_celsius']:.1f}°C hotter than expected for current altitude/throttle. "
                    "Engine control unit is over-fueling to compensate for core stage efficiency loss."
                )
            elif "core_vibration_mms" in raw_residuals and raw_residuals["core_vibration_mms"] > 0.5:
                mode = "High-Pressure Rotor Shaft Unbalance / Bearing Raceway Spall"
                mech = "Elevated high-frequency radial vibration indicates mechanical imbalance in core spool."
            else:
                mode = "Nominal Turbofan Cycle"
                mech = "Core thermodynamics match calibrated nominal baseline."

        elif asset_class == "uav_electric_motor":
            if "winding_temp_c" in raw_residuals and raw_residuals["winding_temp_c"] > 4.0:
                mode = "Stator Phase Winding Thermal Degradation & Micro-Shorts"
                mech = (
                    f"Winding temperature elevated by {raw_residuals['winding_temp_c']:.1f}°C. "
                    "Phase current shows abnormal I^2*R Joule dissipation from degraded enamel insulation."
                )
            elif "bearing_vibration_ms2" in raw_residuals and raw_residuals["bearing_vibration_ms2"] > 1.2:
                mode = "Propulsion Motor Ball Bearing Pitting / Raceway Spalling"
                mech = "Mechanical vibration harmonics elevated above aerodynamic slipstream baseline."
            else:
                mode = "Nominal Motor Propulsion"
                mech = "Electromechanical conversion efficiency nominal."

        elif asset_class == "uav_battery":
            if "terminal_voltage_v" in raw_residuals and raw_residuals["terminal_voltage_v"] < -0.3:
                mode = "Li-Ion Electrolyte Decomposition & Internal Resistance (R0) Escalation"
                mech = (
                    f"Terminal voltage drop exceeds nominal ECM baseline by {abs(raw_residuals['terminal_voltage_v']):.2f}V under load. "
                    "Direct consequence of SEI layer thickening and internal impedance growth."
                )
            else:
                mode = "Nominal Battery Pack"
                mech = "Electrochemical polarization dynamics consistent with nominal capacity."
        else:
            mode = "Generic Asset Degradation"
            mech = "Deviation detected against physics baseline."

        severity = (
            "CRITICAL" if estimated_degradation > 0.55
            else "WARNING" if estimated_degradation > 0.25
            else "INFO"
        )

        channels_detail = [
            {"channel": ch, "raw_diff": round(raw_residuals.get(ch, 0.0), 3), "z_score": round(z, 2)}
            for ch, z in sorted_channels[:3]
        ]

        return DiagnosticEvidence(
            asset_id=asset_id,
            asset_class=asset_class,
            primary_failure_mode=mode,
            severity_level=severity,
            contributing_channels=channels_detail,
            physical_mechanism=mech,
            confidence_score=round(min(0.98, 0.70 + 0.30 * estimated_degradation), 2),
        )

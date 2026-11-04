# PHI-FLEET System Architecture

**Physics-Hybrid Intelligence for Federated Aerospace Fleet Health**  
**Principal Architect:** Mohammed Bello Sani ([@Sm-bello](https://github.com/Sm-bello))

---

## High-Level Architecture Overview

PHI-FLEET is organized into four decoupled, interoperable layers:

```
+-----------------------------------------------------------------------------------+
| LAYER 1: MULTI-ASSET SIMULATION ENVIRONMENT                                       |
| JSBSim · Simscape · Python Physics Models · UAV SITL                              |
|                                                                                   |
|    Aircraft Twin: Landing Gear · Turbofan Engine · Airframe Structure             |
|    UAV Twin: BLDC Electric Motors · Li-Ion Battery Pack · Aerodynamics            |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 2: PHYSICS-INFORMED DIGITAL TWIN ENGINE                                     |
| State Estimation · Physics Residuals · Degradation Models · Uncertainty Quant.    |
|                                                                                   |
|    r_k(t) = y_obs,k(t) - y_phys,k(t)                                              |
|    Evidential Disentanglement: Aleatoric vs Epistemic (OOD) vs Degradation        |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 3: FLEET INTELLIGENCE LAYER                                                 |
| Cross-Platform Learning · Federated Model Updates · Domain Adaptation (FedPhys)   |
|                                                                                   |
|    Invariant Latent Projection: z in R^4                                          |
|    Physics-Consistency Loss + Epistemic Certainty Aggregation                     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 4: ENGINEERING DECISION SUPPORT                                             |
| Health Assessment · Remaining Useful Life (RUL) · Maintenance Recommendations     |
|                                                                                   |
|    Conformal RUL Bounds [5th %, Median, 95th %] · Work Orders · MEL Dispatch      |
+-----------------------------------------------------------------------------------+
```

---

## Layer-by-Layer Detailed Breakdown

### Layer 1: Multi-Asset Simulation Environment (`phi_fleet.simulation`)
- **Landing Gear (`LandingGearSimulator`):**
  - Polytropic gas compression ($p_0 V_0^\gamma = p V^\gamma$)
  - Hydraulic orifice turbulent damping ($\dot{s}^2$)
  - Degradation modes: Nitrogen chamber micro-leakage, seal friction wear, thermal dissipation.
- **Turbofan Engine (`TurbofanEngineSimulator`):**
  - Brayton thermodynamic gas-cycle model
  - Exhaust Gas Temperature (EGT) margin decay
  - High-Pressure Rotor unbalance and bearing vibration harmonics.
- **UAV BLDC Motor (`UAVElectricMotorSimulator`):**
  - Electromechanical torque equation ($K_t I = J \dot{\omega} + B \omega + \tau_{\text{aero}}$)
  - Back-EMF and Joule heat dissipation
  - Degradation modes: Stator phase winding insulation degradation, raceway pitting.
- **UAV Li-Ion Battery (`UAVBatterySimulator`):**
  - Thevenin Equivalent Circuit Model (ECM)
  - Non-linear Open Circuit Voltage ($V_{\text{oc}}$) vs State of Charge (SOC)
  - Degradation modes: SEI layer growth, internal resistance escalation, capacity fade.

### Layer 2: Physics-Informed Digital Twin Engine (`phi_fleet.twin`)
- **Nominal Physics Estimator (`PhysicsEstimator`):** First-principles analytical baseline running in real time.
- **Physics Residual Engine (`PhysicsResidualEngine`):**
  $$\mathbf{r}_k(t) = \mathbf{y}_{obs, k}(t) - \hat{\mathbf{y}}_{phys, k}(t)$$
  Normalized against nominal 1-sigma operational noise.
- **Evidential Disentanglement Engine (`EvidentialDisentanglementEngine`):**
  Separates residual variance into:
  - Measurement noise (Aleatoric)
  - Unseen flight regime / out-of-distribution operating conditions (Epistemic)
  - Genuine structural or component degradation.

### Layer 3: Fleet Intelligence Layer (`phi_fleet.federated`)
- **Invariant Projection (`InvariantDegradationProjector`):**
  Maps arbitrary physical channels into universal latent coordinates:
  - $z_0$: Thermal stress manifestation
  - $z_1$: Mechanical / kinematic wear
  - $z_2$: Energy dissipation / impedance anomaly
  - $z_3$: Cross-stress fatigue interaction
- **Edge Client Twin (`FleetClientNode`):**
  Performs edge-level physics-regularized optimization. Telemetry never leaves the asset.
- **FedPhys Aggregator (`FleetFederatedServer`):**
  Aggregates client model weights scaled by physics consistency ($\exp(-\lambda \mathcal{L}_{\text{phys}})$) and evidential certainty ($1 - u_{\text{epistemic}}$).

### Layer 4: Engineering Decision Support (`phi_fleet.prognostics`)
- **Health Index Calculator (`HealthIndexCalculator`):** Continuous health percentage $[0, 100\%]$.
- **Conformal RUL Predictor (`ConformalRULPredictor`):** Computes median RUL with certified 90% confidence lower bounds for safe airworthiness dispatch.
- **Diagnostic Evidence Engine (`DiagnosticEvidenceEngine`):** Explainable engineering evidence pinpointing failing components and mechanical mechanisms.
- **Decision Support Engine (`DecisionSupportEngine`):** Issues actionable maintenance directives (ATA chapter work orders, AOG grounding notices, or MEL deferrals).

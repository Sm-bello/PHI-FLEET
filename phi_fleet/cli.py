"""
Command-line Interface (CLI) for PHI-FLEET.

Provides interactive commands to run multi-asset fleet simulation,
trigger physics residual engines, execute FedPhys cross-platform federated updates,
and render engineering diagnostics.
"""

import sys
import argparse
from typing import Dict, List, Any
from phi_fleet.simulation.fleet_generator import FleetSimulationOrchestrator
from phi_fleet.twin.residual_engine import PhysicsResidualEngine
from phi_fleet.twin.uncertainty import EvidentialDisentanglementEngine
from phi_fleet.federated.client_node import FleetClientNode
from phi_fleet.federated.server_aggregator import FleetFederatedServer
from phi_fleet.prognostics.health_index import HealthIndexCalculator
from phi_fleet.prognostics.rul_estimator import ConformalRULPredictor
from phi_fleet.prognostics.diagnostics import DiagnosticEvidenceEngine
from phi_fleet.prognostics.decision_support import DecisionSupportEngine
from phi_fleet.visualization.console import (
    console,
    print_banner,
    print_fleet_status_table,
    print_federated_round,
    print_diagnostics_report,
)


def run_fleet_demo(rounds: int = 3, simulation_steps: int = 30):
    """
    Executes a complete 4-layer demonstration of PHI-FLEET across heterogeneous assets.
    """
    print_banner()

    console.print("[bold yellow]Initializing Multi-Asset Simulation Environment...[/bold yellow]")
    orchestrator = FleetSimulationOrchestrator()
    classes = orchestrator.get_asset_classes()

    # Create Federated Nodes
    clients = {
        asset_id: FleetClientNode(asset_id, sim.step({}).asset_class)
        for asset_id, sim in orchestrator.simulators.items()
    }
    server = FleetFederatedServer(latent_dim=4, lambda_physics=2.0)

    console.print(f"[green][OK] Configured {len(clients)} digital twin nodes across Aircraft and UAV platforms.[/green]\n")

    # Step 1: Replay Telemetry and Ingest into Edge Twins
    console.print(f"[bold cyan]Replaying flight telemetry ({simulation_steps} frames per asset)...[/bold cyan]")
    for step_idx in range(simulation_steps):
        # Generate slightly varying atmospheric/flight conditions
        cond_map = {
            "AIRCRAFT-701-LG": {"sink_rate": 2.2 + 0.1 * (step_idx % 3), "ambient_temp": 18.0},
            "AIRCRAFT-701-ENG": {"throttle_pct": 84.0, "altitude_m": 10500.0, "ambient_temp": -49.0},
            "AIRCRAFT-702-ENG": {"throttle_pct": 88.0, "altitude_m": 9200.0, "ambient_temp": -38.0},
            "AIRCRAFT-703-LG": {"sink_rate": 1.9, "ambient_temp": 20.0},
            "UAV-ALPHA-MOTOR": {"throttle_pct": 72.0, "airspeed_m_s": 19.5, "ambient_temp": 26.0},
            "UAV-ALPHA-BATT": {"current_demand_a": 22.0, "ambient_temp": 26.0},
            "UAV-BETA-BATT": {"current_demand_a": 28.0, "ambient_temp": -14.0},  # sub-zero condition (OOD/stress)
            "UAV-GAMMA-MOTOR": {"throttle_pct": 65.0, "airspeed_m_s": 15.0, "ambient_temp": 42.0},  # desert heat
        }
        fleet_frames = orchestrator.step_fleet(cond_map)

        for asset_id, frame in fleet_frames.items():
            clients[asset_id].ingest_frame(frame)

    # Step 2: Cross-Fleet Intelligence & Federated Aggregation
    console.print("[bold cyan]Executing Cross-Platform Federated Learning (FedPhys)...[/bold cyan]")
    global_params = None
    for r in range(1, rounds + 1):
        updates = [client.train_local_epoch(epochs=2, lr=0.015) for client in clients.values()]
        global_params = server.aggregate(updates)
        for client in clients.values():
            client.update_parameters(global_params.global_weights, global_params.global_bias)
        print_federated_round(r, global_params)

    # Step 3: Compute Prognostics, Conformal RUL, and Maintenance Decisions
    console.print("[bold cyan]Synthesizing Engineering Decision Support...[/bold cyan]")
    rul_predictor = ConformalRULPredictor(confidence_level=0.90)
    summary_data = []
    evidence_list = []
    recommendation_list = []

    # Get one latest telemetry frame from each asset for final state
    final_frames = orchestrator.step_fleet({})

    for asset_id, client in clients.items():
        frame = final_frames[asset_id]
        res = client.residual_engine.compute_residuals(frame)
        unc = client.evidential_engine.evaluate(
            frame.asset_class,
            frame.operating_conditions,
            res["normalized_residuals"],
            res["composite_divergence"],
        )

        hi = HealthIndexCalculator.compute_hi(
            unc["estimated_degradation"],
            res["composite_divergence"],
        )

        # Global learned degradation projection factor
        global_factor = sum(global_params.global_weights) / len(global_params.global_weights) if global_params else 0.05

        rul = rul_predictor.predict_rul(
            asset_id=asset_id,
            asset_class=frame.asset_class,
            health_index_pct=hi,
            epistemic_uncertainty=unc["epistemic_uncertainty"],
            aleatoric_uncertainty=unc["aleatoric_uncertainty"],
            global_degradation_rate=global_factor,
        )

        ev = DiagnosticEvidenceEngine.generate_evidence(
            asset_id=asset_id,
            asset_class=frame.asset_class,
            raw_residuals=res["raw_residuals"],
            normalized_residuals=res["normalized_residuals"],
            estimated_degradation=unc["estimated_degradation"],
        )

        rec = DecisionSupportEngine.generate_recommendation(rul, ev)

        summary_data.append({
            "asset_id": asset_id,
            "subsystem": frame.asset_class.replace("_", " ").title(),
            "health_index": hi,
            "composite_divergence": res["composite_divergence"],
            "epistemic_u": unc["epistemic_uncertainty"],
            "median_rul": rul.median_rul_hours,
            "safe_bound": rul.lower_bound_rul_hours,
            "dispatch_status": rec.dispatch_status,
        })
        evidence_list.append(ev)
        recommendation_list.append(rec)

    print_fleet_status_table(summary_data)
    print_diagnostics_report(evidence_list, recommendation_list)

    console.print(
        "[bold green][OK] PHI-FLEET Demonstration Completed Successfully.[/bold green]\n"
        "[dim]Repository: https://github.com/Sm-bello/PHI-FLEET[/dim]\n"
    )


def main():
    parser = argparse.ArgumentParser(
        prog="phi-fleet",
        description="Physics-Hybrid Intelligence for Federated Aerospace Fleet Health",
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run end-to-end multi-asset fleet simulation & FedPhys demo")
    demo_parser.add_argument("--rounds", type=int, default=3, help="Number of federated rounds")
    demo_parser.add_argument("--steps", type=int, default=30, help="Number of simulation steps per asset")

    args = parser.parse_args()

    if args.command == "demo" or len(sys.argv) == 1:
        rounds = getattr(args, "rounds", 3)
        steps = getattr(args, "steps", 30)
        run_fleet_demo(rounds=rounds, simulation_steps=steps)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""
Rich Terminal Console UI for PHI-FLEET.

Displays aerospace fleet telemetry, physics residual metrics, federated learning rounds,
and engineering decision support tables.
"""

import os
import sys
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

# Ensure robust UTF-8 handling on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(highlight=False)


def print_banner():
    banner_text = Text()
    banner_text.append("[*] PHI-FLEET [*]\n", style="bold cyan")
    banner_text.append("Physics-Hybrid Intelligence for Federated Aerospace Fleet Health\n", style="bold white")
    banner_text.append("Lead Architect & Researcher: Mohammed Bello Sani (Sm-bello)\n", style="dim cyan")
    banner_text.append("Targeting: AIAA SciTech | IEEE Aerospace | PHM Society", style="italic yellow")

    panel = Panel(
        banner_text,
        border_style="cyan",
        box=box.ASCII2 if sys.platform == "win32" else box.DOUBLE,
        padding=(1, 2),
    )
    console.print(panel)



def print_fleet_status_table(fleet_summary: List[Dict[str, Any]]):
    table = Table(
        title="[bold green]FLEET HEALTH & PROGNOSTICS SUMMARY[/bold green]",
        box=box.ASCII2 if sys.platform == "win32" else box.ROUNDED,
        header_style="bold magenta",
    )

    table.add_column("Asset ID", style="cyan", no_wrap=True)
    table.add_column("Subsystem", style="white")
    table.add_column("Health Index", justify="right")
    table.add_column("Residual Div.", justify="right")
    table.add_column("Epistemic U", justify="right")
    table.add_column("Median RUL", justify="right", style="bold yellow")
    table.add_column("Safe 90% Bound", justify="right", style="bold green")
    table.add_column("Dispatch Status", justify="center")

    for item in fleet_summary:
        hi = item["health_index"]
        hi_style = "bold green" if hi > 75 else "bold yellow" if hi > 40 else "bold red"
        hi_str = f"[{hi_style}]{hi:.1f}%[/{hi_style}]"

        div = item["composite_divergence"]
        div_str = f"{div:.2f} sigma"

        epistemic = item["epistemic_u"]
        ep_style = "green" if epistemic < 0.20 else "yellow" if epistemic < 0.35 else "bold red"
        ep_str = f"[{ep_style}]{epistemic:.2f}[/{ep_style}]"

        rul = f"{item['median_rul']:.1f} hrs"
        safe_bound = f"{item['safe_bound']:.1f} hrs"

        status = item["dispatch_status"]
        if status == "AIRWORTHY":
            status_str = "[bold green]AIRWORTHY[/bold green]"
        elif status == "DISPATCH_WITH_LIMITATION":
            status_str = "[bold yellow]DISPATCH (MEL)[/bold yellow]"
        else:
            status_str = "[bold red]GROUNDED (AOG)[/bold red]"

        table.add_row(
            item["asset_id"],
            item["subsystem"],
            hi_str,
            div_str,
            ep_str,
            rul,
            safe_bound,
            status_str,
        )

    console.print(table)


def print_federated_round(round_num: int, global_params: Any):
    table = Table(
        title=f"[bold blue]FEDERATED AGGREGATION (FedPhys) -- ROUND {round_num}[/bold blue]",
        box=box.ASCII2 if sys.platform == "win32" else box.SIMPLE_HEAVY,
    )
    table.add_column("Parameter Coordinate", style="cyan")
    table.add_column("Global Consensus Weight", justify="right", style="bold white")
    table.add_column("Physical Manifold Meaning", style="dim white")

    coord_names = [
        ("z_0 (Thermal Stress)", "Arrhenius thermal aging kinetics"),
        ("z_1 (Mechanical Wear)", "Friction & raceway clearance wear"),
        ("z_2 (Energy Dissipation)", "Ohmic/polarization impedance rate"),
        ("z_3 (Thermo-Mechanical)", "Paris-Erdogan cyclic fatigue growth"),
    ]

    for (name, desc), w in zip(coord_names, global_params.global_weights):
        table.add_row(name, f"{w:.4f}", desc)

    console.print(table)
    console.print(f"[dim]Contributing Fleet Nodes: {', '.join(global_params.contributing_clients)}[/dim]")
    console.print(f"[dim]Fleet-wide Physics Loss: {global_params.fleet_consensus_loss:.5f}[/dim]\n")


def print_diagnostics_report(evidence_list: List[Any], recommendations: List[Any]):
    table = Table(
        title="[bold red]ENGINEERING DECISION SUPPORT & DIAGNOSTIC EVIDENCE[/bold red]",
        box=box.ASCII2 if sys.platform == "win32" else box.DOUBLE_EDGE,
        header_style="bold red",
    )
    table.add_column("Asset ID", style="cyan")
    table.add_column("Identified Failure Mode", style="bold white")
    table.add_column("Primary Physical Mechanism", style="italic")
    table.add_column("Actionable Maintenance Directive", style="yellow")

    for ev, rec in zip(evidence_list, recommendations):
        if rec.dispatch_status != "AIRWORTHY":
            table.add_row(
                ev.asset_id,
                ev.primary_failure_mode,
                ev.physical_mechanism,
                f"[{rec.work_order_code}] {rec.recommended_action}",
            )

    console.print(table)

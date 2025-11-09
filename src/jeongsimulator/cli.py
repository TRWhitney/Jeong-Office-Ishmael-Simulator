"""Command-line interface for running the Jeong simulator."""

from __future__ import annotations

import sys
from typing import Sequence

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .simulation import CARD_COLORS, Action, Card, JeongSimulation, TurnEndResult, TurnSnapshot

console = Console()

SUIT_STYLES = {
    "Red": "bold red",
    "Yellow": "bold gold1",
    "Blue": "bold cyan",
}

SUIT_ICONS = {
    "Red": "🔻",
    "Yellow": "🔶",
    "Blue": "🔷",
}

CARD_ICONS = {
    Card.S1: "①",
    Card.S2: "②",
    Card.S3: "③",
}

BRIGHT_ICON = "⚡"
COUNT_ICON = "⏳"
ACTION_ICONS = {
    Action.USE_FIRST: "🎴",
    Action.USE_SECOND: "🎴",
    Action.DEFEND: "🛡️",
    Action.EGO: "🌀",
}


def main(interactive: bool | None = None) -> None:
    """Entry point dispatched by the package script."""

    if interactive is None:
        interactive = _detect_interactive()
    try:
        if interactive:
            run_interactive()
        else:
            run_smoke()
    except KeyboardInterrupt:
        _handle_interrupt()


def run_smoke(turns: int = 2) -> None:
    """Non-interactive smoke scenario used by automation."""

    sim = JeongSimulation()
    console.rule("[bold cyan]JeongSimulator Smoke Run[/]")
    for turn in range(1, turns + 1):
        console.rule(f"[bold white]Turn {turn}[/]")
        snapshot = sim.start_turn()
        _print_snapshot(snapshot)
        action = _default_action(snapshot)
        console.print(
            Panel.fit(
                f"{ACTION_ICONS[action]} Auto action → [bold]{action.value}[/]",
                border_style="bright_black",
            )
        )
        result = sim.resolve(action)
        _print_messages(result.messages)
        end_state = sim.end_turn()
        _print_end_state(end_state)
    console.print()
    console.print("[bold green]JeongSimulator smoke run complete.[/]")


def run_interactive() -> None:
    """Interactive loop for manual play."""

    sim = JeongSimulation()
    turn = 1
    console.rule("[bold cyan]Jeong Office Ishmael Simulator[/]")
    console.print("Press [bold]q[/] at any prompt to quit.\n")
    while True:
        console.rule(f"[bold white]Turn {turn}[/]")
        snapshot = sim.start_turn()
        _print_snapshot(snapshot)
        action = _prompt_for_action(snapshot)
        result = sim.resolve(action)
        _print_messages(result.messages)
        end_state = sim.end_turn()
        _print_end_state(end_state)
        turn += 1


def _detect_interactive() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:  # pragma: no cover - defensive
        return False


def _print_snapshot(snapshot: TurnSnapshot) -> None:
    suit_name = snapshot.suit.value
    suit_style = SUIT_STYLES[suit_name]
    suit_icon = SUIT_ICONS[suit_name]
    header = Text(
        f"{suit_icon} {suit_name} ",
        style=suit_style,
    )
    header.append(f"{BRIGHT_ICON} {snapshot.bright_potency}/5   {COUNT_ICON} {snapshot.bright_count}", style="bold white")

    offer_table = Table(
        "Slot",
        "Card",
        "Color",
        title="Offer",
        box=box.SIMPLE,
        expand=False,
        show_edge=True,
        header_style="bold magenta",
    )
    if snapshot.offer:
        for idx, card in enumerate(snapshot.offer, start=1):
            color = CARD_COLORS[card]
            offer_table.add_row(
                f"[bold]{idx}[/]",
                f"{CARD_ICONS.get(card, '•')} {card.value}",
                f"[{SUIT_STYLES[color.value]}]{color.value}[/]",
            )
    else:
        offer_table.add_row("–", "Empty", "-")

    console.print(Panel.fit(offer_table, title=header, border_style=suit_style))
    console.print("Actions: [bold]1[/]=First  [bold]2[/]=Second  [bold]d[/]=Defend  [bold]e[/]=EGO  [bold]q[/]=Quit")


def _default_action(snapshot: TurnSnapshot) -> Action:
    if snapshot.offer:
        return Action.USE_FIRST
    return Action.DEFEND


def _prompt_for_action(snapshot: TurnSnapshot) -> Action:
    valid = {"1": Action.USE_FIRST, "d": Action.DEFEND, "e": Action.EGO, "q": None}
    if len(snapshot.offer) >= 2:
        valid["2"] = Action.USE_SECOND
    while True:
        choice = console.input("[bold green]Select action[/]: ").strip().lower() or "1"
        if choice == "q":
            console.print("[bold red]Exiting JeongSimulator.[/]")
            sys.exit(0)
        action = valid.get(choice)
        if action is not None:
            return action
        console.print("[bold red]Invalid choice. Try again.[/]")


def _print_messages(messages: Sequence[str]) -> None:
    if not messages:
        return
    bullet_lines = "\n".join(f"• {message}" for message in messages)
    console.print(Panel.fit(bullet_lines, title="Resolution", border_style="green"))


def _print_end_state(end_state: TurnEndResult) -> None:
    if not isinstance(end_state, TurnEndResult):  # pragma: no cover - defensive
        return
    body = f"{BRIGHT_ICON} {end_state.bright_potency}/5   {COUNT_ICON} {end_state.bright_count}"
    extra = []
    if end_state.kozan:
        seq = ", ".join(end_state.kozan.flips)
        extra.append(f"Kōzan → {seq} → {end_state.kozan.hits} hits")
    if end_state.cycle_reset and end_state.new_suit:
        extra.append(f"Cycle reset → new suit {end_state.new_suit.value}")
    elif end_state.suit_shuffle_pending:
        extra.append("Suit will shuffle at the next start")
    if extra:
        body = f"{body}\n" + "\n".join(extra)
    console.print(Panel.fit(body, title="End of Turn", border_style="blue"))


def _handle_interrupt() -> None:
    console.print()
    console.print("[bold yellow]Interrupted by user. Exiting JeongSimulator gracefully.[/]")


__all__ = ["main", "run_interactive", "run_smoke"]

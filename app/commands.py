"""CLI commands for BreathQuest."""

from __future__ import annotations

import click
from flask import Flask
from seed import run_all_seeds


def register_commands(app: Flask) -> None:
    """Register custom CLI commands with the Flask application."""

    @app.cli.command("seed")
    def seed_command() -> None:
        """Seed the database with initial ward rooms, prerequisites, and clinical activities."""
        click.echo("Seeding ward rooms, prerequisites, and clinical activities...")
        results = run_all_seeds()
        click.echo(
            f"Done! Created {results['missions']} new missions, "
            f"{results['prerequisites']} prerequisites, "
            f"{results['activities']} activities verified/seeded."
        )

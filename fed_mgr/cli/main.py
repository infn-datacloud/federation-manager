"""Module with the CLI commands."""

import typer

from fed_mgr.cli.users import app as user_app

app = typer.Typer()

app.add_typer(user_app, name="users")

if __name__ == "__main__":
    app()

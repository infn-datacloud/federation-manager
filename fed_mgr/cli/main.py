"""Module with the CLI commands."""

import typer

from fed_mgr.cli.identity_providers import app as idps_app
from fed_mgr.cli.providers import app as providers_app
from fed_mgr.cli.users import app as users_app

app = typer.Typer()

app.add_typer(users_app, name="users")
app.add_typer(idps_app, name="idps")
app.add_typer(providers_app, name="providers")

if __name__ == "__main__":
    app()

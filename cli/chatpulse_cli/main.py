import os
import typer
from . import auth, rooms, messages
from .chat import run_chat
from .config import (
    get_api_url,
    set_api_url,
    unset_api_url,
    DEFAULT_API_URL,
    CONFIG_FILE,
)
from .ui import console, print_success, print_error, print_info

app = typer.Typer(
    name="chatpulse",
    help="Terminal-based client for ChatPulse real-time chat",
    no_args_is_help=True,
)

app.add_typer(auth.app, name="auth", help="Authentication commands")
app.add_typer(rooms.app, name="rooms", help="Room management commands")
app.add_typer(messages.app, name="messages", help="Message commands")
app.add_typer(config_app := typer.Typer(help="CLI configuration"), name="config")


@config_app.command("show")
def config_show():
    """Show current CLI configuration."""
    current = get_api_url()
    console.print(f"[bold]API URL:[/bold] {current}")
    console.print(f"[bold]Config file:[/bold] {CONFIG_FILE}")
    if current == DEFAULT_API_URL:
        print_info("Using default (no config file override)")


@config_app.command("set-api-url")
def config_set_api_url(
    url: str = typer.Argument(..., help="API base URL (e.g. https://api.chatpulse.online/api)"),
):
    """Set a persistent API URL override."""
    try:
        set_api_url(url)
        os.environ["CHATPULSE_API_URL"] = url
        print_success(f"API URL set to [bold]{url}[/bold]")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@config_app.command("reset")
def config_reset():
    """Reset API URL to the default (production)."""
    unset_api_url()
    os.environ.pop("CHATPULSE_API_URL", None)
    print_success(f"Reset to default: [bold]{DEFAULT_API_URL}[/bold]")


@app.command()
def chat(
    room_id: int = typer.Argument(..., help="Room ID to enter"),
):
    """Enter interactive chat mode for a room."""
    run_chat(room_id)


@app.callback()
def main_callback(
    api_url: str = typer.Option(
        None,
        "--api-url",
        envvar="CHATPULSE_API_URL",
        help="Override API base URL (persisted on next login)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    if api_url:
        os.environ["CHATPULSE_API_URL"] = api_url
    if verbose:
        typer.echo(f"API URL: {get_api_url()}")

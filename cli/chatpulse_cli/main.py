import os
import typer
from . import auth, rooms, messages
from .chat import run_chat
from .config import get_api_url

app = typer.Typer(
    name="chatpulse",
    help="Terminal-based client for ChatPulse real-time chat",
    no_args_is_help=True,
)

app.add_typer(auth.app, name="auth", help="Authentication commands")
app.add_typer(rooms.app, name="rooms", help="Room management commands")
app.add_typer(messages.app, name="messages", help="Message commands")


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
        help="Override API base URL",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    if api_url:
        os.environ["CHATPULSE_API_URL"] = api_url
    if verbose:
        typer.echo(f"API URL: {get_api_url()}")

from datetime import datetime
import typer
from .client import get_client
from .ui import console, print_error, print_info

app = typer.Typer(help="Message commands")


@app.command()
def send(
    room_id: int = typer.Argument(..., help="Room ID"),
    content: str = typer.Argument(..., help="Message text"),
):
    """Send a message to a room."""
    try:
        data = get_client().send_message(room_id, content)
        console.print(f"[bold green]\u2713[/bold green] {data['status']}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def history(
    room_id: int = typer.Argument(..., help="Room ID"),
    limit: int = typer.Option(50, "--limit", "-l", help="Number of messages"),
    before_id: int = typer.Option(
        None, "--before-id", "-b", help="Cursor for pagination"
    ),
):
    """Show message history for a room."""
    try:
        data = get_client().get_messages(room_id, limit, before_id)
        msgs = data.get("messages", [])
        if not msgs:
            print_info("No messages yet.")
            return
        for m in msgs:
            ts = datetime.fromisoformat(m["timestamp"]).strftime("%H:%M:%S")
            sender = m["sender"]["username"]
            console.print(
                f"[dim]{ts}[/dim] [bold]{sender}:[/bold] {m['content']}"
            )
        console.print(
            f"\n[dim]Showing {len(msgs)} message(s). "
            f"Use [bold]--before-id {msgs[0]['id']}[/bold] to see earlier.[/dim]"
        )
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

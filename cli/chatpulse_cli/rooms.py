import typer
from .client import get_client
from .ui import console, print_success, print_error, print_info, room_table, members_panel

app = typer.Typer(help="Room management commands")


@app.command("list")
def list_rooms():
    """List all available rooms."""
    try:
        client = get_client()
        user = client.get_current_user() or client.me()
        rooms = client.list_rooms()
        if not rooms:
            print_info(
                "No rooms yet. Create one with [bold]chatpulse rooms create[/bold]"
            )
            return
        console.print(room_table(rooms, user["id"]))
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Argument(..., help="Room name (min 3 characters)"),
):
    """Create a new room and auto-join."""
    try:
        data = get_client().create_room(name)
        print_success(f"Room [bold]'{data['name']}'[/bold] created and joined!")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def show(
    room_id: int = typer.Argument(..., help="Room ID"),
):
    """Show room details and members."""
    try:
        data = get_client().room_detail(room_id)
        console.print(members_panel(data["room"], data["members"]))
        console.print(f"[dim]Created: {data['room']['created_at']}[/dim]")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def join(
    room_id: int = typer.Argument(..., help="Room ID to join"),
):
    """Join a room."""
    try:
        data = get_client().join_room(room_id)
        print_success(data["message"])
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def leave(
    room_id: int = typer.Argument(..., help="Room ID to leave"),
):
    """Leave a room. If you are the creator, the room is permanently deleted."""
    try:
        client = get_client()
        user = client.get_current_user() or client.me()
        detail = client.room_detail(room_id)
        room = detail["room"]
        if room["creator"]["id"] == user["id"]:
            typer.confirm(
                "You are the creator. Leaving will permanently delete this room "
                "and ALL messages. Continue?",
                abort=True,
            )
        data = client.leave_room(room_id)
        print_success(data["message"])
    except typer.Abort:
        print_info("Cancelled.")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_success(message: str):
    console.print(f"[bold green]\u2713[/bold green] {message}")


def print_error(message: str):
    console.print(f"[bold red]\u2717[/bold red] {message}")


def print_info(message: str):
    console.print(f"[bold blue]\u2139[/bold blue] {message}")


def room_table(rooms: list, current_user_id: int | None = None) -> Table:
    table = Table(title="Rooms", border_style="cyan")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Name", style="bold")
    table.add_column("Creator")
    table.add_column("Members", justify="right")
    table.add_column("Joined", justify="center")
    for r in rooms:
        creator = r["creator"]["username"]
        is_member = "(you)" if current_user_id and r.get("is_member") else ""
        table.add_row(
            str(r["id"]),
            r["name"],
            creator,
            str(r["member_count"]),
            is_member,
        )
    return table


def members_panel(room: dict, members: list) -> Panel:
    text = Text()
    for m in members:
        user = m["user"]
        tag = "  (you)" if room["room"]["creator"]["id"] == user["id"] else ""
        text.append(f"  \u2022 {user['username']}{tag}\n")
    return Panel(text, title=f"[bold]{room['room']['name']}[/bold]", border_style="cyan")

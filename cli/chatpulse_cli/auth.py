import typer
from .client import get_client, reset_client
from .ui import console, print_success, print_error

app = typer.Typer(help="Authentication commands")


@app.command()
def register(
    username: str = typer.Argument(..., help="Desired username"),
    email: str = typer.Argument(..., help="Email address"),
    password: str = typer.Option(
        ...,
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Password",
    ),
):
    """Register a new account."""
    try:
        data = get_client().register(username, email, password)
        print_success(data["message"])
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def login(
    username: str = typer.Argument(..., help="Your username"),
    password: str = typer.Option(
        ..., prompt=True, hide_input=True, help="Your password"
    ),
):
    """Login and store JWT tokens."""
    try:
        data = get_client().login(username, password)
        print_success(f"Logged in as [bold]{data['user']['username']}[/bold]")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def logout():
    """Logout and clear stored tokens."""
    try:
        client = get_client()
        if client._refresh_token:
            client.logout()
        else:
            reset_client()
        print_success("Logged out.")
    except Exception:
        reset_client()
        print_success("Logged out (cleared local tokens).")


@app.command()
def me():
    """Show current user profile."""
    try:
        user = get_client().me()
        console.print(f"[bold]Username:[/bold] {user['username']}")
        console.print(f"[bold]Email:[/bold]    {user['email']}")
        console.print(f"[bold]Online:[/bold]   {'Yes' if user['is_online'] else 'No'}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

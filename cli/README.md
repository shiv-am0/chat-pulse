# ChatPulse CLI

Terminal-based client for [ChatPulse](https://chatpulse.online) — a real-time messaging platform powered by Kafka.

## Install

**macOS / Linux** (installs pipx if missing and configures your shell PATH):

```bash
curl -fsSL https://chatpulse.online/install.sh | bash
```

**Windows** (PowerShell — auto-installs pipx if missing):

```powershell
irm https://chatpulse.online/install.ps1 | iex
```

**Any OS** (pipx required — see [Prerequisites](#prerequisites)):

```bash
pipx install chatpulse-cli
pipx ensurepath
```

The CLI installs into an isolated pipx environment, so it does not add packages to your system Python environment. Open a new terminal after installation so your shell loads the persisted PATH change.

## Quick Start

```bash
# Register a new account
chatpulse auth register username your@email.com

# Login
chatpulse auth login username

# List rooms
chatpulse rooms list

# Start chatting in room 1
chatpulse chat 1
```

## Features

- JWT-based authentication
- Room creation, listing, joining, leaving
- Real-time message sending and polling
- Interactive chat mode
- Persistent config across sessions

## Requirements

Python 3.10+

## Prerequisites

- **Python 3.10+** — install from <https://python.org/downloads> if missing.
- **pipx** — the install scripts bootstrap it automatically (via your package manager, or into an isolated fallback environment; they never use `--break-system-packages`). To install it yourself: `brew install pipx` (macOS), `sudo apt install pipx` (Debian/Ubuntu), or `python3 -m pip install --user pipx`.
- **Windows** — interactive `chatpulse chat` requires [WSL](https://learn.microsoft.com/windows/wsl/install); all other commands run natively in PowerShell.

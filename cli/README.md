# ChatPulse CLI

Terminal-based client for [ChatPulse](https://chatpulse.online) — a real-time messaging platform powered by Kafka.

```bash
pip install chatpulse-cli
```

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

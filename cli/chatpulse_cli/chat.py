import threading
import queue
import time
import select
import sys
import logging
from datetime import datetime
from rich.text import Text
from .client import get_client, ChatPulseError
from .ui import console, print_error, print_info
from .config import get_poll_interval

logger = logging.getLogger(__name__)


def fmt_msg(m: dict, user_id: int) -> str:
    ts = datetime.fromisoformat(m["timestamp"]).strftime("%H:%M:%S")
    tag = "you" if m["sender"]["id"] == user_id else m["sender"]["username"]
    return f"[dim]{ts}[/dim] [bold]{tag}:[/bold] {m['content']}"


def run_chat(room_id: int):
    client = get_client()

    try:
        room_data = client.room_detail(room_id)
        room_name = room_data["room"]["name"]
    except ChatPulseError as e:
        print_error(str(e))
        return

    user = client.get_current_user() or client.me()
    msg_queue: queue.Queue = queue.Queue()
    stop_event = threading.Event()
    latest_id: int | None = None

    # ── Polling thread ───────────────────────────────────
    def poll_messages():
        nonlocal latest_id
        interval = get_poll_interval()
        backoff = interval

        while not stop_event.is_set():
            try:
                data = client.get_messages(room_id, limit=50)
                for m in reversed(data.get("messages", [])):
                    if latest_id is None or m["id"] > latest_id:
                        msg_queue.put(m)
                        latest_id = m["id"]
                backoff = interval
            except ChatPulseError:
                logger.warning("Poll failed, backing off", exc_info=True)
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
            except Exception:
                logger.exception("Unexpected poll error")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
            time.sleep(interval)

    poller = threading.Thread(target=poll_messages, daemon=False)
    poller.start()

    # ── Helpers ──────────────────────────────────────────
    def drain_messages() -> bool:
        any_new = False
        while True:
            try:
                m = msg_queue.get_nowait()
                console.print(Text.from_markup(fmt_msg(m, user["id"])))
                any_new = True
            except queue.Empty:
                break
        return any_new

    # ── Pre-load existing messages ────────────────────────
    try:
        data = client.get_messages(room_id, limit=20)
        for m in data.get("messages", []):
            msg_queue.put(m)
            if latest_id is None or m["id"] > latest_id:
                latest_id = m["id"]
    except ChatPulseError:
        logger.exception("Failed to pre-load messages")

    # ── Welcome ──────────────────────────────────────────
    print_info(f"Joined [bold]{room_name}[/bold] (room {room_id})")
    print_info("Type your message and press Enter to send.")
    print_info("Commands: [bold]/q[/bold] quit  [bold]/help[/bold] this")
    console.print(Text("\u2500" * min(60, console.width), style="dim"))
    drain_messages()
    console.print(Text("\u2500" * min(60, console.width), style="dim"))

    # ── Main loop ─────────────────────────────────────────
    needs_prompt = True
    try:
        while not stop_event.is_set():
            if drain_messages():
                needs_prompt = True

            if needs_prompt:
                sep = "\u2500" * min(32, console.width // 2)
                sys.stdout.write(f"\r\033[K{sep}\n> ")
                sys.stdout.flush()
                needs_prompt = False

            r, _, _ = select.select([sys.stdin], [], [], 0.2)
            if not r:
                continue

            raw = sys.stdin.readline().strip()
            sys.stdout.write("\r\033[K")
            if not raw:
                needs_prompt = True
                continue

            if raw == "/q":
                break

            if raw == "/help":
                print_info("/q  quit chat  |  /help  this message")
                needs_prompt = True
                continue

            try:
                client.send_message(room_id, raw)
                sys.stdout.write("\r\033[K")
            except ChatPulseError as e:
                print_error(str(e))

            needs_prompt = True

    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        poller.join(timeout=5)
        print_info("Exited chat.")

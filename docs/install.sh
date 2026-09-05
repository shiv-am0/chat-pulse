#!/usr/bin/env bash
#
# ChatPulse CLI installer for macOS and Linux
#
# Installs the `chatpulse` CLI into its own isolated environment via pipx.
#
#   curl -fsSL https://chatpulse.online/install.sh | bash
#
set -euo pipefail

PACKAGE="chatpulse-cli"

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { printf "%b\n" "${GREEN}✓${NC} $*"; }
info() { printf "%b\n" "${CYAN}→${NC} $*"; }
warn() { printf "%b\n" "${YELLOW}⚠${NC} $*"; }
die()  { printf "%b\n" "${RED}✗${NC} $*" >&2; exit 1; }

printf "\n"
printf "%b\n" "${BOLD}${CYAN}  ┌─────────────────────────────────────────┐${NC}"
printf "%b\n" "${BOLD}${CYAN}  │           ChatPulse CLI Install          │${NC}"
printf "%b\n" "${BOLD}${CYAN}  └─────────────────────────────────────────┘${NC}"
printf "\n"
info "Prerequisites:"
info "  • Python 3.10 or newer"
info "  • pipx (installed below if missing)"
printf "\n"

if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    die "Do not run this installer as root. Run it from your normal user account."
fi

# ── 1. Detect OS ───────────────────────────────────────────
case "$(uname -s)" in
    Darwin) OS="macos" ;;
    Linux) OS="linux" ;;
    *) die "This installer supports macOS and Linux. On Windows, use install.ps1." ;;
esac

# ── 2. Detect Python 3.10+ ─────────────────────────────────
PYTHON=""
PY_VER=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
        "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        PYTHON="$(command -v "$candidate")"
        PY_VER="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    die "Python 3.10+ not found. Install it first: https://python.org/downloads"
fi
ok "Python $PY_VER found ($PYTHON)"

# Store the executable and optional arguments separately so paths with spaces work.
PIPX=()

find_pipx() {
    local resolved=""
    if resolved="$(command -v pipx 2>/dev/null)" && [ -n "$resolved" ]; then
        PIPX=("$resolved")
        return 0
    fi

    if "$PYTHON" -m pipx --version >/dev/null 2>&1; then
        PIPX=("$PYTHON" -m pipx)
        return 0
    fi

    for candidate in "$HOME/.local/bin/pipx" "$HOME/.local/share/pipx-bootstrap/bin/pipx"; do
        if [ -x "$candidate" ]; then
            PIPX=("$candidate")
            return 0
        fi
    done

    return 1
}

# ── 3. Locate pipx (or bootstrap it) ───────────────────────
if ! find_pipx; then
    info "pipx not found. Installing it for your user account..."

    package_install_succeeded=false
    if [ "$OS" = "macos" ] && command -v brew >/dev/null 2>&1; then
        if brew install pipx; then
            package_install_succeeded=true
        fi
    elif [ "$OS" = "linux" ] && command -v sudo >/dev/null 2>&1; then
        if command -v apt-get >/dev/null 2>&1 && sudo apt-get update -y && sudo apt-get install -y pipx; then
            package_install_succeeded=true
        elif command -v dnf >/dev/null 2>&1 && sudo dnf install -y pipx; then
            package_install_succeeded=true
        elif command -v pacman >/dev/null 2>&1 && sudo pacman -S --noconfirm python-pipx; then
            package_install_succeeded=true
        fi
    fi

    if [ "$package_install_succeeded" != true ] && ! "$PYTHON" -m pip install --user pipx; then
        warn "The package manager and user-level pip installation were unavailable."
    fi

    if ! find_pipx; then
        info "Creating an isolated pipx bootstrap environment..."
        PIPX_BOOTSTRAP="$HOME/.local/share/pipx-bootstrap"
        "$PYTHON" -m venv "$PIPX_BOOTSTRAP"
        "$PIPX_BOOTSTRAP/bin/python" -m pip install --upgrade pip pipx
        PIPX=("$PIPX_BOOTSTRAP/bin/pipx")
    fi
fi

PIPX_DESCRIPTION="${PIPX[*]}"
ok "Using pipx: $PIPX_DESCRIPTION"

# ── 4. Persist and refresh the pipx application path ───────
if ! ENSUREPATH_OUTPUT="$("${PIPX[@]}" ensurepath 2>&1)"; then
    printf "%s\n" "$ENSUREPATH_OUTPUT" >&2
    die "pipx could not update your shell PATH. Run '$PIPX_DESCRIPTION ensurepath' and retry."
fi

PIPX_APP_DIR="$("${PIPX[@]}" environment --value PIPX_BIN_DIR 2>/dev/null || true)"
if [ -z "$PIPX_APP_DIR" ]; then
    PIPX_APP_DIR="${PIPX_BIN_DIR:-$HOME/.local/bin}"
fi

case ":$PATH:" in
    *":$PIPX_APP_DIR:"*) ;;
    *) export PATH="$PIPX_APP_DIR:$PATH" ;;
esac

# ── 5. Install or upgrade the CLI ──────────────────────────
if "${PIPX[@]}" list --short 2>/dev/null | grep -Eq "^${PACKAGE}([[:space:]]|$)"; then
    info "ChatPulse is already installed. Upgrading it..."
    "${PIPX[@]}" upgrade "$PACKAGE"
else
    info "Installing $PACKAGE (this may take a minute)..."
    "${PIPX[@]}" install "$PACKAGE"
fi

# ── 6. Verify using pipx's actual application directory ───
CHATPULSE_BIN="$PIPX_APP_DIR/chatpulse"
if [ ! -x "$CHATPULSE_BIN" ]; then
    die "pipx completed, but the ChatPulse launcher was not found at $CHATPULSE_BIN."
fi

VERSION_OUTPUT="$("$CHATPULSE_BIN" --version 2>/dev/null || true)"

printf "\n"
ok "${BOLD}ChatPulse CLI installed!${NC}${VERSION_OUTPUT:+ ($VERSION_OUTPUT)}"
printf "\n"
printf "  Get started with:\n\n"
printf "%b\n" "    ${CYAN}chatpulse --help${NC}           show all commands"
printf "%b\n" "    ${CYAN}chatpulse auth register <username> <email>${NC}"
printf "%b\n" "    ${CYAN}chatpulse auth login <username>${NC}"
printf "%b\n" "    ${CYAN}chatpulse rooms create general${NC}"
printf "%b\n" "    ${CYAN}chatpulse chat 1${NC}            interactive chat"
printf "\n"
info "The command works in this installer process. Open a new terminal before using it from your shell."

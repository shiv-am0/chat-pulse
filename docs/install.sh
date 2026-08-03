#!/usr/bin/env bash
#
# ChatPulse CLI installer
#
# Installs the `chatpulse` CLI into its own isolated environment via pipx
# (never touching system packages). If pipx is missing it is installed safely.
#
#   curl -sSL https://chatpulse.online/install.sh | bash
#
set -euo pipefail

PACKAGE="chatpulse-cli"

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $*"; }
info() { echo -e "${CYAN}→${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
die()  { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

echo ""
echo -e "${BOLD}${CYAN}  ┌─────────────────────────────────────────┐${NC}"
echo -e "${BOLD}${CYAN}  │           ChatPulse CLI Install          │${NC}"
echo -e "${BOLD}${CYAN}  └─────────────────────────────────────────┘${NC}"
echo ""
info "Prerequisites:"
info "  • Python 3.10 or newer"
info "  • pipx (auto-installed below if missing)"
info "  • For Windows: Git Bash, or WSL for chat mode"
echo ""

# ── 1. Detect OS ───────────────────────────────────────────
UNAME="$(uname -s)"
case "$UNAME" in
    Darwin) OS="macos" ;;
    Linux)
        case "$(uname -r)" in
            *[Mm]icrosoft*) OS="wsl" ;;
            *[Mm]icrosoft-[Ww]sl2) OS="wsl" ;;
            *) OS="linux" ;;
        esac
        ;;
    MINGW*|MSYS*|CYGWIN*) OS="windows-gitbash" ;;
    *) OS="unknown" ;;
esac

# ── 2. Detect Python 3.10+ ─────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER="$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
        MAJOR="${VER%%.*}"
        MINOR="${VER#*.}"
        MINOR="${MINOR%%.*}"
        if [ -n "$VER" ] && [ "$MAJOR" -ge 3 ] && { [ "$MAJOR" -gt 3 ] || [ "$MINOR" -ge 10 ]; }; then
            PYTHON="$cmd"
            PY_VER="$VER"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    die "Python 3.10+ not found. Install it first: https://python.org/downloads"
fi
ok "Python $PY_VER found ($PYTHON)"

# ── 3. Locate pipx (or bootstrap it) ───────────────────────
PIPX_CMD=""
if command -v pipx &>/dev/null; then
    PIPX_CMD="pipx"
else
    for cand in "$HOME/.local/bin/pipx" "$HOME/.local/share/pipx-boot/bin/pipx"; do
        if [ -x "$cand" ]; then
            PIPX_CMD="$cand"
            break
        fi
    done
fi

if [ -z "$PIPX_CMD" ]; then
    info "pipx not found. Bootstrapping it safely..."
    case "$OS" in
        macos)
            if command -v brew &>/dev/null; then
                brew install pipx
            else
                "$PYTHON" -m pip install --user pipx || true
            fi
            ;;
        linux|wsl)
            if command -v apt-get &>/dev/null; then
                sudo apt-get update -y && sudo apt-get install -y pipx
            elif command -v dnf &>/dev/null; then
                sudo dnf install -y pipx
            elif command -v pacman &>/dev/null; then
                sudo pacman -S --noconfirm pipx
            else
                "$PYTHON" -m pip install --user pipx || true
            fi
            ;;
        *)
            "$PYTHON" -m pip install --user pipx || true
            ;;
    esac

    if [ -x "$HOME/.local/bin/pipx" ]; then
        PIPX_CMD="$HOME/.local/bin/pipx"
    elif command -v pipx &>/dev/null; then
        PIPX_CMD="pipx"
    elif [ ! -x "$HOME/.local/share/pipx-boot/bin/pipx" ]; then
        warn "pipx could not be installed via the package manager / pip --user."
        info "Falling back to an isolated bootstrap environment..."
        "$PYTHON" -m venv "$HOME/.local/share/pipx-boot"
        "$HOME/.local/share/pipx-boot/bin/pip" install --upgrade pip pipx
        PIPX_CMD="$HOME/.local/share/pipx-boot/bin/pipx"
    else
        PIPX_CMD="$HOME/.local/share/pipx-boot/bin/pipx"
    fi
fi

if [ -z "$PIPX_CMD" ] || [ ! -x "$PIPX_CMD" ]; then
    die "pipx is required. Install it with: $PYTHON -m pip install --user pipx  (or 'brew install pipx' on macOS), then re-run this script."
fi

ok "Using pipx: $PIPX_CMD"

# ── 4. Ensure pipx bin directory is on PATH ────────────────
"$PIPX_CMD" ensurepath >/dev/null 2>&1 || true
# Also make it available in the current shell without a restart.
if [ -d "$HOME/.local/bin" ]; then
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *) export PATH="$HOME/.local/bin:$PATH" ;;
    esac
fi

# ── 5. Install / upgrade the CLI ────────────────────────────
if command -v chatpulse &>/dev/null; then
    info "chatpulse already installed. Upgrading to the latest version..."
    "$PIPX_CMD" upgrade "$PACKAGE" || "$PIPX_CMD" install "$PACKAGE"
else
    info "Installing $PACKAGE (this may take a minute)..."
    "$PIPX_CMD" install "$PACKAGE"
fi

# ── 6. Verify ───────────────────────────────────────────────
if ! command -v chatpulse &>/dev/null; then
    warn "chatpulse is not on PATH yet."
    info "Run the following, then open a new terminal:"
    echo ""
    echo "  $PIPX_CMD ensurepath"
    echo ""
    die "chatpulse not found on PATH."
fi

VERSION="$("$PIPX_CMD" list 2>/dev/null | grep -oE "$PACKAGE [0-9.]+" | head -1 | awk '{print $2}' || true)"
[ -z "$VERSION" ] && VERSION="$(chatpulse --version 2>/dev/null | awk '{print $NF}' || true)"

echo ""
ok "$BOLD ChatPulse CLI installed!${NC} ${VERSION:+(version $VERSION)}"
echo ""
echo -e "  Get started with:"
echo ""
echo -e "    ${CYAN}chatpulse --help${NC}           show all commands"
echo -e "    ${CYAN}chatpulse auth register <username> <email>${NC}"
echo -e "    ${CYAN}chatpulse auth login <username>${NC}"
echo -e "    ${CYAN}chatpulse rooms create general${NC}"
echo -e "    ${CYAN}chatpulse chat 1${NC}            interactive chat"
echo ""
info "On Windows, interactive chat mode requires WSL (Python cannot read the terminal natively)."

#!/bin/bash
set -e

# ── Colors ──────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${BOLD}${CYAN}  ╭────────────────────────────────────╮${NC}"
echo -e "${BOLD}${CYAN}  │        ChatPulse CLI Install       │${NC}"
echo -e "${BOLD}${CYAN}  ╰────────────────────────────────────╯${NC}"
echo ""

# ── Detect Python ──────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}✗ Python 3 not found.${NC}"
    echo ""
    echo "  Install Python 3.10 or later:"
    echo "    https://python.org/downloads"
    echo ""
    echo "  Or install directly via pip once Python is available:"
    echo "    pip install chatpulse-cli"
    echo ""
    exit 1
fi

# ── Check Version ───────────────────────────────────────
RAW_VER=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo "$RAW_VER" | cut -d. -f1)
MINOR=$(echo "$RAW_VER" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
    echo -e "${RED}✗ Python 3.10+ required (found $RAW_VER)${NC}"
    echo ""
    echo "  Upgrade Python: https://python.org/downloads"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} Python $RAW_VER detected ($PYTHON)"
echo ""

# ── Determine pip command ──────────────────────────────
if $PYTHON -m pip --version &>/dev/null; then
    PIP="$PYTHON -m pip"
else
    echo -e "${RED}✗ pip not found for $PYTHON${NC}"
    echo ""
    echo "  Install pip: $PYTHON -m ensurepip --upgrade"
    echo ""
    exit 1
fi

# ── Install ─────────────────────────────────────────────
echo -e "${CYAN}⟳ Installing chatpulse-cli...${NC}"

install_ok=0

if command -v pipx &>/dev/null; then
    pipx install chatpulse-cli && install_ok=1
fi

if [ "$install_ok" -eq 0 ]; then
    INSTALL_OUTPUT=$($PIP install --user chatpulse-cli 2>&1) || true
    if echo "$INSTALL_OUTPUT" | grep -q "Successfully installed"; then
        install_ok=1
    elif echo "$INSTALL_OUTPUT" | grep -q "externally-managed-environment"; then
        echo -e "${YELLOW}⚠ System pip restricted. Trying --break-system-packages...${NC}"
        $PIP install --break-system-packages chatpulse-cli && install_ok=1
    fi
fi

if [ "$install_ok" -eq 0 ]; then
    $PIP install chatpulse-cli && install_ok=1
fi

if [ "$install_ok" -eq 0 ]; then
    echo ""
    echo -e "${RED}✗ Installation failed.${NC}"
    echo ""
    echo "  Try one of these:"
    echo "    pipx install chatpulse-cli"
    echo "    python3 -m venv venv && venv/bin/pip install chatpulse-cli"
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}✓${NC} ${BOLD}ChatPulse CLI installed!${NC}"
echo ""
echo -e "  Run ${BOLD}chatpulse --help${NC} to get started."
echo -e "  Or jump right in:"
echo ""
echo -e "    ${CYAN}chatpulse auth register username your@email.com${NC}"
echo -e "    ${CYAN}chatpulse auth login username${NC}"
echo -e "    ${CYAN}chatpulse rooms create general${NC}"
echo -e "    ${CYAN}chatpulse chat 1${NC}"
echo ""

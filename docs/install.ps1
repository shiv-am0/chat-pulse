# ChatPulse CLI installer (Windows / PowerShell)
#
# Installs the `chatpulse` CLI into an isolated environment via pipx
# (never touching system Python). Run in PowerShell:
#
#   powershell -ExecutionPolicy Bypass -c "irm https://chatpulse.online/install.ps1 | iex"
#
$ErrorActionPreference = "Stop"
$Package = "chatpulse-cli"

Write-Host ""
Write-Host "  ChatPulse CLI Install" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Prerequisites:" -ForegroundColor Cyan
Write-Host "    * Python 3.10 or newer"
Write-Host "    * pipx (auto-installed below if missing)"
Write-Host "    * Note: interactive 'chatpulse chat' requires WSL;"
Write-Host "      all other commands work natively."
Write-Host ""

# ── 1. Find Python 3.10+ ───────────────────────────────────
$PythonCmd = $null
foreach ($candidate in @("py", "python", "python3")) {
    try {
        $raw = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $parts = ($raw -split '\.')
            if ([int]$parts[0] -ge 3 -and [int]$parts[1] -ge 10) {
                $PythonCmd = $candidate
                break
            }
        }
    } catch {}
}
if (-not $PythonCmd) {
    Write-Host "  Python 3.10+ is required. Install it from https://python.org/downloads" -ForegroundColor Red
    exit 1
}
Write-Host "  Python found: $PythonCmd" -ForegroundColor Green

# ── 2. Locate or bootstrap pipx ────────────────────────────
$PipxCmd = Get-Command pipx -ErrorAction SilentlyContinue
if (-not $PipxCmd) {
    Write-Host "  pipx not found. Installing it into your user Python..." -ForegroundColor Cyan
    try {
        & $PythonCmd -m pip install --user pipx
        if ($LASTEXITCODE -ne 0) { throw "pip install pipx failed" }
    } catch {
        Write-Host "  pip is restricted. Trying winget for pipx..." -ForegroundColor Yellow
        winget install --id pypi.pipx -e --accept-source-agreements --accept-package-agreements
    }
    # Re-locate pipx (now installed to the user Python scripts dir).
    $PipxCmd = Get-Command pipx -ErrorAction SilentlyContinue
    if (-not $PipxCmd) {
        # Fallback path used by "python -m pip install --user"
        $userScripts = & $PythonCmd -m site --user-site
        $userScripts = Split-Path $userScripts -Parent
        $pipxExe = Join-Path $userScripts "Scripts\pipx.exe"
        if (Test-Path $pipxExe) { $PipxCmd = Get-Item $pipxExe }
    }
}
if (-not $PipxCmd) {
    Write-Host "  pipx is required. Install it with: $PythonCmd -m pip install --user pipx" -ForegroundColor Red
    exit 1
}
Write-Host "  Using pipx: $($PipxCmd.Path)" -ForegroundColor Green

# ── 3. Ensure pipx bin dir is on PATH ──────────────────────
& $PipxCmd.Path ensurepath | Out-Null

# ── 4. Install / upgrade the CLI ───────────────────────────
if (Get-Command chatpulse -ErrorAction SilentlyContinue) {
    Write-Host "  chatpulse already installed. Upgrading..." -ForegroundColor Cyan
    & $PipxCmd.Path upgrade $Package
    if ($LASTEXITCODE -ne 0) { & $PipxCmd.Path install $Package }
} else {
    Write-Host "  Installing $Package (this may take a minute)..." -ForegroundColor Cyan
    & $PipxCmd.Path install $Package
    if ($LASTEXITCODE -ne 0) { throw "pipx install $Package failed" }
}

# ── 5. Verify ──────────────────────────────────────────────
if (-not (Get-Command chatpulse -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "  chatpulse is not on PATH yet." -ForegroundColor Yellow
    Write-Host "  Run 'pipx ensurepath', then open a NEW terminal window." -ForegroundColor Yellow
    exit 1
}
$version = (& chatpulse --version 2>$null) -join ' '
if (-not $version) { $version = "version $Package" }
Write-Host ""
Write-Host "  ChatPulse CLI installed! ($version)" -ForegroundColor Green
Write-Host ""
Write-Host "  Get started:"
Write-Host "    chatpulse --help"
Write-Host "    chatpulse auth register <username> <email>"
Write-Host "    chatpulse auth login <username>"
Write-Host "    chatpulse rooms create general"
Write-Host "    chatpulse chat 1"
Write-Host ""
Write-Host "  Interactive chat mode requires WSL: https://learn.microsoft.com/windows/wsl/install" -ForegroundColor Cyan

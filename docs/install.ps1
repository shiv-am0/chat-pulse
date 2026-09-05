# ChatPulse CLI installer for Windows PowerShell
#
# Installs the `chatpulse` CLI into an isolated environment via pipx.
# Run in your current PowerShell session:
#
#   irm https://chatpulse.online/install.ps1 | iex

& {
    $ErrorActionPreference = "Stop"
    $Package = "chatpulse-cli"

    Write-Host ""
    Write-Host "  ChatPulse CLI Install" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Prerequisites:" -ForegroundColor Cyan
    Write-Host "    * Python 3.10 or newer"
    Write-Host "    * pipx (installed below if missing)"
    Write-Host "    * Note: interactive 'chatpulse chat' requires WSL;"
    Write-Host "      all other commands work natively."
    Write-Host ""

    # ── 1. Find Python 3.10+ ───────────────────────────────
    $PythonCmd = $null
    foreach ($Candidate in @("py", "python", "python3")) {
        try {
            & $Candidate -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $PythonCmd = $Candidate
                break
            }
        } catch {}
    }

    if (-not $PythonCmd) {
        throw "Python 3.10+ is required. Install it from https://python.org/downloads"
    }
    $PythonVersion = (& $PythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')") -join ""
    Write-Host "  Python $PythonVersion found ($PythonCmd)" -ForegroundColor Green

    # Invoke pipx either as an executable or as `python -m pipx`.
    $PipxExecutable = $null
    $PipxPrefix = @()

    function Resolve-PipxCommand {
        $Command = Get-Command pipx -ErrorAction SilentlyContinue
        if ($Command) {
            return @{
                Executable = if ($Command.Source) { $Command.Source } else { $Command.Path }
                Prefix = @()
            }
        }

        try {
            & $PythonCmd -m pipx --version *> $null
            if ($LASTEXITCODE -eq 0) {
                return @{
                    Executable = $PythonCmd
                    Prefix = @("-m", "pipx")
                }
            }
        } catch {}

        return $null
    }

    function Invoke-Pipx([string[]] $Arguments) {
        & $PipxExecutable @PipxPrefix @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "pipx command failed: $($Arguments -join ' ')"
        }
    }

    # ── 2. Locate or bootstrap pipx ────────────────────────
    $ResolvedPipx = Resolve-PipxCommand
    if (-not $ResolvedPipx) {
        Write-Host "  pipx not found. Installing it for your user account..." -ForegroundColor Cyan
        $UserInstallWorked = $false
        try {
            & $PythonCmd -m pip install --user pipx
            $UserInstallWorked = ($LASTEXITCODE -eq 0)
        } catch {}

        if ($UserInstallWorked) {
            $ResolvedPipx = Resolve-PipxCommand
        }

        if (-not $ResolvedPipx) {
            Write-Host "  Creating an isolated pipx bootstrap environment..." -ForegroundColor Yellow
            $BootstrapDir = Join-Path $env:LOCALAPPDATA "ChatPulse\pipx-bootstrap"
            & $PythonCmd -m venv $BootstrapDir
            if ($LASTEXITCODE -ne 0) { throw "Could not create the pipx bootstrap environment." }
            $BootstrapPython = Join-Path $BootstrapDir "Scripts\python.exe"
            & $BootstrapPython -m pip install --upgrade pip pipx
            if ($LASTEXITCODE -ne 0) { throw "Could not install pipx in the bootstrap environment." }
            $PipxExecutable = Join-Path $BootstrapDir "Scripts\pipx.exe"
            $PipxPrefix = @()
        }
    }

    if ($ResolvedPipx) {
        $PipxExecutable = $ResolvedPipx.Executable
        $PipxPrefix = @($ResolvedPipx.Prefix)
    }

    $PipxDescription = (@($PipxExecutable) + $PipxPrefix) -join " "
    Write-Host "  Using pipx: $PipxDescription" -ForegroundColor Green

    # ── 3. Persist and refresh the application path ────────
    Invoke-Pipx @("ensurepath") | Out-Null
    $PipxBinDir = (Invoke-Pipx @("environment", "--value", "PIPX_BIN_DIR") | Out-String).Trim()
    if (-not $PipxBinDir) {
        $PipxBinDir = Join-Path $HOME ".local\bin"
    }
    if (($env:Path -split ';') -notcontains $PipxBinDir) {
        $env:Path = "$PipxBinDir;$env:Path"
    }

    # ── 4. Install or upgrade the CLI ──────────────────────
    $InstalledPackages = (Invoke-Pipx @("list", "--short") | Out-String)
    if ($InstalledPackages -match "(?m)^$([regex]::Escape($Package))(\s|$)") {
        Write-Host "  ChatPulse is already installed. Upgrading it..." -ForegroundColor Cyan
        Invoke-Pipx @("upgrade", $Package)
    } else {
        Write-Host "  Installing $Package (this may take a minute)..." -ForegroundColor Cyan
        Invoke-Pipx @("install", $Package)
    }

    # ── 5. Verify using pipx's actual application directory
    $ChatPulseLauncher = Join-Path $PipxBinDir "chatpulse.exe"
    if (-not (Test-Path $ChatPulseLauncher)) {
        $ChatPulseLauncher = Join-Path $PipxBinDir "chatpulse"
    }
    if (-not (Test-Path $ChatPulseLauncher)) {
        throw "pipx completed, but the ChatPulse launcher was not found in $PipxBinDir."
    }

    $Version = (& $ChatPulseLauncher --version 2>$null) -join " "
    Write-Host ""
    Write-Host "  ChatPulse CLI installed! ($Version)" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Get started:"
    Write-Host "    chatpulse --help"
    Write-Host "    chatpulse auth register <username> <email>"
    Write-Host "    chatpulse auth login <username>"
    Write-Host "    chatpulse rooms create general"
    Write-Host "    chatpulse chat 1"
    Write-Host ""
    Write-Host "  The command now works in this PowerShell session and in new terminals." -ForegroundColor Cyan
    Write-Host "  Interactive chat mode requires WSL: https://learn.microsoft.com/windows/wsl/install" -ForegroundColor Cyan
}

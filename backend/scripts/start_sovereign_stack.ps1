param(
    [switch]$Restart,
    [switch]$WithWatchdog
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$logs = Join-Path $root "relatorios_melhorias\logs"
$errorLogs = Join-Path $root "relatorios_melhorias\logs_erros"
New-Item -ItemType Directory -Force -Path $logs, $errorLogs | Out-Null

if ($Restart) {
    $targets = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -in @("python.exe", "node.exe") -and (
            $_.CommandLine -like "*uvicorn main:app*" -or
            $_.CommandLine -like "*celery -A tasks worker*" -or
            $_.CommandLine -like "*next start*"
        )
    }
    foreach ($target in $targets) {
        Stop-Process -Id $target.ProcessId -Force -ErrorAction SilentlyContinue
    }
    $portOwners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -in 3000, 8000 } |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($portOwner in $portOwners) {
        Stop-Process -Id $portOwner -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

& (Join-Path $backend "scripts\start_local_ai.ps1")

$python = (Get-Command python).Source
$apiListening = Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
if (-not $apiListening) {
    Start-Process `
        -FilePath $python `
        -ArgumentList @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $backend `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logs "sovereign_api_stdout.log") `
        -RedirectStandardError (Join-Path $errorLogs "sovereign_api_stderr.log")
}

$workers = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "python.exe" -and
    $_.CommandLine -like "*celery -A tasks worker*"
} | Sort-Object CreationDate)
if ($workers.Count -gt 1) {
    $workers | Select-Object -Skip 1 | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
    $workers = @($workers | Select-Object -First 1)
}
if ($workers.Count -eq 0) {
    Start-Process `
        -FilePath $python `
        -ArgumentList @(
            "-m", "celery", "-A", "tasks", "worker",
            "--pool=solo", "--loglevel=INFO",
            "--queues=celery,processing,reports,notifications,maintenance",
            "--hostname=lex-sovereign@%h"
        ) `
        -WorkingDirectory $backend `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logs "sovereign_worker_stdout.log") `
        -RedirectStandardError (Join-Path $errorLogs "sovereign_worker_stderr.log")
}

$frontendListening = Get-NetTCPConnection -State Listen -LocalPort 3000 -ErrorAction SilentlyContinue
if (-not $frontendListening) {
    Start-Process `
        -FilePath (Get-Command npm.cmd).Source `
        -ArgumentList @("run", "start", "--", "--hostname", "127.0.0.1", "--port", "3000") `
        -WorkingDirectory $frontend `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logs "sovereign_frontend_stdout.log") `
        -RedirectStandardError (Join-Path $errorLogs "sovereign_frontend_stderr.log")
}

if ($WithWatchdog) {
    $watchdog = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -like "*local_ai_watchdog.ps1*"
    }
    if (-not $watchdog) {
        Start-Process `
            -FilePath "powershell.exe" `
            -ArgumentList @(
                "-ExecutionPolicy", "Bypass",
                "-File", (Join-Path $backend "scripts\local_ai_watchdog.ps1")
            ) `
            -WorkingDirectory $backend `
            -WindowStyle Hidden
    }
}

$deadline = (Get-Date).AddMinutes(2)
do {
    Start-Sleep -Seconds 2
    try {
        $api = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health/ready" -TimeoutSec 3
        $ai = Invoke-RestMethod -Uri "http://127.0.0.1:8000/ai/sovereign/status" -TimeoutSec 10
        $ready = $api.status -eq "ready" -and $ai.status -eq "healthy"
    } catch {
        $ready = $false
    }
} until ($ready -or (Get-Date) -ge $deadline)

if (-not $ready) {
    throw "Stack iniciou parcialmente; verifique os logs em relatorios_melhorias."
}

[PSCustomObject]@{
    API = $api.status
    AI = $ai.status
    Sources = $ai.knowledge.sources
    Chunks = $ai.knowledge.chunks
    FastModel = $ai.models.fast
    QuickModel = $ai.models.quick
    BalancedModel = $ai.models.balanced
    DeepModel = $ai.models.deep
} | Format-List

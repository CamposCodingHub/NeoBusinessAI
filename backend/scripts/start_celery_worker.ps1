param(
    [switch]$Visible
)

$backendRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $backendRoot
$logsRoot = Join-Path $repoRoot "relatorios_melhorias\logs"
New-Item -ItemType Directory -Path $logsRoot -Force | Out-Null

$existingWorker = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -like "*celery* -A tasks worker*"
    } |
    Select-Object -First 1

if ($existingWorker) {
    Write-Output "Celery worker ja esta em execucao (PID $($existingWorker.ProcessId))."
    exit 0
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$stdout = Join-Path $logsRoot "celery_worker_${stamp}_stdout.log"
$stderr = Join-Path $logsRoot "celery_worker_${stamp}_stderr.log"
$queues = "celery,processing,reports,notifications,maintenance"
$arguments = @(
    "-m", "celery",
    "-A", "tasks",
    "worker",
    "--pool=solo",
    "--loglevel=INFO",
    "--queues=$queues",
    "--hostname=jurisflow-worker@%h"
)

$startParams = @{
    FilePath = "python"
    ArgumentList = $arguments
    WorkingDirectory = $backendRoot
    RedirectStandardOutput = $stdout
    RedirectStandardError = $stderr
    PassThru = $true
}

if (-not $Visible) {
    $startParams.WindowStyle = "Hidden"
}

$process = Start-Process @startParams
Start-Sleep -Seconds 4

if ($process.HasExited) {
    throw "Celery worker encerrou durante a inicializacao. Consulte $stderr"
}

Write-Output "Celery worker iniciado (PID $($process.Id)). Logs: $stdout"

param(
    [int]$IntervalSeconds = 15,
    [int]$FailureThreshold = 3
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$logs = Join-Path $root "relatorios_melhorias\logs"
$errorLogs = Join-Path $root "relatorios_melhorias\logs_erros"
New-Item -ItemType Directory -Force -Path $logs, $errorLogs | Out-Null
$watchdogLog = Join-Path $logs "local_ai_watchdog.log"
$failures = 0

while ($true) {
    try {
        $health = Invoke-RestMethod `
            -Uri "http://127.0.0.1:11434/api/tags" `
            -TimeoutSec 5
        $failures = 0
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Add-Content $watchdogLog "$timestamp healthy models=$($health.models.Count)"
    } catch {
        $failures++
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Add-Content $watchdogLog "$timestamp failure=$failures error=$($_.Exception.Message)"
        if ($failures -ge $FailureThreshold) {
            Get-Process ollama -ErrorAction SilentlyContinue |
                Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            Start-Process `
                -FilePath (Get-Command ollama).Source `
                -ArgumentList @("serve") `
                -WindowStyle Hidden `
                -RedirectStandardOutput (Join-Path $logs "ollama_stdout.log") `
                -RedirectStandardError (Join-Path $errorLogs "ollama_stderr.log")
            $failures = 0
        }
    }
    Start-Sleep -Seconds $IntervalSeconds
}

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$targets = Get-CimInstance Win32_Process | Where-Object {
    ($_.CommandLine -like "*$root*" -and (
        $_.CommandLine -like "*uvicorn main:app*" -or
        $_.CommandLine -like "*celery -A tasks worker*" -or
        $_.CommandLine -like "*next start*" -or
        $_.CommandLine -like "*local_ai_watchdog.ps1*"
    )) -or (
        $_.Name -eq "ollama.exe" -and $_.CommandLine -like "*serve*"
    )
}
foreach ($target in $targets) {
    Stop-Process -Id $target.ProcessId -Force -ErrorAction SilentlyContinue
}

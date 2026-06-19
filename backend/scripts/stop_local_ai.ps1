$processes = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "ollama.exe" -and $_.CommandLine -like "*serve*"
}
foreach ($process in $processes) {
    Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
}

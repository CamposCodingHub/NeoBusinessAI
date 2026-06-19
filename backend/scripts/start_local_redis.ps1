$ErrorActionPreference = "Stop"

$redisServer = Get-ChildItem `
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" `
    -Recurse `
    -Filter redis-server.exe `
    -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName

if (-not $redisServer) {
    throw "redis-server.exe nao encontrado. Instale taizod1024.redis-windows-fork pelo WinGet."
}

$runtimeDir = Join-Path (Split-Path $PSScriptRoot -Parent) "runtime\redis"
New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

$listening = netstat -ano | Select-String ":6379\s+.*LISTENING"
if (-not $listening) {
    Start-Process `
        -FilePath $redisServer `
        -ArgumentList @(
            "--bind", "127.0.0.1",
            "--port", "6379",
            "--dir", $runtimeDir,
            "--appendonly", "yes",
            "--appenddirname", "appendonlydir",
            "--dbfilename", "dump.rdb",
            "--logfile", (Join-Path $runtimeDir "redis.log")
        ) `
        -WorkingDirectory $runtimeDir `
        -WindowStyle Hidden | Out-Null
}

for ($attempt = 0; $attempt -lt 20; $attempt++) {
    if (netstat -ano | Select-String ":6379\s+.*LISTENING") {
        Write-Output "Redis local pronto em 127.0.0.1:6379"
        exit 0
    }
    Start-Sleep -Milliseconds 500
}

throw "Redis local nao iniciou dentro do prazo."

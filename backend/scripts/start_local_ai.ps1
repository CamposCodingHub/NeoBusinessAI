param(
    [switch]$RebuildModels
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$logs = Join-Path $root "relatorios_melhorias\logs"
$errorLogs = Join-Path $root "relatorios_melhorias\logs_erros"
New-Item -ItemType Directory -Force -Path $logs, $errorLogs | Out-Null

$ollama = Get-Command ollama -ErrorAction Stop
$listening = Get-NetTCPConnection -State Listen -LocalPort 11434 -ErrorAction SilentlyContinue
if (-not $listening) {
    Start-Process `
        -FilePath $ollama.Source `
        -ArgumentList @("serve") `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logs "ollama_stdout.log") `
        -RedirectStandardError (Join-Path $errorLogs "ollama_stderr.log")
}

$deadline = (Get-Date).AddSeconds(30)
do {
    Start-Sleep -Seconds 1
    try {
        $null = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2
        $ready = $true
    } catch {
        $ready = $false
    }
} until ($ready -or (Get-Date) -ge $deadline)

if (-not $ready) {
    throw "Ollama nao respondeu na porta 11434."
}

$installedModels = @(
    (& $ollama.Source list | Select-Object -Skip 1) |
        ForEach-Object { ($_ -split "\s+")[0] }
)

$modelfile = Join-Path $root "backend\runtime\ollama\Modelfile.lex-juridica"
if ($RebuildModels -or "lex-juridica:14b" -notin $installedModels) {
    & $ollama.Source create "lex-juridica:14b" -f $modelfile
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar lex-juridica:14b."
    }
}

$rapidModelfile = Join-Path $root "backend\runtime\ollama\Modelfile.lex-juridica-rapida"
if ($RebuildModels -or "lex-juridica-rapida:3b" -notin $installedModels) {
    & $ollama.Source create "lex-juridica-rapida:3b" -f $rapidModelfile
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar lex-juridica-rapida:3b."
    }
}

$instantModelfile = Join-Path $root "backend\runtime\ollama\Modelfile.lex-juridica-instant"
if ($RebuildModels -or "lex-juridica-instant:1.5b" -notin $installedModels) {
    & $ollama.Source create "lex-juridica-instant:1.5b" -f $instantModelfile
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar lex-juridica-instant:1.5b."
    }
}

$warmupPayload = @{
    model = "lex-juridica-instant:1.5b"
    prompt = "OK"
    stream = $false
    keep_alive = "15m"
    options = @{
        num_ctx = 4096
        num_predict = 1
        temperature = 0
    }
} | ConvertTo-Json -Depth 4
Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:11434/api/generate" `
    -ContentType "application/json" `
    -Body $warmupPayload `
    -TimeoutSec 180 | Out-Null

$embeddingWarmupPayload = @{
    model = "nomic-embed-text"
    input = "aquecimento da busca juridica local"
    keep_alive = "15m"
} | ConvertTo-Json
Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:11434/api/embed" `
    -ContentType "application/json" `
    -Body $embeddingWarmupPayload `
    -TimeoutSec 120 | Out-Null

& $ollama.Source list

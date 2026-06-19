$backendRoot = Split-Path -Parent $PSScriptRoot
Push-Location $backendRoot

try {
    python -m pytest -q `
        --cov=. `
        --cov-config=.coveragerc `
        --cov-report=term-missing `
        --cov-report=html:htmlcov `
        --cov-fail-under=40

    if ($LASTEXITCODE -ne 0) {
        throw "Quality gate falhou com codigo $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

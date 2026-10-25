$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Instale Python 3.11 ou superior e habilite Add python.exe to PATH.'
}
python app.py --seed

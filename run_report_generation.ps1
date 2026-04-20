$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $scriptDir

uv run python .\report_gen.py

Write-Host ""
Write-Host "Report generation completed."
Read-Host "Press Enter to close"

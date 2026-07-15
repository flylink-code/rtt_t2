$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$VenvPython = Join-Path $RootDir '.venv\Scripts\python.exe'
$VenvPip = Join-Path $RootDir '.venv\Scripts\pip.exe'

if (-not (Test-Path $VenvPython)) {
    python -m venv .venv
}

$env:PYQTGRAPH_QT_LIB = 'PySide6'

& $VenvPip install -U pip
& $VenvPip install -r requirements.txt pyinstaller

if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }

& (Join-Path $RootDir '.venv\Scripts\pyinstaller.exe') (Join-Path $RootDir 'rtt_t2.spec') --noconfirm

$Version = if ($env:RTT_VERSION) { $env:RTT_VERSION } else { 'v1.0.4' }
$Archive = Join-Path $RootDir "dist\rtt_t2-$Version-windows-x64.zip"
if (Test-Path $Archive) { Remove-Item -Force $Archive }
$DistFolder = Join-Path $RootDir 'dist\rtt_t2'
if (-not (Test-Path $DistFolder)) {
    throw "Build output not found: $DistFolder"
}
Compress-Archive -Path (Join-Path $DistFolder '*') -DestinationPath $Archive
Write-Host "Created $Archive"

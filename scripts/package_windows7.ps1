param(
    [string]$Version = $env:RTT_VERSION
)

$ErrorActionPreference = 'Stop'
$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$VenvDir = Join-Path $RootDir '.venv-win7'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'

if (-not (Test-Path $VenvPython)) {
    if ($env:PYTHON38) {
        & $env:PYTHON38 -m venv $VenvDir
    } else {
        py -3.8 -m venv $VenvDir
    }
}

$env:PYQTGRAPH_QT_LIB = 'PySide2'
$env:RTT_QT_BINDING = 'PySide2'
& $VenvPython -m pip install -r requirements-win7.txt

if (Test-Path build-win7) { Remove-Item -Recurse -Force build-win7 }
if (Test-Path dist-win7) { Remove-Item -Recurse -Force dist-win7 }
& $VenvPython -m PyInstaller rtt_t2.spec --noconfirm --workpath build-win7 --distpath dist-win7

if (-not $Version) { $Version = 'v1.0.7' }
$Archive = Join-Path $RootDir "dist-win7\rtt_t2-$Version-windows7-x64.zip"
$DistFolder = Join-Path $RootDir 'dist-win7\rtt_t2'
Compress-Archive -Path (Join-Path $DistFolder '*') -DestinationPath $Archive
Write-Host "Created $Archive"

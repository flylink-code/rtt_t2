$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$VersionTag = if ($env:RTT_VERSION) { $env:RTT_VERSION } else { 'v1.0.7' }
$Version = $VersionTag.TrimStart('v', 'V')

$DistFolder = if ($env:RTT_DIST_DIR) { $env:RTT_DIST_DIR } else { Join-Path $RootDir 'dist\rtt_t2' }
$PackageSuffix = if ($env:RTT_PACKAGE_SUFFIX) { $env:RTT_PACKAGE_SUFFIX } else { '' }
if (-not (Test-Path $DistFolder)) {
    throw "PyInstaller output not found: $DistFolder"
}

$InnoCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe')
)
$IsccExe = $null
foreach ($candidate in $InnoCandidates) {
    if (Test-Path $candidate) {
        $IsccExe = $candidate
        break
    }
}
if (-not $IsccExe) {
    throw 'Inno Setup not found. Install Inno Setup 6 or run: choco install innosetup -y'
}

$IssFile = Join-Path $RootDir 'installer\rtt_t2.iss'
$SetupPath = Join-Path $RootDir "dist\rtt_t2-$VersionTag-windows$PackageSuffix-x64-setup.exe"

& $IsccExe $IssFile "/DMyAppVersion=$Version" "/DMyAppReleaseTag=$VersionTag" "/DMyAppOutputSuffix=$PackageSuffix" "/DMyAppDistDir=$DistFolder"

if (-not (Test-Path $SetupPath)) {
    throw "Setup EXE was not created: $SetupPath"
}

Write-Host "Created $SetupPath"

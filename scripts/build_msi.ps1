$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$VersionTag = if ($env:RTT_VERSION) { $env:RTT_VERSION } else { 'v1.0.5' }
$Version = $VersionTag.TrimStart('v', 'V')
$parts = $Version.Split('.')
while ($parts.Count -lt 3) {
    $parts += '0'
}
$ProductVersion = ($parts[0..2] -join '.') + '.0'

$DistFolder = Resolve-Path (Join-Path $RootDir 'dist\rtt_t2')
$SourceDir = "$DistFolder\"

$WixCandidates = @(
    (Join-Path $env:ProgramFiles 'WiX Toolset v3.14\bin'),
    (Join-Path ${env:ProgramFiles(x86)} 'WiX Toolset v3.14\bin'),
    (Join-Path ${env:ProgramFiles(x86)} 'WiX Toolset v3.11\bin')
)
if ($env:WIX) {
    $WixCandidates = @((Join-Path $env:WIX 'bin')) + $WixCandidates
}

$WixBin = $null
foreach ($candidate in $WixCandidates) {
    if (Test-Path (Join-Path $candidate 'heat.exe')) {
        $WixBin = $candidate
        break
    }
}
if (-not $WixBin) {
    throw 'WiX Toolset not found. Install WiX 3.11+ or run: choco install wixtoolset -y'
}

$HeatExe = Join-Path $WixBin 'heat.exe'
$CandleExe = Join-Path $WixBin 'candle.exe'
$LightExe = Join-Path $WixBin 'light.exe'

$InstallerDir = Join-Path $RootDir 'installer'
$FilesWxs = Join-Path $InstallerDir 'Files.wxs'
$ProductWxs = Join-Path $InstallerDir 'Product.wxs'
$ObjDir = Join-Path $InstallerDir 'obj'
$MsiName = "rtt_t2-$VersionTag-windows-x64.msi"
$MsiPath = Join-Path $RootDir "dist\$MsiName"

if (Test-Path $FilesWxs) {
    Remove-Item -Force $FilesWxs
}
if (Test-Path $ObjDir) {
    Remove-Item -Recurse -Force $ObjDir
}
New-Item -ItemType Directory -Force -Path $ObjDir | Out-Null

Write-Host "Using WiX from $WixBin"
Write-Host "ProductVersion=$ProductVersion SourceDir=$SourceDir"

& $HeatExe dir $DistFolder `
    -cg AppFiles `
    -dr INSTALLFOLDER `
    -var var.SourceDir `
    -platform x64 `
    -srd `
    -ag `
    -sfrag `
    -out $FilesWxs

& $CandleExe -nologo -arch x64 `
    -dProductVersion=$ProductVersion `
    "-dSourceDir=$SourceDir" `
    -out "$ObjDir\" `
    $ProductWxs $FilesWxs

& $LightExe -nologo -ext WixUIExtension -sval `
    -out $MsiPath `
    (Join-Path $ObjDir 'Product.wixobj') `
    (Join-Path $ObjDir 'Files.wixobj')

if (-not (Test-Path $MsiPath)) {
    throw "MSI was not created: $MsiPath"
}

Write-Host "Created $MsiPath"

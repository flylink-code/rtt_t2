$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$VersionTag = if ($env:RTT_VERSION) { $env:RTT_VERSION } else { 'v1.0.2' }
$Version = $VersionTag.TrimStart('v', 'V')
$parts = $Version.Split('.')
while ($parts.Count -lt 3) {
    $parts += '0'
}
$ProductVersion = ($parts[0..2] -join '.') + '.0'

$DistFolder = Join-Path $RootDir 'dist\rtt_t2'
if (-not (Test-Path $DistFolder)) {
    throw "PyInstaller output not found: $DistFolder"
}

$InstallerDir = Join-Path $RootDir 'installer'
$FilesWxs = Join-Path $InstallerDir 'Files.wxs'
$ProductWxs = Join-Path $InstallerDir 'Product.wxs'
$MsiName = "rtt_t2-$VersionTag-windows-x64.msi"
$MsiPath = Join-Path $RootDir "dist\$MsiName"

wix extension add -g WixToolset.Heat.wixext WixToolset.UI.wixext | Out-Null

if (Test-Path $FilesWxs) {
    Remove-Item -Force $FilesWxs
}

wix heat dir $DistFolder `
    -cg AppFiles `
    -dr INSTALLFOLDER `
    -var var.SourceDir `
    -srd `
    -ag `
    -sfrag `
    -out $FilesWxs

wix build $ProductWxs $FilesWxs `
    -ext WixToolset.Heat.wixext `
    -ext WixToolset.UI.wixext `
    -arch x64 `
    -d ProductVersion=$ProductVersion `
    -d SourceDir=$DistFolder `
    -o $MsiPath

Write-Host "Created $MsiPath"

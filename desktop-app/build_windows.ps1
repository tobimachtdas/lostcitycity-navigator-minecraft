param([switch]$PortableOnly)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Run($Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed ($LASTEXITCODE)" }
}
if ($env:OS -ne 'Windows_NT') { throw 'Windows x64 is required for this build.' }
Run py @('-3.12','-m','venv','.build-venv')
$python = Join-Path $PWD '.build-venv\Scripts\python.exe'
Run $python @('-m','pip','install','pyinstaller==6.20.0')
New-Item -ItemType Directory -Force release,src-tauri/binaries | Out-Null
Run $python @('-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed','--name','LostCityFinder_Portable','--icon','src-tauri/icons/icon.ico','--distpath','release','desktop/app.py')
if (!$PortableOnly) {
    Run $python @('-m','PyInstaller','--noconfirm','--clean','--onefile','--console','--name','lcf-backend','--add-data','frontend;frontend','--distpath','build-sidecar','desktop/webapp.py')
    Copy-Item build-sidecar/lcf-backend.exe src-tauri/binaries/lcf-backend-x86_64-pc-windows-msvc.exe -Force
    Run cargo @('tauri','build','--target','x86_64-pc-windows-msvc','--bundles','nsis')
    $setup = Get-ChildItem src-tauri/target/x86_64-pc-windows-msvc/release/bundle/nsis -Filter '*setup.exe' | Select-Object -First 1
    if (!$setup) { throw 'Installer not found' }
    Copy-Item $setup.FullName release/LostCityFinder_Setup.exe -Force
}
Get-ChildItem release -Filter '*.exe' | Get-FileHash -Algorithm SHA256 | Format-Table
Write-Host 'Build completed. See release folder.'

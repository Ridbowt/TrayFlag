<#
    File: updater.ps1
    Version: 0.1.1
    Author: Ridbowt
    Description: Downloads and installs the latest version of TrayFlag.
#>

# --- Beautiful Title ---
Write-Host "=========================" -ForegroundColor Green
Write-Host "   TrayFlag Auto-Updater   " -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# --- ENCODING ---
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "DO NOT CLOSE THIS WINDOW." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# --- URL to Check ---
$GistRawUrl = "https://raw.githubusercontent.com/Ridbowt/TrayFlag/refs/heads/main/TrayFlagLastVersion.txt"

try {
    # --- PowerShell Version Check ---
    if ($PSVersionTable.PSVersion.Major -lt 7) {
        Write-Host "WARNING: It is recommended to run the update using PowerShell 7 for proper operation. Currently, PowerShell $($PSVersionTable.PSVersion) is being used. The script will attempt to update TrayFlag, but some limitations may apply." -ForegroundColor Yellow
    }

    # --- Step 1: Find TrayFlag ---
    Write-Host "[1/5] Finding TrayFlag process..." -ForegroundColor Cyan
    $trayflagProcess = Get-Process -Name "TrayFlag" -ErrorAction Stop
    if (-not $trayflagProcess) {
        throw "TrayFlag is not running. Please start it before checking for updates."
    }
    $trayflagDir = Split-Path $trayflagProcess.Path
    $iniPath = Join-Path $trayflagDir "TrayFlag.ini"

    # --- Step 2: Check Version ---
    Write-Host "[2/5] Checking for new version..." -ForegroundColor Cyan
    
    $iniContent = Get-Content $iniPath
    $currentVersionLine = $iniContent | Select-String -Pattern "version="
    $currentVersion = ($currentVersionLine.Line -replace "version=", "").Trim()

    $headers = @{ "Cache-Control" = "no-cache"; "Pragma" = "no-cache" }
    if ($PSVersionTable.PSVersion.Major -ge 7) {
        $gistContent = (Invoke-WebRequest -Uri $GistRawUrl -Headers $headers).Content
    } else {
        $gistContent = (Invoke-WebRequest -Uri $GistRawUrl -Headers $headers -UseBasicParsing).Content
    }
    $gistLines = $gistContent -split "`r?`n"

    $latestVersionLine = $gistLines | Where-Object { $_ -match "^VER[:=]" } | Select-Object -First 1
    if (-not $latestVersionLine) { throw "Cannot find version info in Gist." }
    Write-Host "Latest version line raw:" $latestVersionLine
    $latestVersion = ($latestVersionLine -replace "VER[:=]", "").Trim()
    if (-not $latestVersion) { throw "Could not determine latest version. Check the Gist content." }

    $zipUrlLine = $gistLines | Where-Object { $_ -match "^LINK[:=]" } | Select-Object -First 1
    if (-not $zipUrlLine) { throw "Cannot find download link in Gist." }
    $zipUrl = ($zipUrlLine -replace "LINK[:=]", "").Trim()

    $hashLine = $gistLines | Where-Object { $_ -match "^HASH[:=]" } | Select-Object -First 1
    if (-not $hashLine) { throw "Cannot find HASH info in Gist." }
    $hashFromGist = ($hashLine -replace "HASH[:=]", "").Trim()

    Write-Host "Current version: $currentVersion, Latest version: $latestVersion"
    Write-Host "Download URL: $zipUrl"
    Write-Host "Expected SHA256: $hashFromGist"

    if ([version]$latestVersion -le [version]$currentVersion) {
        Write-Host ""
        Write-Host "You already have the latest version!" -ForegroundColor Green
        Start-Sleep -Seconds 3
        exit
    }

    Write-Host "New version available!" -ForegroundColor Yellow
    
    $choice = Read-Host "Do you want to install this update now? (y/n)"
    if ($choice -ne 'y') {
        Write-Host "Update cancelled by user." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        exit
    }

    # --- Step 3: Kill the process ---
    Write-Host "[3/5] Closing TrayFlag..." -ForegroundColor Cyan
    Stop-Process -Name "TrayFlag" -Force
    Start-Sleep -Seconds 2

    # --- Step 4: Download the update ---
    Write-Host "[4/5] Downloading and installing update..." -ForegroundColor Cyan
    $zipPath = Join-Path $trayflagDir "TrayFlag_update.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath

    # --- SHA256 Check ---
    $sha256 = Get-FileHash -Algorithm SHA256 $zipPath
    if ($sha256.Hash -ne $hashFromGist) {
        throw "Downloaded file hash mismatch! Update aborted."
    }

    # --- Clear old files except TrayFlag.ini ---
    Get-ChildItem -Path $trayflagDir -Recurse | Where-Object {
        $_.FullName -ne $iniPath
    } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    # --- Extract and copy new files ---
    $tempDir = Join-Path $trayflagDir "update_temp"
    if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
    New-Item -ItemType Directory -Path $tempDir -Force

    Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force

    $unpackedDir = Get-ChildItem -Path $tempDir | Where-Object { $_.PSIsContainer } | Select-Object -First 1
    $sourceDir = $unpackedDir.FullName

    Get-ChildItem -Path $sourceDir | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $trayflagDir -Recurse -Force
    }

    # --- Cleanup temporary files ---
    Remove-Item $zipPath -Force
    Remove-Item $tempDir -Recurse -Force

    # --- Step 5: Launch the new version ---
    Write-Host "[5/5] Starting new version..." -ForegroundColor Cyan
    Start-Process (Join-Path $trayflagDir "TrayFlag.exe")

    Write-Host ""
    Write-Host "Update successful! This window will close in 5 seconds." -ForegroundColor Green
    Start-Sleep -Seconds 5

} catch {
    Write-Host ""
    Write-Host "AN ERROR OCCURRED:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
}

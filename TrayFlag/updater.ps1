<#
    File: updater.ps1
    Version: 0.2.0
    Author: Ridbowt
    Description: Downloads and installs the latest version of TrayFlag with clean file replacement.
    Features:
      - Full cleanup of old files (preserves only TrayFlag.ini)
      - Temp files retained after success for rollback capability
      - Self-updating (updater.ps1 replaces itself from ZIP)
      - No log files (console output only)
      - Enhanced error handling and validation
#>

# ============================================================================
# --- HEADER & UI ---
# ============================================================================

Write-Host "=========================" -ForegroundColor Green
Write-Host "   TrayFlag Auto-Updater   " -ForegroundColor Green
Write-Host "   Version 0.2.0           " -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# Set UTF-8 encoding for proper character display
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "DO NOT CLOSE THIS WINDOW." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# ============================================================================
# --- CONFIGURATION ---
# ============================================================================

# GitHub raw URL for version info (NO trailing spaces!)
$VersionUrl = "https://raw.githubusercontent.com/Ridbowt/TrayFlag/refs/heads/main/TrayFlagLastVersion.txt"

# Minimum required free space (100 MB)
$MinFreeSpaceMB = 100

# Network timeout (seconds)
$NetworkTimeout = 30

# ============================================================================
# --- HELPER FUNCTIONS ---
# ============================================================================

function Get-IniVersion {
    param([string]$Path)
    # Parse version from INI file reliably
    if (Test-Path $Path) {
        try {
            $content = Get-Content $Path -Raw -ErrorAction Stop
            $match = [regex]::Match($content, 'version\s*=\s*([0-9.]+)')
            if ($match.Success) {
                return $match.Groups[1].Value
            }
        } catch {
            Write-Host "  Warning: Could not read INI file" -ForegroundColor Yellow
        }
    }
    return "0.0.0"
}

function Remove_OldTempFiles {
    param([string]$Dir)
    # Remove temp files from PREVIOUS update attempt (if any)
    $oldTemp = Join-Path $Dir "__update_temp"
    $oldZip = Join-Path $Dir "TrayFlag_update.zip"

    if (Test-Path $oldTemp) {
        try {
            Remove-Item $oldTemp -Recurse -Force -ErrorAction Stop
            Write-Host "[CLEANUP] Removed old __update_temp folder" -ForegroundColor Gray
        } catch {
            Write-Host "[CLEANUP] Warning: Could not remove old __update_temp folder" -ForegroundColor Yellow
        }
    }
    if (Test-Path $oldZip) {
        try {
            Remove-Item $oldZip -Force -ErrorAction Stop
            Write-Host "[CLEANUP] Removed old update ZIP" -ForegroundColor Gray
        } catch {
            Write-Host "[CLEANUP] Warning: Could not remove old update ZIP" -ForegroundColor Yellow
        }
    }
}

function Test-WritePermission {
    param([string]$Path)
    # Check if we have write permission to directory
    try {
        $testFile = Join-Path $Path ".permission_test"
        [System.IO.File]::Create($testFile).Close()
        Remove-Item $testFile -Force
        return $true
    } catch {
        return $false
    }
}

function Get-DirectoryFreeSpaceMB {
    param([string]$Path)
    # Get free disk space in MB
    try {
        $drive = [System.IO.DriveInfo]::new((Get-Item $Path).Root.Name)
        return [math]::Round($drive.AvailableFreeSpace / 1MB, 2)
    } catch {
        return 0
    }
}

function Test-FileLocked {
    param([string]$Path)
    # Check if file is locked by another process
    try {
        $file = [System.IO.File]::Open($Path, 'Open', 'Read', 'None')
        $file.Close()
        return $false
    } catch {
        return $true
    }
}

# ============================================================================
# --- MAIN UPDATE LOGIC ---
# ============================================================================

try {
    # --- PowerShell Version Check ---
    if ($PSVersionTable.PSVersion.Major -lt 7) {
        Write-Host "WARNING: PowerShell 7+ is recommended. Currently using PS $($PSVersionTable.PSVersion)." -ForegroundColor Yellow
        Write-Host "The update will proceed, but some features may be limited." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }

    # --- Step 1: Find TrayFlag Process ---
    Write-Host ""
    Write-Host "[1/8] Finding TrayFlag process..." -ForegroundColor Cyan

    try {
        $trayflagProcess = Get-Process -Name "TrayFlag" -ErrorAction Stop
    } catch {
        throw "TrayFlag is not running. Please start TrayFlag before checking for updates."
    }

    try {
        $trayflagDir = Split-Path $trayflagProcess.Path -ErrorAction Stop
    } catch {
        throw "Could not determine TrayFlag installation directory."
    }

    $iniPath = Join-Path $trayflagDir "TrayFlag.ini"
    Write-Host "  Installation directory: $trayflagDir" -ForegroundColor Gray

    # --- Check Write Permissions ---
    Write-Host "  Checking write permissions..." -ForegroundColor Gray
    if (-not (Test-WritePermission -Path $trayflagDir)) {
        throw "No write permission to installation directory. Run PowerShell as Administrator."
    }
    Write-Host "  Write permission: OK" -ForegroundColor Green

    # --- Check Free Disk Space ---
    Write-Host "  Checking free disk space..." -ForegroundColor Gray
    $freeSpace = Get-DirectoryFreeSpaceMB -Path $trayflagDir
    Write-Host "  Free space: ${freeSpace} MB" -ForegroundColor Gray
    if ($freeSpace -lt $MinFreeSpaceMB) {
        throw "Insufficient disk space. Required: ${MinFreeSpaceMB} MB, Available: ${freeSpace} MB"
    }

    # --- Step 2: Check Current Version ---
    Write-Host ""
    Write-Host "[2/8] Checking current version..." -ForegroundColor Cyan
    $currentVersion = Get-IniVersion -Path $iniPath
    Write-Host "  Current version: $currentVersion" -ForegroundColor Gray

    # --- Download Version Info ---
    Write-Host "  Downloading version info from GitHub..." -ForegroundColor Gray
    $headers = @{ "Cache-Control" = "no-cache"; "Pragma" = "no-cache" }

    try {
        if ($PSVersionTable.PSVersion.Major -ge 7) {
            $versionContent = (Invoke-WebRequest -Uri $VersionUrl -Headers $headers -TimeoutSec $NetworkTimeout).Content
        } else {
            $versionContent = (Invoke-WebRequest -Uri $VersionUrl -Headers $headers -UseBasicParsing -TimeoutSec $NetworkTimeout).Content
        }
    } catch {
        throw "Failed to download version info. Check your internet connection.`n  Error: $($_.Exception.Message)"
    }

    $versionLines = $versionContent -split "`r?`n"

    # Parse version info with validation
    $latestVersion = ($versionLines | Where-Object { $_ -match "^VER[:=]" } | Select-Object -First 1) -replace "VER[:=]", ""
    $zipUrl = ($versionLines | Where-Object { $_ -match "^LINK[:=]" } | Select-Object -First 1) -replace "LINK[:=]", ""
    $expectedHash = ($versionLines | Where-Object { $_ -match "^HASH[:=]" } | Select-Object -First 1) -replace "HASH[:=]", ""

    # Trim whitespace from all values
    $latestVersion = $latestVersion.Trim()
    $zipUrl = $zipUrl.Trim()
    $expectedHash = $expectedHash.Trim()

    # --- Validate parsed data ---
    if (-not $latestVersion) {
        throw "Could not find version info in GitHub file. File format may have changed."
    }
    if (-not $zipUrl) {
        throw "Could not find download link in GitHub file. File format may have changed."
    }
    if (-not $expectedHash) {
        throw "Could not find SHA256 hash in GitHub file. Security validation disabled - update aborted."
    }

    Write-Host "  Latest version: $latestVersion" -ForegroundColor Gray
    Write-Host "  Download URL: $zipUrl" -ForegroundColor Gray
    Write-Host "  Expected SHA256: $expectedHash" -ForegroundColor Gray

    # --- Version Comparison ---
    if ([version]$latestVersion -le [version]$currentVersion) {
        Write-Host ""
        Write-Host "You already have the latest version!" -ForegroundColor Green
        Start-Sleep -Seconds 3
        exit 0
    }

    Write-Host ""
    Write-Host "New version available: $currentVersion → $latestVersion" -ForegroundColor Yellow

    # --- User Confirmation ---
    # Check if running in interactive mode
    if ($null -eq $variable) {
        Write-Host "Non-interactive mode detected. Proceeding with update..." -ForegroundColor Yellow
        $choice = 'y'
    } else {
        $choice = Read-Host "Do you want to install this update now? (y/n)"
    }

    if ($choice -ne 'y' -and $choice -ne 'Y') {
        Write-Host "Update cancelled by user." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        exit 0
    }

    # --- Step 3: Stop TrayFlag Process ---
    Write-Host ""
    Write-Host "[3/8] Closing TrayFlag..." -ForegroundColor Cyan

    try {
        Stop-Process -Name "TrayFlag" -Force -ErrorAction Stop
        Start-Sleep -Seconds 2

        # Verify process is actually stopped
        $stillRunning = Get-Process -Name "TrayFlag" -ErrorAction SilentlyContinue
        if ($stillRunning) {
            throw "TrayFlag process could not be terminated. Close it manually and try again."
        }
    } catch {
        throw "Failed to close TrayFlag. Error: $($_.Exception.Message)"
    }

    Write-Host "  Process stopped successfully" -ForegroundColor Gray

    # --- Step 4: Cleanup Old Temp Files ---
    Write-Host ""
    Write-Host "[4/8] Cleaning up old temp files..." -ForegroundColor Cyan
    Remove_OldTempFiles -Dir $trayflagDir

    # --- Step 5: Backup Settings & Clean Install Folder ---
    Write-Host ""
    Write-Host "[5/8] Backing up settings and cleaning installation folder..." -ForegroundColor Cyan

    $tempDir = Join-Path $trayflagDir "__update_temp"
    $iniBackup = Join-Path $tempDir "TrayFlag.ini.backup"

    # Create temp directory
    try {
        New-Item -ItemType Directory -Path $tempDir -Force -ErrorAction Stop | Out-Null
    } catch {
        throw "Could not create temporary directory. Error: $($_.Exception.Message)"
    }

    # Backup INI file
    if (Test-Path $iniPath) {
        try {
            Copy-Item $iniPath $iniBackup -Force -ErrorAction Stop
            Write-Host "  Settings backed up: TrayFlag.ini → __update_temp/TrayFlag.ini.backup" -ForegroundColor Gray
        } catch {
            Write-Host "  Warning: Could not backup settings file. Continuing without backup..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "  No settings file found (first install?)" -ForegroundColor Gray
    }

    # Delete ALL files in installation folder EXCEPT:
    # - updater.ps1 (current script, running from memory)
    # - __update_temp (our temp folder with backup)
    Write-Host "  Removing old application files..." -ForegroundColor Gray
    try {
        Get-ChildItem -Path $trayflagDir | Where-Object {
            $_.Name -notin @('updater.ps1', '__update_temp')
        } | Remove-Item -Recurse -Force -ErrorAction Stop
        Write-Host "  Old files removed" -ForegroundColor Gray
    } catch {
        # Some files might be locked - try to continue
        Write-Host "  Warning: Some files could not be removed. They will be overwritten." -ForegroundColor Yellow
    }

    # --- Step 6: Download & Verify Update ---
    Write-Host ""
    Write-Host "[6/8] Downloading and verifying update..." -ForegroundColor Cyan

    $zipPath = Join-Path $trayflagDir "TrayFlag_update.zip"

    try {
        Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -TimeoutSec $NetworkTimeout -ErrorAction Stop
        Write-Host "  Download complete: $(Split-Path $zipPath -Leaf)" -ForegroundColor Gray
    } catch {
        throw "Failed to download update file. Check your internet connection.`n  Error: $($_.Exception.Message)"
    }

    # SHA256 Verification
    Write-Host "  Verifying SHA256 hash..." -ForegroundColor Gray
    try {
        $actualHash = (Get-FileHash -Algorithm SHA256 $zipPath -ErrorAction Stop).Hash
    } catch {
        throw "Failed to calculate file hash. File may be corrupted.`n  Error: $($_.Exception.Message)"
    }

    if ($actualHash -ne $expectedHash) {
        # Delete corrupted file
        if (Test-Path $zipPath) {
            Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        }
        throw "Downloaded file hash mismatch!`n  Expected: $expectedHash`n  Actual:   $actualHash`n  File deleted for security. Update aborted."
    }
    Write-Host "  Hash verified successfully ✓" -ForegroundColor Green

    # --- Extract Archive ---
    Write-Host "  Extracting archive..." -ForegroundColor Gray
    try {
        Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force -ErrorAction Stop
    } catch {
        throw "Failed to extract archive. File may be corrupted.`n  Error: $($_.Exception.Message)"
    }

    # Find extracted folder (first subdirectory in temp)
    $extractedFolder = Get-ChildItem -Path $tempDir -Directory | Where-Object {
        $_.Name -ne '__update_temp'
    } | Select-Object -First 1

    if (-not $extractedFolder) {
        # Try alternative: maybe files are in root of ZIP
        $extractedFolder = Get-ChildItem -Path $tempDir -File | Select-Object -First 1
        if ($extractedFolder) {
            $sourceDir = $tempDir  # Files are directly in temp
            Write-Host "  Archive structure: files in root directory" -ForegroundColor Gray
        } else {
            throw "Could not find extracted files in archive. Archive may be empty or corrupted."
        }
    } else {
        $sourceDir = $extractedFolder.FullName
        Write-Host "  Extracted to: $sourceDir" -ForegroundColor Gray
    }

    # --- Copy New Files ---
    Write-Host "  Copying new files to installation folder..." -ForegroundColor Gray
    $copyErrors = @()
    try {
        Get-ChildItem -Path $sourceDir | ForEach-Object {
            try {
                Copy-Item -Path $_.FullName -Destination $trayflagDir -Recurse -Force -ErrorAction Stop
            } catch {
                $copyErrors += $_.Exception.Message
            }
        }

        if ($copyErrors.Count -gt 0) {
            Write-Host "  Warning: Some files could not be copied:" -ForegroundColor Yellow
            $copyErrors | ForEach-Object { Write-Host "    - $_" -ForegroundColor Gray }
        } else {
            Write-Host "  Files copied successfully" -ForegroundColor Green
        }
    } catch {
        throw "Failed to copy files. Error: $($_.Exception.Message)"
    }

    # --- Restore Settings ---
    if (Test-Path $iniBackup) {
        try {
            Copy-Item $iniBackup $iniPath -Force -ErrorAction Stop
            Write-Host "  Settings restored: __update_temp/TrayFlag.ini.backup → TrayFlag.ini" -ForegroundColor Gray
        } catch {
            Write-Host "  Warning: Could not restore settings file." -ForegroundColor Yellow
        }
    }

    # --- Verify Essential Files ---
    Write-Host "  Verifying essential files..." -ForegroundColor Gray
    $essentialFiles = @('TrayFlag.exe', 'updater.ps1')
    $missingFiles = @()

    foreach ($file in $essentialFiles) {
        $filePath = Join-Path $trayflagDir $file
        if (-not (Test-Path $filePath)) {
            $missingFiles += $file
        }
    }

    if ($missingFiles.Count -gt 0) {
        throw "Essential files missing after update: $($missingFiles -join ', '). Update may be incomplete."
    }
    Write-Host "  Essential files verified ✓" -ForegroundColor Green

    # --- Step 7: Launch New Version ---
    Write-Host ""
    Write-Host "[7/8] Starting new version..." -ForegroundColor Cyan
    $newExePath = Join-Path $trayflagDir "TrayFlag.exe"

    try {
        Start-Process $newExePath -ErrorAction Stop
        Write-Host "  TrayFlag.exe launched successfully" -ForegroundColor Gray
    } catch {
        Write-Host "  Warning: Could not auto-start TrayFlag. Please launch it manually." -ForegroundColor Yellow
    }

    # --- Step 8: Final Cleanup ---
    Write-Host ""
    Write-Host "[8/8] Finalizing..." -ForegroundColor Cyan

    # Delete ZIP file (not needed anymore, saves disk space)
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        Write-Host "  ZIP file removed (not needed anymore)" -ForegroundColor Gray
    }

    Write-Host "  Temp files retained for rollback capability" -ForegroundColor Gray

    # --- Success Message ---
    Write-Host ""
    Write-Host "=========================" -ForegroundColor Green
    Write-Host "   UPDATE SUCCESSFUL!      " -ForegroundColor Green
    Write-Host "=========================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Updated from v$currentVersion to v$latestVersion" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backup files retained for rollback (if needed):" -ForegroundColor Cyan
    Write-Host "  • __update_temp\ folder" -ForegroundColor Gray
    Write-Host "  • TrayFlag_update.zip" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To rollback manually:" -ForegroundColor Yellow
    Write-Host "  1. Close TrayFlag" -ForegroundColor Gray
    Write-Host "  2. Copy files from __update_temp\TrayFlag_vX.XX.X\ to installation folder" -ForegroundColor Gray
    Write-Host "  3. Restart TrayFlag" -ForegroundColor Gray
    Write-Host ""
    Write-Host "This window will close in 5 seconds..." -ForegroundColor Gray
    Start-Sleep -Seconds 5

} catch {
    # --- Error Handling ---
    Write-Host ""
    Write-Host "=========================" -ForegroundColor Red
    Write-Host "   UPDATE FAILED!          " -ForegroundColor Red
    Write-Host "=========================" -ForegroundColor Red
    Write-Host ""
    Write-Host "AN ERROR OCCURRED:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "  • Check your internet connection" -ForegroundColor Gray
    Write-Host "  • Run PowerShell as Administrator" -ForegroundColor Gray
    Write-Host "  • Make sure TrayFlag.exe is running before updating" -ForegroundColor Gray
    Write-Host "  • Check if antivirus is blocking the update" -ForegroundColor Gray
    Write-Host "  • Temp files retained for inspection in: __update_temp\" -ForegroundColor Gray
    Write-Host "  • Check free disk space (minimum ${MinFreeSpaceMB} MB required)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "If problem persists, download update manually from:" -ForegroundColor Cyan
    Write-Host "  https://github.com/Ridbowt/TrayFlag  " -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to exit"
}

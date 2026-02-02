# getip_myip.ps1
# Version: 0.1.0
# Last-resort backup service via myip.com

function Invoke-WithRetry {
    param(
        [ScriptBlock]$Script,
        [int]$Retries = 3,
        [int]$DelaySeconds = 1
    )

    for ($i = 1; $i -le $Retries; $i++) {
        try {
            return & $Script
        } catch {
            Write-Host "[Debug] Attempt $i/$Retries failed: $_"
            if ($i -lt $Retries) { Start-Sleep -Seconds $DelaySeconds }
        }
    }
    throw "All retries failed."
}

try {
    $data = Invoke-WithRetry { Invoke-RestMethod -Uri "https://api.myip.com" -UseBasicParsing }

    $output = @{
        ip = $data.ip
        full_data = @{
            ip = $data.ip
            country_code = $data.cc
            city = "N/A"
            isp = "N/A"
            error = ""
        }
    }

    $output | ConvertTo-Json -Compress
} catch {
    $output = @{
        ip = "N/A"
        full_data = @{
            ip = ""
            country_code = ""
            city = ""
            isp = ""
            error = $_.Exception.Message
        }
    }
    $output | ConvertTo-Json -Compress
}

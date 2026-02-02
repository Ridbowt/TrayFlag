# getip_ipify.ps1
# Version: 0.1.0
# Fast service to get only the external IP via ipify.org

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
    $ip = Invoke-WithRetry { (Invoke-RestMethod -Uri "https://api.ipify.org?format=json" -UseBasicParsing).ip }

    $output = @{
        ip = $ip
        full_data = @{
            ip = $ip
            country_code = ""
            city = ""
            isp = ""
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

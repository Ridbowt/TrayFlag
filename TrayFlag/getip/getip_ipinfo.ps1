# getip_ipinfo.ps1
# Version: 0.1.0
# Backup service for full information via ipinfo.io

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
    # --- ИЗМЕНЕНИЕ: Берем IP из переменной окружения ---
    $ip = $env:TRAYFLAG_IP_TO_LOOKUP
    if (-not $ip) {
        throw "IP address not provided via environment variable."
    }

    $url = "https://ipinfo.io/$ip/json"
    $data = Invoke-WithRetry { Invoke-RestMethod -Uri $url -UseBasicParsing }

    $output = @{
        ip = $ip
        full_data = @{
            ip = $data.ip
            country_code = $data.country
            city = $data.city
            isp = $data.org
            error = ""
        }
    }

    $output | ConvertTo-Json -Compress
} catch {
    $output = @{
        ip = $ip
        full_data = @{
            ip = $ip
            country_code = ""
            city = ""
            isp = ""
            error = $_.Exception.Message
        }
    }
    $output | ConvertTo-Json -Compress
}

# File: src/ip_fetcher.py

import subprocess
import json
import os
import time
from utils import resource_path

# --- Fallback state for ipinfo.io ---
_IPINFO_FALLBACK_ACTIVE = False
_IPINFO_FALLBACK_SINCE = 0
_IPINFO_COOLDOWN = 2 * 60

def _run_ip_lookup(exe_name):
    exe_path = resource_path(os.path.join("getip", exe_name))
    if not os.path.exists(exe_path):
        raise FileNotFoundError(f"Executable not found: {exe_path}")

    result = subprocess.run(
        [exe_path],
        capture_output=True,
        text=True,
        timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    result.check_returncode()
    return json.loads(result.stdout)

def get_ip_data():
    """
    STEP 1: Quick IP check.
    Returns only the IP, not full details.
    """
    try:
        print("Attempting fast IP check via getip_ipify-org.exe...")
        data = _run_ip_lookup("getip_ipify-org.exe")
        ip = data.get("ip")
        if ip and ip != "N/A":
            return ip
    except Exception as e:
        print(f"Fast IP check (ipify) failed: {e}. Proceeding to fallback.")

    # Fallback
    print("Falling back to getip_myip-com.exe...")
    try:
        data = _run_ip_lookup("getip_myip-com.exe")
        ip = data.get("ip")
        if ip and ip != "N/A":
            return ip
    except Exception as e:
        print(f"Fallback (myip) also failed: {e}")

    return None

def get_full_data(ip_address, force=False):
    """
    Fetch full geo-IP data with myip.com as universal fallback.
    
    Args:
        ip_address: IP to lookup
        force: If True, bypass cooldown and always try ipinfo.io first
    
    Returns: dict with ip, full_data (country/city/isp/asn), and asn field.
    """
    global _IPINFO_FALLBACK_ACTIVE, _IPINFO_FALLBACK_SINCE, _IPINFO_COOLDOWN
    
    current_time = time.time()
    
    # === BLOCK 1: Cooldown check (skip if force=True) ===
    if not force and _IPINFO_FALLBACK_ACTIVE and (current_time - _IPINFO_FALLBACK_SINCE) < _IPINFO_COOLDOWN:
        print("ipinfo.io on cooldown, using myip.com fallback for partial data...")
        return _fetch_partial_from_myip(ip_address)
    
    # If cooldown has expired OR force=True — try ipinfo
    if _IPINFO_FALLBACK_ACTIVE:
        print("Cooldown expired or force update, testing ipinfo.io...")
        _IPINFO_FALLBACK_ACTIVE = False
    
    # === BLOCK 2: Try main service (ipinfo) ===
    try:
        print(f"Fetching full data for {ip_address} via getip_ipinfo-io.exe...")
        
        exe_path = resource_path(os.path.join("getip", "getip_ipinfo-io.exe"))
        env = os.environ.copy()
        env["TRAYFLAG_IP_TO_LOOKUP"] = ip_address
        
        result = subprocess.run(
            [exe_path], capture_output=True, text=True, timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW, env=env
        )
        result.check_returncode()
        data = json.loads(result.stdout)
        
        # Extract ASN from full_data if available
        if data.get('full_data'):
            asn = data['full_data'].get('asn', '')
            data['asn'] = asn
        
        # Успех! Сбрасываем флаг фоллбэка
        if _IPINFO_FALLBACK_ACTIVE:
            print("ipinfo.io recovered, switching back to primary.")
            _IPINFO_FALLBACK_ACTIVE = False
        
        return data
            
    except Exception as e:
        print(f"ipinfo.io failed: {e}. Switching to myip.com fallback.")
        _IPINFO_FALLBACK_ACTIVE = True
        _IPINFO_FALLBACK_SINCE = current_time
    
    # === BLOCK 3: Fallback to myip.com (partial data) ===
    return _fetch_partial_from_myip(ip_address)

def _fetch_partial_from_myip(ip_address):
    """
    Helper: fetch IP + country from myip.com as fallback for full data.
    Returns structure compatible with get_full_data() output.
    """
    try:
        print(f"Fetching partial data via getip_myip-com.exe...")
        data = _run_ip_lookup("getip_myip-com.exe")
        
        ip = data.get("ip", "")
        country = data.get("full_data", {}).get("country_code", "")
        
        # Return a structure compatible with the main format
        result = {
            "ip": ip,
            "full_data": {
                "ip": ip,
                "country_code": country,
                "city": "",          # myip does not provide the city
                "isp": "",           # myip does not provide the ISP
                "asn": "",           # myip does not provide ASN
                "error": "" if ip and ip != "N/A" else "Fallback failed"
            },
            "asn": ""  # Top-level ASN field for compatibility
        }
        return result
        
    except Exception as e:
        print(f"myip.com fallback also failed: {e}")
        # Return a minimal placeholder
        return {
            "ip": ip_address,
            "full_data": {
                "ip": "",
                "country_code": "",
                "city": "",
                "isp": "",
                "asn": "",
                "error": f"All services failed: {e}"
            },
            "asn": ""
        }
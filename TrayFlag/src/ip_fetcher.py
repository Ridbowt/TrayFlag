# File: src/ip_fetcher.py (НОВАЯ ВЕРСИЯ)

import subprocess
import json
import os
from utils import resource_path

def _run_ps_script(script_name):
    """Helper function to run a PowerShell script."""
    script_path = resource_path(os.path.join("getip", script_name))
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")

    command = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
    
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    result.check_returncode() # Will raise an error if the script exits with a code other than 0
    return json.loads(result.stdout)

def get_ip_data():
    """
    STEP 1: Quick IP check.
    Returns only the IP, not full details.
    """
    try:
        print("Attempting fast IP check via getip_ipify.ps1...")
        data = _run_ps_script("getip_ipify.ps1")
        ip = data.get("ip")
        if ip and ip != "N/A":
            return ip
    except Exception as e:
        print(f"Fast IP check (ipify) failed: {e}. Proceeding to fallback.")

    # Fallback
    print("Falling back to getip_myip.ps1...")
    try:
        data = _run_ps_script("getip_myip.ps1")
        ip = data.get("ip")
        if ip and ip != "N/A":
            return ip
    except Exception as e:
        print(f"Fallback (myip) also failed: {e}")

    return None

def get_full_data(ip_address):
    """
    Gets full geo-data for a known IP.
    """
    # --- STEP 3: Retrieve geo-data ---
    try:
        print(f"Fetching full data for {ip_address} via getip_ipinfo.ps1...")
        # We need to pass the IP to the script. We'll do this via environment variables.
        env = os.environ.copy()
        env["TRAYFLAG_IP_TO_LOOKUP"] = ip_address
        
        script_path = resource_path(os.path.join("getip", "getip_ipinfo.ps1"))
        command = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
        
        result = subprocess.run(
            command,
            capture_output=True, text=True, timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=env
        )
        result.check_returncode()
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Full data fetch (ipinfo) failed: {e}")
        # If it fails, at least return what we have (IP only)
        return {'ip': ip_address, 'full_data': {}}
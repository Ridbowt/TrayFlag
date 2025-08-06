# File: src/ip_fetcher.py
import subprocess
import json
import os
from utils import resource_path

def get_ip_data_from_go():
    go_exe_path = resource_path("ip_lookup.exe")
    if not os.path.isfile(go_exe_path):
        print(f"Error: Go executable not found at {go_exe_path}")
        return None
    try:
        result = subprocess.run(
            [go_exe_path], capture_output=True, text=True, check=True, timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error interacting with Go executable: {e}")
        return None
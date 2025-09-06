# File: src/ip_fetcher.py

import subprocess
import json
import os
from utils import resource_path

def get_ip_data_from_rust():
    rust_exe_path = resource_path("ip_lookup.exe")
    if not os.path.isfile(rust_exe_path):
        print(f"Error: Rust executable not found at {rust_exe_path}")
        return None
    try:
        result = subprocess.run(
            [rust_exe_path], capture_output=True, text=True, check=True, timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error interacting with Rust executable: {e}")
        return None

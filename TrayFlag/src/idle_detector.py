# File: src/idle_detector.py

try:
    import win32api
    from pycaw.pycaw import AudioUtilities
    LIBS_AVAILABLE = True
except ImportError:
    print("WARNING: pywin32/pycaw not found. Idle mode will be disabled.")
    LIBS_AVAILABLE = False

def get_idle_time_seconds():
    if not LIBS_AVAILABLE: return 0
    try:
        last_input_info = win32api.GetLastInputInfo()
        current_time_ms = win32api.GetTickCount()
        return (current_time_ms - last_input_info) / 1000
    except Exception:
        return 0

def is_audio_playing():
    if not LIBS_AVAILABLE: return False
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.SimpleAudioVolume.GetMasterVolume() > 0:
                if session.State == 1: # S_ACTIVE
                    return True
        return False
    except Exception:
        return False

def is_user_idle(idle_threshold_seconds):
    if not LIBS_AVAILABLE: return False
    if get_idle_time_seconds() < idle_threshold_seconds:
        return False
    if is_audio_playing():
        return False
    return True

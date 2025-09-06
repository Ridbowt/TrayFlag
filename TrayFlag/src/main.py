# File: src/main.py

import sys
import os
from PySide6 import QtWidgets
import themes
from utils import resource_path, create_desktop_shortcut
from constants import APP_NAME, ORG_NAME, __version__
from translator import Translator

# --- Code to check for a single instance ---
try:
    import win32event
    import win32api
    from winerror import ERROR_ALREADY_EXISTS
    pywin32_available = True
except ImportError:
    pywin32_available = False

class SingleInstance:
    def __init__(self, name):
        self.mutex = None
        self.mutexname = name
        if pywin32_available:
            self.mutex = win32event.CreateMutex(None, False, name)
            self.lasterror = win32api.GetLastError()
        else:
            self.lasterror = 0
    def already_running(self):
        return pywin32_available and (self.lasterror == ERROR_ALREADY_EXISTS)
    def __del__(self):
        if self.mutex:
            win32api.CloseHandle(self.mutex)

# --- Prompt to Create Shortcut ---
def handle_first_launch():
    """
    Checks if this is the first launch and prompts to create a shortcut.
    """
    settings_path = resource_path(f"{APP_NAME}.ini")
    if os.path.exists(settings_path):
        return

    # Create a temporary translator just for this conversation
    tr = Translator(resource_path("assets/i18n"))
    # Try to determine the system language for this conversation
    try:
        import locale
        system_lang, _ = locale.getdefaultlocale()
        lang_to_load = system_lang[:2] if system_lang else "en"
    except Exception:
        lang_to_load = "en"
    tr.load_language(lang_to_load)

    reply = QtWidgets.QMessageBox.question(
        None, 
        tr.get("shortcut_dialog_title"),
        tr.get("shortcut_dialog_text"),
        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        QtWidgets.QMessageBox.StandardButton.Yes
    )

    if reply == QtWidgets.QMessageBox.StandardButton.Yes:
        create_desktop_shortcut()


if __name__ == "__main__":
    # 1. Check if another instance is already running
    mutex_name = f"TrayFlag-Instance-Mutex-8E2E7A4E"
    instance = SingleInstance(mutex_name)
    if instance.already_running():
        print("[WARNING] Application is already running. Exiting.")
        sys.exit(0)
    
    print(f"[INFO] --- {APP_NAME} v{__version__} starting up ---")

    # 2. Create QApplication - it's needed for MessageBox
    qt_app = QtWidgets.QApplication(sys.argv)

    # 4. Apply styles and settings
    qt_app.setStyleSheet(themes.get_context_menu_style())
    qt_app.setApplicationName(APP_NAME)
    qt_app.setOrganizationName(ORG_NAME)
    qt_app.setQuitOnLastWindowClosed(False)
    
    # 5. Import and run the main application
    from app import App
    main_app = App()
    
    sys.exit(qt_app.exec())

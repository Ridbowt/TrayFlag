# File: src/main.py

import sys
import os
from PySide6 import QtWidgets # Используем PySide6, как в вашем коде
import themes
from utils import resource_path, create_desktop_shortcut
from constants import APP_NAME, ORG_NAME
from translator import Translator

# --- Код для проверки одного экземпляра (без изменений) ---
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

# --- НОВАЯ ФУНКЦИЯ: Предложение создать ярлык ---
def handle_first_launch():
    """
    Проверяет, первый ли это запуск, и предлагает создать ярлык.
    """
    settings_path = resource_path(f"{APP_NAME}.ini")
    if os.path.exists(settings_path):
        return

    # Создаем временный переводчик только для этого диалога
    tr = Translator(resource_path("assets/i18n"))
    # Пытаемся определить системный язык для диалога
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
    # 1. Проверяем, не запущена ли уже копия
    mutex_name = f"TrayFlag-Instance-Mutex-8E2E7A4E"
    instance = SingleInstance(mutex_name)
    if instance.already_running():
        print("Application is already running. Exiting.")
        sys.exit(0)

    # 2. Создаем QApplication - он нужен для MessageBox
    qt_app = QtWidgets.QApplication(sys.argv)

    # 4. Применяем стили и настройки (без изменений)
    qt_app.setStyleSheet(themes.get_context_menu_style())
    qt_app.setApplicationName(APP_NAME)
    qt_app.setOrganizationName(ORG_NAME)
    qt_app.setQuitOnLastWindowClosed(False)
    
    # 5. Импортируем и запускаем основное приложение (без изменений)
    from app import App
    main_app = App()
    
    sys.exit(qt_app.exec())
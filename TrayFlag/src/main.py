# File: src/main.py
import sys
from PySide6 import QtWidgets
from app import App
from constants import APP_NAME, ORG_NAME
import themes

# --- НАЧАЛО НОВОГО КОДА ---
try:
    import win32event
    import win32api
    from winerror import ERROR_ALREADY_EXISTS
    pywin32_available = True
except ImportError:
    pywin32_available = False

class SingleInstance:
    """Класс для проверки и удержания мьютекса."""
    def __init__(self, name):
        self.mutex = None
        self.mutexname = name
        if pywin32_available:
            self.mutex = win32event.CreateMutex(None, False, name)
            self.lasterror = win32api.GetLastError()
        else:
            self.lasterror = 0

    def already_running(self):
        """Возвращает True, если другой экземпляр уже запущен."""
        return pywin32_available and (self.lasterror == ERROR_ALREADY_EXISTS)

    def __del__(self):
        """Освобождает мьютекс при выходе из программы."""
        if self.mutex:
            win32api.CloseHandle(self.mutex)
# --- КОНЕЦ НОВОГО КОДА ---


if __name__ == "__main__":
    # --- НАЧАЛО НОВОГО КОДА ---
    # Уникальное имя для мьютекса. Можно использовать GUID.
    mutex_name = f"TrayFlag-Instance-Mutex-8E2E7A4E"
    instance = SingleInstance(mutex_name)

    if instance.already_running():
        # (Опционально) Можно показать сообщение пользователю
        # QtWidgets.QMessageBox.warning(None, "TrayFlag", "Приложение уже запущено.")
        print("Application is already running. Exiting.")
        sys.exit(0)
    # --- КОНЕЦ НОВОГО КОДА ---

    qt_app = QtWidgets.QApplication(sys.argv)

    qt_app.setStyleSheet(themes.get_context_menu_style())
    
    qt_app.setApplicationName(APP_NAME)
    qt_app.setOrganizationName(ORG_NAME)
    qt_app.setQuitOnLastWindowClosed(False)
    
    # Импортируем App только ПОСЛЕ проверки, чтобы не грузить тяжелый GUI зря
    from app import App
    main_app = App()
    
    sys.exit(qt_app.exec())
# File: src/utils.py
import sys
import os
import re
from PyQt6 import QtWidgets, QtGui, QtCore
from constants import APP_NAME # <-- ИЗМЕНЕНО

def get_base_path():
    """
    Возвращает правильный базовый путь для .py и для скомпилированного .exe.
    """
    if getattr(sys, 'frozen', False):
        # Для скомпилированного приложения Nuitka:
        # sys.executable указывает на сам исполняемый файл (например, TrayFlag.exe).
        # os.path.dirname(sys.executable) вернет путь к папке, где лежит .exe.
        # Пример: F:\Scripts\Python\TrayFlag\dist\TrayFlag.dist
        return os.path.dirname(sys.executable)
    else:
        # Для запуска .py скрипта:
        # os.path.abspath(__file__) дает полный путь к текущему скрипту (TrayFlag.py).
        # os.path.dirname(...) вернет путь к папке, где лежит скрипт (например, src).
        # Пример: F:\Scripts\Python\TrayFlag\src
        #return os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # <--- ПРИ ЗАПУСКЕ ИЗ .PY СКРИПТА
        return os.path.dirname(os.path.abspath(__file__)) # <--- ПРИ ЗАПУСКЕ ИЗ .EXE ПРИЛОЖЕНИЯ

def resource_path(relative_path):
    return os.path.join(get_base_path(), relative_path)

def clean_isp_name(isp_name):
    if not isp_name: return "N/A"
    isp_name = re.sub(r'\bAS\d+\b|\(\s*AS\d+\s*\)', '', isp_name, flags=re.IGNORECASE).strip()
    words_to_remove = [
        "PJSC", "LLC", "Ltd", "Inc", "Corp", "Corporation", "Company", "Co",
        "Public Joint Stock Company", "Limited Liability Company",
        "Joint Stock Company", "Open Joint Stock Company",
        "Private Limited Company", "PLC", "GmbH", "AG", "SA", "S.A.", "S.P.A.", "S.R.L.",
        "Internet Service Provider", "ISP", "Telecommunications", "Communications",
        "Network", "Solutions", "Technologies", "Services", "Group", "Holding",
        "LLP", "LP", "PC", "SC", "O.O.O.", "ZAO", "OAO", "PAO", "JSC", "CJSC"
    ]
    pattern = r'\b(?:' + '|'.join(re.escape(word) for word in words_to_remove) + r')\b\.?\s*'
    isp_name = re.sub(pattern, '', isp_name, flags=re.IGNORECASE).strip()
    isp_name = isp_name.replace("  ", " ").strip(' -.,')
    return isp_name if isp_name else "N/A"

def truncate_text(text, max_length):
    return text[:max_length-3] + "..." if len(text) > max_length else text

def set_autostart_shortcut(enabled):
    if sys.platform != 'win32': return
    try:
        import win32com.client
    except ImportError:
        print("WARNING: pywin32 library not found. Autostart feature is disabled.")
        return
        
    shell = win32com.client.Dispatch("WScript.Shell")
    startup_folder = shell.SpecialFolders("Startup")
    shortcut_path = os.path.join(startup_folder, f"{APP_NAME}.lnk")
    
    if enabled:
        main_exe_path = resource_path(f"{APP_NAME}.exe")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = main_exe_path
        shortcut.IconLocation = resource_path(os.path.join("assets", "icons", "logo.ico"))
        shortcut.Description = f"Start {APP_NAME}"
        shortcut.WorkingDirectory = get_base_path()
        shortcut.save()
        print(f"Autostart shortcut created at: {shortcut_path}")
    else:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print(f"Autostart shortcut removed from: {shortcut_path}")

def create_no_internet_icon(size=20):
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    pen = QtGui.QPen(QtCore.Qt.GlobalColor.red)
    pen.setWidth(3)
    painter.setPen(pen)
    painter.drawLine(3, 3, size - 4, size - 4)
    painter.drawLine(size - 4, 3, 3, size - 4)
    painter.end()
    return QtGui.QIcon(pixmap)
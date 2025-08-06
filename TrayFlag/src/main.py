# File: src/main.py
import sys
from PyQt6 import QtWidgets
from app import App
from constants import APP_NAME, ORG_NAME # <-- ИЗМЕНЕНО

if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)
    
    qt_app.setApplicationName(APP_NAME)
    qt_app.setOrganizationName(ORG_NAME)
    qt_app.setQuitOnLastWindowClosed(False)
    
    main_app = App()
    
    sys.exit(qt_app.exec())
# File: src/tray_menu.py

from PySide6 import QtWidgets, QtGui
from functools import partial
from utils import clean_isp_name
from constants import APP_NAME

class TrayMenuManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.tr = self.app.tr
        self.menu = QtWidgets.QMenu()
        self.create_menu()

    def create_menu(self):
            # Now the information items are created as clickable right away
            self.ip_action = QtGui.QAction(self.tr.get("menu_ip_wait"))
            self.ip_action.triggered.connect(lambda: self.app.copy_text_to_clipboard(self.app.state.current_location_data.get('ip', '')))
            self.ip_action.setEnabled(False)

            self.city_action = QtGui.QAction(self.tr.get("menu_city_wait"))
            self.city_action.triggered.connect(lambda: self.app.copy_text_to_clipboard(self.app.state.current_location_data.get('city', '')))
            self.city_action.setEnabled(False)

            self.isp_action = QtGui.QAction(self.tr.get("menu_isp_wait"))
            self.isp_action.triggered.connect(lambda: self.app.copy_text_to_clipboard(clean_isp_name(self.app.state.current_location_data.get('isp', ''))))
            self.isp_action.setEnabled(False)            

            # The remaining menu items stay unchanged
            self.force_update_action = QtGui.QAction(self.tr.get("menu_update_now")); self.force_update_action.triggered.connect(lambda: self.app.update_handler.update_location_icon(is_forced_by_user=True))
            self.speedtest_action = QtGui.QAction(self.tr.get("menu_speedtest_browser"))
            self.speedtest_action.triggered.connect(self.app.open_speedtest_website)
            self.dns_leak_action = QtGui.QAction(self.tr.get("menu_dns_leak_test"))
            self.dns_leak_action.triggered.connect(self.app.open_dns_leak_test_website)
            self.weblink_action = QtGui.QAction(self.tr.get("menu_weblink")); self.weblink_action.triggered.connect(self.app.open_weblink); self.weblink_action.setEnabled(False)
            self.history_menu = QtWidgets.QMenu(self.tr.get("menu_history"))
            self.history_placeholder_action = QtGui.QAction(self.tr.get("menu_history_empty")); self.history_placeholder_action.setEnabled(False)
            self.history_menu.addAction(self.history_placeholder_action)

            self.update_action = QtGui.QAction(self.tr.get("menu_check_for_updates"))
            self.update_action.triggered.connect(self.app.run_updater)

            self.settings_action = QtGui.QAction(self.tr.get("menu_settings")); self.settings_action.triggered.connect(self.app.open_settings_dialog)
            self.about_action = QtGui.QAction(self.tr.get("menu_about", app_name=APP_NAME)); self.about_action.triggered.connect(self.app.open_about_dialog)
            self.exit_action = QtGui.QAction(self.tr.get("menu_exit")); self.exit_action.triggered.connect(QtWidgets.QApplication.quit)
            
            actions = [
                # Group 1: Information
                self.ip_action, self.city_action, self.isp_action,
                None,
                # Group 2: IP Actions
                self.history_menu, self.weblink_action,
                None,
                # Group 3: Diagnostic Tools
                self.force_update_action, self.speedtest_action, self.dns_leak_action,
                None,
                # Group 4: Application
                self.settings_action, self.update_action, self.about_action,
                None,
                self.exit_action
            ]
            for action in actions:
                if action is None: self.menu.addSeparator()
                elif isinstance(action, QtWidgets.QMenu): self.menu.addMenu(action)
                else: self.menu.addAction(action)

    def update_menu_content(self):
            data = self.app.state.current_location_data
            ip, city, isp = data.get('ip', 'N/A'), data.get('city', 'N/A'), clean_isp_name(data.get('isp', 'N/A'))
            self.ip_action.setText(self.tr.get("menu_ip_label", ip=ip))
            self.city_action.setText(self.tr.get("menu_city_label", city=city))
            self.isp_action.setText(self.tr.get("menu_isp_label", isp=isp))
            
            has_ip = ip != 'N/A'
            
            self.weblink_action.setEnabled(has_ip)
            self.ip_action.setEnabled(has_ip)
            self.city_action.setEnabled(has_ip)
            self.isp_action.setEnabled(has_ip)

            self.history_menu.clear()
            if not self.app.state.location_history:
                self.history_menu.addAction(self.history_placeholder_action)
            else:
                for entry in reversed(self.app.state.location_history):
                    hist_ip, hist_isp = entry.get('ip', 'N/A'), clean_isp_name(entry.get('isp', 'N/A'))
                    text = f"{hist_ip} ({entry.get('country_code', '??').upper()}, {entry.get('city', 'N/A')}, {hist_isp})"
                    action = QtGui.QAction(text, self.menu)
                    action.triggered.connect(partial(self.app.copy_historical_ip, hist_ip))
                    self.history_menu.addAction(action)

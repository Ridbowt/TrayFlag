# File: src/app.py (ФИНАЛЬНАЯ ВЕРСИЯ ПОСЛЕ РЕФАКТОРИНГА)

import os
import webbrowser
import time
from PySide6 import QtWidgets, QtGui, QtCore

from utils import resource_path, create_no_internet_icon, set_autostart_shortcut, truncate_text, clean_isp_name, create_desktop_shortcut
from config import ConfigManager, SETTINGS_FILE_PATH
from constants import __version__, RELEASE_DATE
from translator import Translator, get_initial_language_code
from dialogs import AboutDialog, SettingsDialog, CustomQuestionDialog
from tray_menu import TrayMenuManager
from sound_manager import SoundManager
from state_manager import AppState
from update_handler import UpdateHandler

class App(QtWidgets.QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        
        # --- 1. Инициализация менеджеров ---
        self.config = ConfigManager()
        self.state = AppState()
        self.tr = Translator(resource_path("assets/i18n"))
        self.sound_manager = SoundManager(self.config)
        
        self.settings_dialog = None
        self.about_dialog = None

        # --- 2. Создаем и настраиваем UpdateHandler ---
        self.update_handler = UpdateHandler(self.config, self.state)
        self.update_handler.ipDataReceived.connect(self.on_ip_data_received)
        self.update_handler.enteredIdleMode.connect(self.on_entered_idle_mode)
        
        # --- 3. Загружаем настройки и ресурсы ---
        self.load_app_settings()
        self.app_icon = self._load_icon("logo.ico")
        self.moon_icon = self._load_icon("moon.png")
        self.no_internet_icon = create_no_internet_icon()
        self.about_logo_pixmap = self._load_pixmap("about_logo.png", 96)
        
        # --- 4. Создаем GUI ---
        self.menu_manager = TrayMenuManager(self)
        self.setContextMenu(self.menu_manager.menu)
        
        # --- 5. Финальная настройка и запуск ---
        self.setIcon(self.app_icon or self.no_internet_icon)
        self.show()
        self.setToolTip(self.tr.get("initializing_tooltip"))
        
        self.activated.connect(self.on_activated)
        
        QtCore.QTimer.singleShot(100, self._handle_first_launch_tasks)
        self.update_handler.start()

    def _handle_first_launch_tasks(self):
        if self.config.shortcut_prompted: return
        dialog = CustomQuestionDialog(
            self.tr.get("shortcut_dialog_title"),
            self.tr.get("shortcut_dialog_text"),
            self.tr, self.app_icon
        )
        if dialog.exec(): create_desktop_shortcut()
        self.config.settings.setValue("main/shortcut_prompted", True)
        self.config.shortcut_prompted = True

    def load_app_settings(self):
        cfg = self.config
        lang_code = get_initial_language_code(cfg.language)
        cfg.language = lang_code
        self.tr.load_language(lang_code)

    @QtCore.Slot(object, bool)
    def on_ip_data_received(self, ip_data, is_forced):
        if not ip_data or ip_data.get('ip') == "N/A":
            if self.state.last_known_external_ip != "N/A":
                self.sound_manager.play_alert()
            self.state.clear_network_state()
            self.setIcon(self.no_internet_icon)
            self.setToolTip(self.tr.get("error_tooltip", error=self.tr.get("no_external_ip_detected")))
            return

        current_ip = ip_data.get('ip')
        full_data = ip_data.get('full_data', {})
        
        ip_has_changed = (current_ip != self.state.last_known_external_ip)

        # --- НАЧАЛО ПРОСТОЙ ИСПРАВЛЕННОЙ ЛОГИКИ ---
        
        # Если IP изменился ИЛИ это был ручной клик,
        # мы всегда делаем полное обновление.
        if ip_has_changed or is_forced:
            if full_data:
                self.state.update_location(full_data)
            else:
                self.state.update_location({'ip': current_ip, 'country_code': '??', 'city': 'N/A', 'isp': 'N/A'})
            
            # Вызываем полное обновление GUI.
            # Звук будет проигран внутри этой функции.
            self.update_gui_with_new_data()
        # --- КОНЕЦ ПРОСТОЙ ИСПРАВЛЕННОЙ ЛОГИКИ ---

    @QtCore.Slot()
    def on_entered_idle_mode(self):
        """Этот слот вызывается, когда приложение переходит в экономный режим."""
        self.setIcon(self.moon_icon or self.app_icon)
        self.setToolTip(self.tr.get("idle_mode_tooltip"))

    def update_gui_with_new_data(self):
        data = self.state.current_location_data
        country_code = data.get('country_code', '')
        icon = self._load_icon(f"{country_code}.png", "flags")
        self.setIcon(icon or self.app_icon)
        
        update_time_str = time.strftime("%H:%M:%S")
        tooltip_text = (f"{data.get('ip', 'N/A')}\n"
                        f"{country_code.upper()}\n"
                        f"{truncate_text(data.get('city', 'N/A'), 17)}\n"
                        f"{truncate_text(clean_isp_name(data.get('isp', 'N/A')), 17)}\n"
                        f"({self.tr.get('tooltip_updated_at', time=update_time_str)})")
        self.setToolTip(tooltip_text)
        
        self.menu_manager.update_menu_content()
        
        if self.config.notifications:
            self.showMessage(self.tr.get("location_updated_title"), 
                             self.tr.get("location_updated_message", ip=data.get('ip'), city=data.get('city'), country_code=country_code.upper()), 
                             self.icon(), 5000)

        self.sound_manager.play_notification()
        
    def open_settings_dialog(self):
        if self.settings_dialog:
            self.settings_dialog.raise_(); self.settings_dialog.activateWindow(); return
        self.settings_dialog = SettingsDialog(self.app_icon, self.tr, self.tr.available_languages, self.config, None)
        self.settings_dialog.accepted.connect(self.on_settings_accepted)
        self.settings_dialog.rejected.connect(self.on_settings_rejected)
        self.settings_dialog.show()

    def on_settings_accepted(self):
        if not self.settings_dialog: return
        old_lang = self.config.language
        new_settings = self.settings_dialog.get_settings()
        self.config.save_settings(new_settings)
        set_autostart_shortcut(new_settings['autostart'])
        self.load_app_settings()
        self.sound_manager.reload_sounds()
        if old_lang != self.config.language:
            self.reload_ui_texts()
        self.settings_dialog.close(); self.settings_dialog = None

    def on_settings_rejected(self):
        if not self.settings_dialog: return
        self.settings_dialog.close(); self.settings_dialog = None

    def reload_ui_texts(self):
        self.tr = Translator(resource_path("assets/i18n"))
        lang_code = get_initial_language_code(self.config.language)
        self.tr.load_language(lang_code)
        self.menu_manager = TrayMenuManager(self)
        self.setContextMenu(self.menu_manager.menu)
        if self.state.current_location_data: self.menu_manager.update_menu_content()

    def open_about_dialog(self):
        if self.about_dialog and self.about_dialog.isVisible():
            self.about_dialog.raise_(); self.about_dialog.activateWindow(); return
        self.about_dialog = AboutDialog(self.app_icon, self.tr, __version__, RELEASE_DATE, self.about_logo_pixmap, None)
        self.about_dialog.exec()

    def on_activated(self, reason):
        if self.state.is_in_idle_mode:
            self.update_handler.exit_idle_mode()
        elif reason == self.ActivationReason.Trigger:
            self.update_handler.update_location_icon(is_forced_by_user=True)

    def _load_icon(self, filename, subfolder="icons", size=20):
        try:
            path = resource_path(os.path.join("assets", subfolder, filename))
            if not os.path.isfile(path): return None
            pixmap = QtGui.QPixmap(path)
            return QtGui.QIcon(pixmap.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"Error loading icon {filename}: {e}"); return None

    def _load_pixmap(self, filename, size):
        try:
            path = resource_path(os.path.join("assets", "icons", filename))
            if not os.path.isfile(path): return None
            pixmap = QtGui.QPixmap(path)
            return pixmap.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        except Exception as e:
            print(f"Error loading pixmap {filename}: {e}"); return None

    def copy_ip_to_clipboard(self):
        if self.state.current_location_data and 'ip' in self.state.current_location_data:
            self.copy_text_to_clipboard(self.state.current_location_data['ip'])

    def copy_historical_ip(self, ip_to_copy):
        self.copy_text_to_clipboard(ip_to_copy)
    
    def copy_text_to_clipboard(self, text):
        QtWidgets.QApplication.clipboard().setText(text)
        if self.config.notifications:
            self.showMessage(self.tr.get("copied_title"), self.tr.get("copied_message_simple", text=text), self.icon(), 2000)

    def open_weblink(self):
        if self.state.current_location_data and 'ip' in self.state.current_location_data:
            webbrowser.open(f"https.www.ip-tracker.org/lookup.php?ip={self.state.current_location_data['ip']}")

    def open_speedtest_website(self):
        webbrowser.open('https://www.speedtest.net')

    def open_dns_leak_test_website(self):
        webbrowser.open('https://ipleak.net/')
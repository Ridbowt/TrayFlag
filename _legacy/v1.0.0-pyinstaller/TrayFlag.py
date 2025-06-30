import sys
import os
import requests
import webbrowser
import json
import locale
from collections import deque
from functools import partial
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import QSettings
import threading
import random

__version__ = "1.0.0"
APP_NAME = "TrayFlag"

# --- ФИНАЛЬНОЕ РЕШЕНИЕ ДЛЯ ПУТЕЙ v2.0 ---
def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсу, работает для скрипта и для .exe """
    if getattr(sys, 'frozen', False):
        # Если мы скомпилированы, базовый путь - это папка, где лежит .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Если мы запускаемся как скрипт, это папка со скриптом
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

SETTINGS_FILE_PATH = resource_path(f"{APP_NAME}.ini")

try:
    import soundfile as sf
    import sounddevice as sd
    sound_libs_available = True
except ImportError:
    sound_libs_available = False

class Translator:
    def __init__(self, i18n_dir, default_lang="en"):
        self.i18n_dir = i18n_dir
        self.default_lang = default_lang
        self.current_lang = default_lang
        self.translations = {}
        self.available_languages = self.find_languages()

    def find_languages(self):
        langs = {}
        path = resource_path(self.i18n_dir)
        if not os.path.isdir(path): return langs
        for filename in os.listdir(path):
            if filename.endswith(".json"):
                lang_code = filename[:-5]
                langs[lang_code] = lang_code.upper() 
        return langs

    def load_language(self, lang_code):
        self.current_lang = lang_code
        if lang_code not in self.available_languages:
            self.current_lang = self.default_lang
        
        filepath = resource_path(os.path.join(self.i18n_dir, f"{self.current_lang}.json"))
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except Exception:
            if self.current_lang != self.default_lang:
                self.load_language(self.default_lang)
        return self.current_lang

    def get(self, key, **kwargs):
        text = self.translations.get(key, f"<{key}>")
        try: return text.format(**kwargs)
        except (KeyError, IndexError): return text

def get_location_data():
    try:
        fields = "status,message,countryCode,city,isp,query"
        response = requests.get(f"http://ip-api.com/json/?fields={fields}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == 'success':
            return {'ip': data.get('query', 'N/A'), 'country_code': data.get('countryCode', '').lower(), 'city': data.get('city', 'N/A'), 'isp': data.get('isp', 'N/A')}
        else:
            raise ValueError(f"API Error: {data.get('message', 'Unknown')}")
    except requests.RequestException as e:
        raise ConnectionError(f"Network error: {e}")
    except ValueError as e:
        raise ValueError(f"API data error: {e}")

def set_autostart_shortcut(enabled):
    if sys.platform != 'win32': return
    try:
        import win32com.client
    except ImportError: return
        
    shell = win32com.client.Dispatch("WScript.Shell")
    startup_folder = shell.SpecialFolders("Startup")
    shortcut_path = os.path.join(startup_folder, f"{APP_NAME}.lnk")
    
    if enabled:
        target_path = sys.executable
        icon_path = resource_path(os.path.join("assets", "icons", "logo.ico"))
        work_dir = os.path.dirname(target_path)
        
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target_path
        shortcut.Arguments = ""
        shortcut.WindowStyle = 1
        shortcut.IconLocation = icon_path
        shortcut.Description = f"Start {APP_NAME}"
        shortcut.WorkingDirectory = work_dir
        shortcut.save()
    else:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)

def truncate_text(text, max_length):
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, version, app_icon, tr, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr.get("about_dialog_title", app_name=APP_NAME))
        self.setWindowIcon(app_icon)
        self.setMinimumWidth(350)
        layout = QtWidgets.QVBoxLayout(self)
        title_label = QtWidgets.QLabel(f"<b>{APP_NAME}</b>")
        font = title_label.font(); font.setPointSize(14); title_label.setFont(font)
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        release_date = "2025-06-27"
        version_label = QtWidgets.QLabel(tr.get("about_version", version=version, release_date=release_date))
        version_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        website_label = QtWidgets.QLabel(f'<a href="https://github.com/Ridbowt/TrayFlag">{tr.get("about_website")}</a>')
        website_label.setOpenExternalLinks(True)
        website_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        acknowledgements_box = QtWidgets.QGroupBox(tr.get("about_acknowledgements"))
        ack_layout = QtWidgets.QVBoxLayout()
        ack_html = (
            f"<style>ul {{ list-style-type: none; padding-left: 0; margin-left: 0; }} li {{ margin-bottom: 5px; }}</style>"
            f"<ul>{tr.get('ack_flags')}{tr.get('ack_app_icon')}{tr.get('ack_logo_builder')}{tr.get('ack_sound')}{tr.get('ack_code')}{tr.get('ack_ai')}</ul>"
        )
        ack_label = QtWidgets.QLabel(ack_html)
        ack_label.setOpenExternalLinks(True)
        ack_label.setWordWrap(True)
        ack_layout.addWidget(ack_label)
        acknowledgements_box.setLayout(ack_layout)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(title_label); layout.addWidget(version_label); layout.addWidget(website_label)
        layout.addSpacing(15); layout.addWidget(acknowledgements_box); layout.addStretch()
        layout.addWidget(button_box)

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, app_icon, tr, available_langs, current_lang, parent=None):
        super().__init__(parent)
        self.tr = tr
        self.current_lang = current_lang
        self.setWindowTitle(tr.get("settings_dialog_title", app_name=APP_NAME))
        self.setWindowIcon(app_icon)
        self.setModal(True)
        self.settings = QSettings(SETTINGS_FILE_PATH, QSettings.Format.IniFormat)
        layout = QtWidgets.QVBoxLayout(self)
        form_layout = QtWidgets.QFormLayout()
        self.language_combo = QtWidgets.QComboBox()
        for code, name in available_langs.items():
            self.language_combo.addItem(name, code)
        lang_label = QtWidgets.QLabel(tr.get("settings_language"))
        lang_label.setToolTip(tr.get("settings_language_tooltip"))
        form_layout.addRow(lang_label, self.language_combo)
        self.active_interval_spinbox = QtWidgets.QSpinBox()
        self.active_interval_spinbox.setMinimum(5); self.active_interval_spinbox.setMaximum(300); self.active_interval_spinbox.setSuffix(" s")
        active_label = QtWidgets.QLabel(tr.get("settings_active_interval"))
        active_label.setToolTip(tr.get("settings_active_tooltip"))
        form_layout.addRow(active_label, self.active_interval_spinbox)
        self.idle_interval_spinbox = QtWidgets.QSpinBox()
        self.idle_interval_spinbox.setMinimum(30); self.idle_interval_spinbox.setMaximum(3600); self.idle_interval_spinbox.setSuffix(" s")
        idle_label = QtWidgets.QLabel(tr.get("settings_idle_interval"))
        idle_label.setToolTip(tr.get("settings_idle_tooltip"))
        form_layout.addRow(idle_label, self.idle_interval_spinbox)
        self.autostart_checkbox = QtWidgets.QCheckBox(tr.get("settings_autostart"))
        self.autostart_checkbox.setToolTip(tr.get("settings_autostart_tooltip"))
        form_layout.addRow(self.autostart_checkbox)
        self.notifications_checkbox = QtWidgets.QCheckBox(tr.get("settings_notifications"))
        form_layout.addRow(self.notifications_checkbox)
        self.sound_checkbox = QtWidgets.QCheckBox(tr.get("settings_sound"))
        form_layout.addRow(self.sound_checkbox)
        layout.addLayout(form_layout)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.load_settings()

    def load_settings(self):
        self.active_interval_spinbox.setValue(self.settings.value("intervals/active", 10, type=int))
        self.idle_interval_spinbox.setValue(self.settings.value("intervals/idle", 50, type=int))
        self.autostart_checkbox.setChecked(self.settings.value("main/autostart", False, type=bool))
        self.notifications_checkbox.setChecked(self.settings.value("main/notifications", True, type=bool))
        self.sound_checkbox.setChecked(self.settings.value("main/sound", True, type=bool))
        if self.language_combo.findData(self.current_lang) != -1:
            self.language_combo.setCurrentIndex(self.language_combo.findData(self.current_lang))

    def accept(self):
        self.settings.setValue("intervals/active", self.active_interval_spinbox.value())
        self.settings.setValue("intervals/idle", self.idle_interval_spinbox.value())
        self.settings.setValue("main/autostart", self.autostart_checkbox.isChecked())
        self.settings.setValue("main/notifications", self.notifications_checkbox.isChecked())
        self.settings.setValue("main/sound", self.sound_checkbox.isChecked())
        self.settings.setValue("main/language", self.language_combo.currentData())
        set_autostart_shortcut(self.autostart_checkbox.isChecked())
        super().accept()

class TrayFlag(QtWidgets.QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        try:
            global sf, sd
            import soundfile as sf
            import sounddevice as sd
            self.sound_libs_available = True
        except ImportError:
            self.sound_libs_available = False

        self.current_location_data = {}
        self.location_history = deque(maxlen=3)
        self.idle_check_counter = 0
        self.IDLE_TRANSITION_THRESHOLD = 3
        self.is_idle_mode = False
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_location_icon)
        
        self.settings = QSettings(SETTINGS_FILE_PATH, QSettings.Format.IniFormat)
        
        self.i18n_dir = "assets/i18n"
        self.flags_dir = "assets/flags"
        self.icons_dir = "assets/icons"
        self.sounds_dir = "assets/sounds"
        
        self.tr = Translator(self.i18n_dir)
        self.load_app_settings()
        
        self.app_icon = self.load_app_icon()
        self.sound_samples, self.sound_samplerate = self.load_sound_file()
        
        self.create_menu()
        self.no_internet_icon = self.create_no_internet_icon()
        self.setIcon(self.app_icon or self.no_internet_icon)
        self.show()
        self.setToolTip(self.tr.get("initializing_tooltip"))
        
        self.activated.connect(self.on_activated)
        QtCore.QTimer.singleShot(100, self.update_location_icon)

    def load_app_settings(self):
        saved_lang = self.settings.value("main/language", "")
        if not saved_lang:
            system_lang, _ = locale.getdefaultlocale()
            saved_lang = system_lang[:2] if system_lang else "en"
        
        final_lang = self.tr.load_language(saved_lang)
        
        if not self.settings.contains("main/language"):
            self.settings.setValue("main/language", final_lang)

        self.active_interval = self.settings.value("intervals/active", 10, type=int)
        if not self.settings.contains("intervals/active"): self.settings.setValue("intervals/active", self.active_interval)
        
        self.idle_interval = self.settings.value("intervals/idle", 50, type=int)
        if not self.settings.contains("intervals/idle"): self.settings.setValue("intervals/idle", self.idle_interval)

        self.notifications_enabled = self.settings.value("main/notifications", True, type=bool)
        if not self.settings.contains("main/notifications"): self.settings.setValue("main/notifications", self.notifications_enabled)

        self.sound_enabled = self.settings.value("main/sound", True, type=bool)
        if not self.settings.contains("main/sound"): self.settings.setValue("main/sound", self.sound_enabled)

        self.autostart_enabled = self.settings.value("main/autostart", False, type=bool)
        if not self.settings.contains("main/autostart"): self.settings.setValue("main/autostart", self.autostart_enabled)
        
        self.reset_to_active_mode()

    def schedule_next_update(self):
        if self.is_idle_mode:
            interval_ms = self.idle_interval * 1000
        else:
            base_interval = self.active_interval
            jitter = base_interval * 0.20
            random_interval = random.uniform(base_interval - jitter, base_interval + jitter)
            interval_ms = int(random_interval * 1000)
        self.timer.start(interval_ms)

    def reset_to_active_mode(self):
        self.is_idle_mode = False
        self.idle_check_counter = 0
        self.schedule_next_update()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.app_icon, self.tr, self.tr.available_languages, self.tr.current_lang, self.menu)
        if dialog.exec():
            self.load_app_settings()
            self.recreate_ui()

    def recreate_ui(self):
        self.create_menu()
        if self.current_location_data:
            self.update_gui_with_new_data()
        else:
            self.setToolTip(self.tr.get("initializing_tooltip"))

    def open_about_dialog(self):
        dialog = AboutDialog(__version__, self.app_icon, self.tr, self.menu)
        dialog.exec()

    def update_location_icon(self, is_forced_by_user=False):
        if is_forced_by_user:
            if self.timer.isActive(): self.timer.stop()
            self.reset_to_active_mode()
        try:
            new_data = get_location_data()
            ip_changed = new_data['ip'] != self.current_location_data.get('ip')
            if not ip_changed:
                if is_forced_by_user:
                    if self.notifications_enabled:
                        self.showMessage(self.tr.get("ip_confirmed_title"), self.tr.get("ip_confirmed_message", ip=new_data.get('ip')), self.icon(), 3000)
                    self.play_notification_sound_threaded()
                else:
                    if not self.is_idle_mode:
                        self.idle_check_counter += 1
                        if self.idle_check_counter >= self.IDLE_TRANSITION_THRESHOLD:
                            self.is_idle_mode = True
            else:
                if self.current_location_data:
                    self.location_history.append(self.current_location_data)
                self.current_location_data = new_data
                self.update_gui_with_new_data()
                self.reset_to_active_mode()
                return
            if not is_forced_by_user:
                self.schedule_next_update()
        except (ConnectionError, ValueError) as e:
            self.setIcon(self.app_icon or self.no_internet_icon)
            self.setToolTip(self.tr.get("error_tooltip", error=str(e)))
            if not is_forced_by_user:
                self.schedule_next_update()

    def update_gui_with_new_data(self):
        data = self.current_location_data
        ip = data.get('ip', 'N/A'); city = data.get('city', 'N/A'); isp = data.get('isp', 'N/A')
        country_code = data.get('country_code', '')
        icon_filename = f"{country_code}.png"
        icon = self.load_icon_from_file(icon_filename)
        self.setIcon(icon if icon else self.app_icon or self.no_internet_icon)
        MAX_LEN = 17
        tooltip_text = (f"{ip}\n"
                        f"{country_code.upper()}\n"
                        f"{truncate_text(city, MAX_LEN)}\n"
                        f"{truncate_text(isp, MAX_LEN)}")
        self.setToolTip(tooltip_text)
        self.update_menu_content()
        if self.notifications_enabled:
            self.showMessage(self.tr.get("location_updated_title"), self.tr.get("location_updated_message", ip=ip, city=city, country_code=country_code.upper()), self.icon(), 5000)
        self.play_notification_sound_threaded()

    def play_notification_sound_threaded(self):
        if not self.sound_enabled or self.sound_samples is None or not self.sound_libs_available: return
        def sound_playback_task():
            try:
                sd.play(self.sound_samples, self.sound_samplerate); sd.wait()
            except Exception as e:
                print(f"Error in sound playback thread: {e}")
        sound_thread = threading.Thread(target=sound_playback_task); sound_thread.start()
        
    def create_menu(self):
        self.menu = QtWidgets.QMenu()
        self.ip_action = QtGui.QAction(self.tr.get("menu_ip_wait")); self.ip_action.setEnabled(False)
        self.city_action = QtGui.QAction(self.tr.get("menu_city_wait")); self.city_action.setEnabled(False)
        self.isp_action = QtGui.QAction(self.tr.get("menu_isp_wait")); self.isp_action.setEnabled(False)
        self.copy_ip_action = QtGui.QAction(self.tr.get("menu_copy_ip")); self.copy_ip_action.triggered.connect(self.copy_ip_to_clipboard); self.copy_ip_action.setEnabled(False)
        self.force_update_action = QtGui.QAction(self.tr.get("menu_update_now")); self.force_update_action.triggered.connect(lambda: self.update_location_icon(is_forced_by_user=True))
        self.weblink_action = QtGui.QAction(self.tr.get("menu_weblink")); self.weblink_action.triggered.connect(self.open_weblink); self.weblink_action.setEnabled(False)
        self.history_menu = QtWidgets.QMenu(self.tr.get("menu_history")); self.history_placeholder_action = QtGui.QAction(self.tr.get("menu_history_empty")); self.history_placeholder_action.setEnabled(False); self.history_menu.addAction(self.history_placeholder_action)
        self.settings_action = QtGui.QAction(self.tr.get("menu_settings")); self.settings_action.triggered.connect(self.open_settings_dialog)
        self.about_action = QtGui.QAction(self.tr.get("menu_about", app_name=APP_NAME)); self.about_action.triggered.connect(self.open_about_dialog)
        self.exit_action = QtGui.QAction(self.tr.get("menu_exit")); self.exit_action.triggered.connect(QtWidgets.QApplication.quit)
        self.menu.addAction(self.ip_action); self.menu.addAction(self.city_action); self.menu.addAction(self.isp_action); self.menu.addSeparator()
        self.menu.addAction(self.copy_ip_action); self.menu.addAction(self.force_update_action); self.menu.addSeparator()
        self.menu.addMenu(self.history_menu); self.menu.addAction(self.weblink_action); self.menu.addSeparator()
        self.menu.addAction(self.settings_action); self.menu.addAction(self.about_action); self.menu.addSeparator()
        self.menu.addAction(self.exit_action)
        self.setContextMenu(self.menu)

    def load_app_icon(self):
        try:
            icon_path = resource_path(os.path.join("assets", "icons", "logo.ico"))
            if not os.path.isfile(icon_path): raise FileNotFoundError(f"Logo file not found: {icon_path}")
            return QtGui.QIcon(icon_path)
        except Exception as e:
            print(f"Error loading logo: {e}"); return None

    def load_sound_file(self):
        if not self.sound_libs_available: return None, None
        try:
            sound_path = resource_path(os.path.join("assets", "sounds", "notification.wav"))
            if not os.path.isfile(sound_path): raise FileNotFoundError(f"Sound file not found: {sound_path}")
            return sf.read(sound_path, dtype='float32')
        except Exception as e:
            print(f"Error loading sound file: {e}"); return None, None

    def on_activated(self, reason):
        if reason == self.ActivationReason.Trigger: self.update_location_icon(is_forced_by_user=True)

    def copy_ip_to_clipboard(self):
        if self.current_location_data and 'ip' in self.current_location_data: self.copy_text_to_clipboard(self.current_location_data['ip'], self.tr.get("current_ip_source"))

    def copy_historical_ip(self, ip_to_copy): self.copy_text_to_clipboard(ip_to_copy, self.tr.get("historical_ip_source"))
    
    def copy_text_to_clipboard(self, text, source_name):
        QtWidgets.QApplication.clipboard().setText(text)
        if self.notifications_enabled:
            self.showMessage(self.tr.get("copied_title"), self.tr.get("copied_message", source_name=source_name, text=text), self.icon(), 2000)

    def open_weblink(self):
        if self.current_location_data and 'ip' in self.current_location_data: webbrowser.open(f"https://www.ip-tracker.org/lookup.php?ip={self.current_location_data['ip']}")

    def update_menu_content(self):
        ip = self.current_location_data.get('ip', 'N/A'); city = self.current_location_data.get('city', 'N/A'); isp = self.current_location_data.get('isp', 'N/A')
        self.ip_action.setText(self.tr.get("menu_ip_label", ip=ip)); self.city_action.setText(self.tr.get("menu_city_label", city=city)); self.isp_action.setText(self.tr.get("menu_isp_label", isp=isp))
        has_ip = ip != 'N/A'; self.copy_ip_action.setEnabled(has_ip); self.weblink_action.setEnabled(has_ip)
        self.history_menu.clear()
        if not self.location_history:
            self.history_menu.addAction(self.history_placeholder_action)
        else:
            for entry in reversed(self.location_history):
                historical_ip = entry.get('ip', 'N/A')
                text = f"{historical_ip} ({entry.get('country_code', '??').upper()}, {entry.get('city', 'N/A')})"
                action = QtGui.QAction(text, self.menu); action.triggered.connect(partial(self.copy_historical_ip, historical_ip)); self.history_menu.addAction(action)

    def create_no_internet_icon(self, size=20):
        pixmap = QtGui.QPixmap(size, size); pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap); painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        pen = QtGui.QPen(QtCore.Qt.GlobalColor.red); pen.setWidth(3); painter.setPen(pen)
        painter.drawLine(3, 3, size - 4, size - 4); painter.drawLine(size - 4, 3, 3, size - 4)
        painter.end(); return QtGui.QIcon(pixmap)

    def load_icon_from_file(self, filename, size=20):
        path = resource_path(os.path.join(self.flags_dir, filename))
        if not os.path.isfile(path): return None
        try:
            pixmap = QtGui.QPixmap(path)
            return None if pixmap.isNull() else QtGui.QIcon(pixmap.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"Error loading icon file: {path}: {e}"); return None

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray_icon = TrayFlag()
    sys.exit(app.exec())
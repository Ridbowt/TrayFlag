import sys
import os
import requests
import webbrowser
import json
import locale
import re
import random
from collections import deque
from functools import partial
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import QSettings
import threading

# =============================================================================
#  Глобальные переменные и константы
# =============================================================================
__version__ = "1.4.0" # <--- ВЕРСИЯ ОБНОВЛЕНА
APP_NAME = "TrayFlag"
ORG_NAME = "YourCompany" # <--- Имя вашей организации, можно любое

try:
    import soundfile as sf
    import sounddevice as sd
    sound_libs_available = True
except ImportError:
    print(f"WARNING: soundfile/sounddevice libraries not found. Sound will be disabled.")
    sound_libs_available = False

# =============================================================================
#  КЛЮЧЕВЫЕ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================

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
        # return os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # <--- ПРИ ЗАПУСКЕ .PY СКРИПТА
        return os.path.dirname(os.path.abspath(__file__)) # <--- ПРИ ЗАПУСКЕ .EXE ПРИЛОЖЕНИЯ
def resource_path(relative_path):
    """
    Возвращает полный путь к файлу ресурсов.
    """
    return os.path.join(get_base_path(), relative_path)

# Определение пути к файлу настроек .ini
SETTINGS_FILE_PATH = os.path.join(get_base_path(), f"{APP_NAME}.ini")

# --- Функция для обеспечения существования INI-файла ---
def ensure_ini_file_exists(file_path):
    """
    Проверяет, существует ли INI-файл по указанному пути.
    Если нет, создает его с минимальным содержимым.
    """
    if not os.path.exists(file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"[{APP_NAME}]\n")
                f.write(f"version = {__version__}\n") # <--- ИЗМЕНЕНО
            print(f"Created new INI file at: {file_path}")
        except Exception as e:
            print(f"ERROR: Could not create INI file at {file_path}: {e}")

# --- НОВАЯ ФУНКЦИЯ: Получение только внешнего IP ---
def get_current_external_ip():
    """
    Получает только текущий внешний IP-адрес с легкого сервиса ipify.org.
    """
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('ip', 'N/A')
    except requests.RequestException as e:
        print(f"Warning: Failed to get external IP from ipify.org: {e}")
        return "N/A"
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to decode JSON from ipify.org: {e}")
        return "N/A"

# --- ПЕРЕИМЕНОВАНА и ИЗМЕНЕНА: Получение полных данных о геолокации ---
def get_location_data_full(ip_address): # <--- Теперь принимает IP-адрес
    """
    Получает полные данные о местоположении для заданного IP-адреса,
    пробуя несколько сервисов по очереди.
    """
    if ip_address == "N/A" or not ip_address:
        raise ValueError("Cannot get full location data for 'N/A' or empty IP address.")

    services = [
        f"http://ip-api.com/json/{ip_address}?fields=status,message,countryCode,city,isp,query", # ПЕРВЫЙ ПРИОРИТЕТ, HTTP
        f"https://ipinfo.io/{ip_address}/json" # ВТОРОЙ ПРИОРИТЕТ, HTTPS, без токена
    ]

    for url in services:
        print(f"Attempting to get full data for {ip_address} from: {url}")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            print(f"Successfully received full data from {url}: {data}")

            if "ip-api.com" in url:
                if data.get('status') == 'success':
                    return {
                        'ip': data.get('query', 'N/A'), 
                        'country_code': data.get('countryCode', '').lower(), 
                        'city': data.get('city', 'N/A'), 
                        'isp': data.get('isp', 'N/A')
                    }
                else:
                    print(f"Service {url} returned status: {data.get('status')} - {data.get('message')}")
                    continue 
            
            elif "ipinfo.io" in url:
                return {
                    'ip': data.get('ip', 'N/A'),
                    'country_code': data.get('country', '').lower(),
                    'city': data.get('city', 'N/A'),
                    'isp': data.get('org', 'N/A')
                }

        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to get full data from {url}. Error: {e}")
            continue
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to decode JSON from {url}. Error: {e}")
            continue

    raise ConnectionError(f"All full IP data services are unavailable for IP: {ip_address}.")

def clean_isp_name(isp_name):
    """
    Очищает имя провайдера, удаляя номера автономных систем (AS) и общие префиксы/суффиксы.
    """
    if not isp_name:
        return "N/A"

    isp_name = re.sub(r'\bAS\d+\b', '', isp_name, flags=re.IGNORECASE).strip()
    isp_name = re.sub(r'\(\s*AS\d+\s*\)', '', isp_name, flags=re.IGNORECASE).strip()

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

    if not isp_name:
        return "N/A"
    
    return isp_name


def set_autostart_shortcut(enabled):
    """ Creates or deletes a shortcut in the Windows startup folder. """
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
        main_exe_path = os.path.join(get_base_path(), f"{APP_NAME}.exe")
        
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = main_exe_path
        shortcut.Arguments = "" 
        shortcut.WindowStyle = 1
        shortcut.IconLocation = resource_path(os.path.join("assets", "icons", "logo.ico"))
        shortcut.Description = f"Start {APP_NAME}"
        shortcut.WorkingDirectory = get_base_path()
        shortcut.save()
        print(f"Autostart shortcut created at: {shortcut_path}")
    else:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print(f"Autostart shortcut removed from: {shortcut_path}")

def truncate_text(text, max_length):
    """ Truncates text to max_length and appends '...' if it's longer. """
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text

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
        if not os.path.isdir(path):
            print(f"Warning: i18n directory not found at {path}")
            return langs
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
            print(f"Language '{self.current_lang}' loaded successfully.")
        except Exception as e:
            print(f"Failed to load language '{self.current_lang}': {e}. Loading default.")
            if self.current_lang != self.default_lang:
                self.load_language(self.default_lang)
        return self.current_lang

    def get(self, key, **kwargs):
        text = self.translations.get(key, f"<{key}>")
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text

    # <--- НОВЫЕ СТРОКИ ЛОКАЛИЗАЦИИ
    def add_new_strings(self):
        if self.current_lang == "Russian":
            self.translations.update({
                "no_external_ip_detected": "Внешний IP не обнаружен.",
                "full_data_unavailable": "Полные данные недоступны для {ip}: {error_msg}",
                "could_not_get_any_ip_data": "Не удалось получить никаких данных об IP.",
                "unexpected_error_occurred": "Произошла непредвиденная ошибка: {error_msg}"
            })
        else: # English
            self.translations.update({
                "no_external_ip_detected": "No external IP detected.",
                "full_data_unavailable": "Full data unavailable for {ip}: {error_msg}",
                "could_not_get_any_ip_data": "Could not get any IP data.",
                "unexpected_error_occurred": "An unexpected error occurred: {error_msg}"
            })
        
# <--- Изменения в AboutDialog (release_date)
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
        release_date = "2025-07-11" # <--- ОБНОВЛЕНА ДАТА РЕЛИЗА
        version_label = QtWidgets.QLabel(tr.get("about_version", version=version, release_date=release_date))
        version_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        website_label = QtWidgets.QLabel(f'<a href="https://github.com/Ridbowt/TrayFlag">{tr.get("about_website")}</a>')
        website_label.setOpenExternalLinks(True)
        website_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        acknowledgements_box = QtWidgets.QGroupBox(tr.get("about_acknowledgements"))
        ack_layout = QtWidgets.QVBoxLayout()
        ack_html = (
            f"<style>ul {{ list-style-type: none; padding-left: 0; margin-left: 0; }} li {{ margin-bottom: 5px; }}</style>"
            f"<ul>"
            f"{tr.get('ack_ip_services')}"
            f"{tr.get('ack_flags')}"
            f"{tr.get('ack_app_icon')}"
            f"{tr.get('ack_logo_builder')}"
            f"{tr.get('ack_sound')}"
            f"{tr.get('ack_code')}"
            f"{tr.get('ack_ai')}"
            f"</ul>"
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
        
        ensure_ini_file_exists(SETTINGS_FILE_PATH)
        self.settings = QSettings(SETTINGS_FILE_PATH, QSettings.Format.IniFormat)
        
        layout = QtWidgets.QVBoxLayout(self)
        form_layout = QtWidgets.QFormLayout()
        self.language_combo = QtWidgets.QComboBox()
        for code, name in available_langs.items():
            self.language_combo.addItem(name, code)
        lang_label = QtWidgets.QLabel(tr.get("settings_language"))
        lang_label.setToolTip(tr.get("settings_language_tooltip"))
        form_layout.addRow(lang_label, self.language_combo)
        self.update_interval_spinbox = QtWidgets.QSpinBox()
        self.update_interval_spinbox.setMinimum(4); self.update_interval_spinbox.setMaximum(300); self.update_interval_spinbox.setSuffix(" s")
        active_label = QtWidgets.QLabel(tr.get("settings_update_interval"))
        active_label.setToolTip(tr.get("settings_update_tooltip"))
        form_layout.addRow(active_label, self.update_interval_spinbox)
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
        self.update_interval_spinbox.setValue(self.settings.value("intervals/active", 7, type=int))
        self.autostart_checkbox.setChecked(self.settings.value("main/autostart", False, type=bool))
        self.notifications_checkbox.setChecked(self.settings.value("main/notifications", True, type=bool))
        self.sound_checkbox.setChecked(self.settings.value("main/sound", True, type=bool))
        if self.language_combo.findData(self.current_lang) != -1:
            self.language_combo.setCurrentIndex(self.language_combo.findData(self.current_lang))

    def accept(self):
        self.settings.setValue("intervals/active", self.update_interval_spinbox.value())
        self.settings.setValue("main/autostart", self.autostart_checkbox.isChecked())
        self.settings.setValue("main/notifications", self.notifications_checkbox.isChecked())
        self.settings.setValue("main/sound", self.sound_checkbox.isChecked())
        self.settings.setValue("main/language", self.language_combo.currentData())
        set_autostart_shortcut(self.autostart_checkbox.isChecked())
        super().accept()

class TrayFlag(QtWidgets.QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        
        self.current_location_data = {}
        self.location_history = deque(maxlen=3)
        self.last_known_external_ip = ""

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_location_icon)
        
        ensure_ini_file_exists(SETTINGS_FILE_PATH)
        self.settings = QSettings(SETTINGS_FILE_PATH, QSettings.Format.IniFormat)
        
        self.i18n_dir = "assets/i18n"
        self.flags_dir = "assets/flags"
        
        self.tr = Translator(self.i18n_dir)
        self.tr.add_new_strings()
        self.load_app_settings()
        
        # ИЗМЕНЕНИЕ: Загрузка двух звуковых файлов
        self.app_icon = self.load_app_icon()
        self.sound_samples, self.sound_samplerate = self.load_sound_file("notification.wav")
        self.alert_sound_samples, self.alert_sound_samplerate = self.load_sound_file("alert.wav")
        
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

        # --- ДОБАВЛЕНА ЛОГИКА ОБНОВЛЕНИЯ ВЕРСИИ INI-ФАЙЛА ---
        current_ini_version = self.settings.value(f"{APP_NAME}/version", "0.0.0", type=str) # Получаем версию из INI
        if current_ini_version != __version__:
            print(f"INFO: INI version mismatch. Updating from {current_ini_version} to {__version__}.")
            self.settings.setValue(f"{APP_NAME}/version", __version__) # Обновляем версию в INI
            # Здесь можно добавить логику миграции настроек, если версии сильно отличаются
            # Например, если в новой версии изменились названия ключей и т.д.
            # Пока просто обновляем версию.
        # --- КОНЕЦ ЛОГИКИ ОБНОВЛЕНИЯ ВЕРСИИ ---

        self.update_interval = self.settings.value("intervals/active", 7, type=int)
        if not self.settings.contains("intervals/active"): self.settings.setValue("intervals/active", self.update_interval)
        
        self.notifications_enabled = self.settings.value("main/notifications", True, type=bool)
        if not self.settings.contains("main/notifications"): self.settings.setValue("main/notifications", self.notifications_enabled)

        self.sound_enabled = self.settings.value("main/sound", True, type=bool)
        if not self.settings.contains("main/sound"): self.settings.setValue("main/sound", self.sound_enabled)

        self.autostart_enabled = self.settings.value("main/autostart", False, type=bool)
        if not self.settings.contains("main/autostart"): self.settings.setValue("main/autostart", self.autostart_enabled)
        
        self.reset_to_active_mode()

    def schedule_next_update(self):
        # ИЗМЕНЕНИЕ В schedule_next_update: УДАЛЕНИЕ ЛОГИКИ IDLE MODE
        # Теперь всегда используется update_interval
        base_interval = self.update_interval # Всегда используем активный интервал
        jitter_amount = 3 # Джиттер 4-10 сек, среднее 7 сек.
        random_interval = random.uniform(base_interval - jitter_amount, base_interval + jitter_amount)
        
        interval_ms = int(random_interval * 1000)
        if interval_ms < 1000: # Минимум 1 секунда
            interval_ms = 1000

        self.timer.start(interval_ms)

    def reset_to_active_mode(self):
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
            current_external_ip = get_current_external_ip()
            
            # ИЗМЕНЕНИЕ В update_location_icon: ОБНОВЛЕНИЕ ЛОГИКИ ОБРАБОТКИ IP И GUI
            # Мы хотим обновить GUI, если IP изменился ИЛИ если он был N/A и стал реальным
            # ИЛИ если это принудительное обновление.

            # Флаг, указывающий, нужно ли обновить GUI и сбросить режим
            should_update_gui_and_reset = False

            if current_external_ip == "N/A":
                # Если IP не обнаружен, всегда показываем иконку "нет интернета"
                self.setIcon(self.app_icon or self.no_internet_icon)
                self.setToolTip(self.tr.get("error_tooltip", error=self.tr.get("no_external_ip_detected")))
                
                # Если последний известный IP был реальным, а теперь N/A, это считается изменением
                if self.last_known_external_ip != "N/A":
                    should_update_gui_and_reset = True
                    # ДОБАВЛЕНО: Уведомление и звук при потере сети
                    if self.notifications_enabled:
                        self.showMessage(self.tr.get("network_lost_title"), self.tr.get("network_lost_message"), self.icon(), 5000)
                        self.play_alert_sound_threaded()
                
                # Обновляем last_known_external_ip на N/A, чтобы отслеживать переход
                self.last_known_external_ip = "N/A" 

            else: # current_external_ip НЕ "N/A" (получен реальный IP)
                # Если IP изменился (включая переход из N/A в реальный)
                if current_external_ip != self.last_known_external_ip:
                    should_update_gui_and_reset = True
                
                # Если это принудительное обновление, всегда обновляем GUI
                if is_forced_by_user:
                    should_update_gui_and_reset = True

                # Пытаемся получить полные данные
                new_data = None
                try:
                    new_data = get_location_data_full(current_external_ip)
                except (ConnectionError, ValueError) as e:
                    # Если не удалось получить полные данные, но IP известен, используем частичные
                    new_data = {'ip': current_external_ip, 'country_code': '??', 'city': 'N/A', 'isp': 'N/A'}
                    print(f"Warning: Failed to get full data for {current_external_ip}: {e}")
                
                # Если данные получены (даже частичные)
                if new_data and new_data.get('ip') != 'N/A':
                    self.last_known_external_ip = new_data['ip'] # Обновляем последний известный IP
                    
                    # Обновляем историю и текущие данные
                    if self.current_location_data:
                        self.location_history.append(self.current_location_data)
                    self.current_location_data = new_data
                    
                    # Если нужно обновить GUI (IP изменился или принудительное обновление)
                    if should_update_gui_and_reset:
                        self.update_gui_with_new_data()
                else:
                    # Если даже после попытки получить полные данные, ничего не вышло (очень редкий случай)
                    self.setIcon(self.app_icon or self.no_internet_icon)
                    self.setToolTip(self.tr.get("error_tooltip", error=self.tr.get("could_not_get_any_ip_data")))
                    should_update_gui_and_reset = True # Считаем это изменением, чтобы сбросить таймер

            # В конце, если нужно обновить GUI и сбросить режим, делаем это
            if should_update_gui_and_reset:
                self.reset_to_active_mode() # Всегда сбрасываем в активный режим (который теперь единственный)
            else:
                # Если IP не изменился и не было принудительного обновления,
                # просто планируем следующее обновление (таймер всегда в активном режиме)
                self.schedule_next_update()


        except Exception as e:
            # Обработка любых непредвиденных ошибок
            self.setIcon(self.app_icon or self.no_internet_icon)
            self.setToolTip(self.tr.get("error_tooltip", error=self.tr.get("unexpected_error_occurred", error_msg=str(e))))
            print(f"CRITICAL ERROR in update_location_icon: {e}")
            # В случае критической ошибки, всегда сбрасываем в активный режим
            self.reset_to_active_mode()

    def update_gui_with_new_data(self):
        data = self.current_location_data
        ip = data.get('ip', 'N/A'); city = data.get('city', 'N/A')
        isp = clean_isp_name(self.current_location_data.get('isp', 'N/A'))
        country_code = self.current_location_data.get('country_code', '')
        icon_filename = f"{country_code}.png"
        icon = self.load_icon_from_file(icon_filename)
        self.setIcon(icon if icon else self.app_icon or self.no_internet_icon)
        MAX_LEN = 17
        tooltip_text = (f"{ip}\n"
                        f"{country_code.upper()}\n"
                        f"{truncate_text(city, MAX_LEN)}\n"
                        f"{truncate_text(isp, MAX_LEN)}")
        self.setToolTip(tooltip_text)
        self.update_menu_content() # <--- ЭТУ СТРОКУ НУЖНО БЫЛО УДАЛИТЬ (причина RecursionError)
        if self.notifications_enabled:
            self.showMessage(self.tr.get("location_updated_title"), self.tr.get("location_updated_message", ip=ip, city=city, country_code=country_code.upper()), self.icon(), 5000)
        self.play_notification_sound_threaded()

    # ИЗМЕНЕНИЕ: load_sound_file теперь принимает имя файла
    def load_sound_file(self, filename):
        if not sound_libs_available: return None, None
        try:
            sound_path = resource_path(os.path.join("assets", "sounds", filename))
            if not os.path.isfile(sound_path): raise FileNotFoundError(f"Sound file not found: {sound_path}")
            return sf.read(sound_path, dtype='float32')
        except Exception as e:
            print(f"Error loading sound file: {e}"); return None, None

    def play_notification_sound_threaded(self):
        if not sound_libs_available or self.sound_samples is None: return
        def sound_playback_task():
            try:
                sd.play(self.sound_samples, self.sound_samplerate); sd.wait()
            except Exception as e:
                print(f"Error in sound playback thread: {e}")
        sound_thread = threading.Thread(target=sound_playback_task); sound_thread.start()

    # ДОБАВЛЕНО: Новый метод для проигрывания аварийного звука
    def play_alert_sound_threaded(self):
        if not sound_libs_available or self.alert_sound_samples is None: return
        def sound_playback_task():
            try:
                sd.play(self.alert_sound_samples, self.alert_sound_samplerate); sd.wait()
            except Exception as e:
                print(f"Error in alert sound playback thread: {e}")
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

    def load_sound_file(self, filename): # <--- ИЗМЕНЕНО
        if not sound_libs_available: return None, None
        try:
            sound_path = resource_path(os.path.join("assets", "sounds", filename)) # <--- ИЗМЕНЕНО
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
        if self.current_location_data and 'ip' in self.current_location_data:
            webbrowser.open(f"https://www.ip-tracker.org/lookup.php?ip={self.current_location_data['ip']}")

    def update_menu_content(self):
        ip = self.current_location_data.get('ip', 'N/A'); city = self.current_location_data.get('city', 'N/A')
        isp = clean_isp_name(self.current_location_data.get('isp', 'N/A'))
        self.ip_action.setText(self.tr.get("menu_ip_label", ip=ip)); self.city_action.setText(self.tr.get("menu_city_label", city=city)); self.isp_action.setText(self.tr.get("menu_isp_label", isp=isp))
        has_ip = ip != 'N/A'; self.copy_ip_action.setEnabled(has_ip); self.weblink_action.setEnabled(has_ip)
        self.history_menu.clear()
        if not self.location_history:
            self.history_menu.addAction(self.history_placeholder_action)
        else:
            for entry in reversed(self.location_history):
                historical_ip = entry.get('ip', 'N/A')
                historical_isp = clean_isp_name(entry.get('isp', 'N/A'))
                text = f"{historical_ip} ({entry.get('country_code', '??').upper()}, {entry.get('city', 'N/A')}, {historical_isp})"
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
            print(f"Error loading icon file: {e}"); return None

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    
    app.setQuitOnLastWindowClosed(False)
    
    tray_icon = TrayFlag()
    
    sys.exit(app.exec())
# File: src/app.py (ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ)

import time
import os
import random
import threading
import webbrowser
from collections import deque
from PyQt6 import QtWidgets, QtGui, QtCore

from utils import resource_path, create_no_internet_icon, set_autostart_shortcut, truncate_text, clean_isp_name
from config import ConfigManager
from constants import APP_NAME, ORG_NAME, __version__, RELEASE_DATE
from translator import Translator, get_initial_language_code
from ip_fetcher import get_ip_data_from_go
from dialogs import AboutDialog, SettingsDialog
from tray_menu import TrayMenuManager
import idle_detector


try:
    import soundfile as sf
    import sounddevice as sd
    sound_libs_available = True
except ImportError:
    sound_libs_available = False

class App(QtWidgets.QSystemTrayIcon):
    # --- НАЧАЛО КОДА ДЛЯ ЗАМЕНЫ ---
    def __init__(self):
        super().__init__()
        
        self.config = ConfigManager()
        self.tr = Translator(resource_path("assets/i18n"))
        
        self.current_location_data = {}
        self.location_history = deque(maxlen=3)
        self.last_known_external_ip = ""
        self.is_in_idle_mode = False
        
        # Переменные для хранения окон
        self.settings_dialog = None
        self.about_dialog = None
        
        # Таймеры
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.main_update_loop)  
        
        self.load_app_settings()
        
        self.app_icon = self._load_icon("logo.ico")
        self.moon_icon = self._load_icon("moon.png")
        self.no_internet_icon = create_no_internet_icon()
        
        self.sound_samples, self.sound_samplerate = self._load_sound_file("notification.wav")
        self.alert_sound_samples, self.alert_sound_samplerate = self._load_sound_file("alert.wav")
        
        self.menu_manager = TrayMenuManager(self)
        self.setContextMenu(self.menu_manager.menu)
        
        self.setIcon(self.app_icon or self.no_internet_icon)
        self.show()
        self.setToolTip(self.tr.get("initializing_tooltip"))
        
        self.activated.connect(self.on_activated)
        QtCore.QTimer.singleShot(100, self.main_update_loop)
    
    def load_app_settings(self):
        cfg = self.config
        lang_code = get_initial_language_code(cfg.language)
        cfg.language = lang_code # Синхронизируем объект конфига с реальным языком
        self.tr.load_language(lang_code)
        
        self.update_interval_ms = cfg.update_interval * 1000
        self.notifications_enabled = cfg.notifications
        self.sound_enabled = cfg.sound
        self.idle_enabled = cfg.idle_enabled
        self.idle_threshold_seconds = cfg.idle_threshold_mins * 60
        self.idle_interval_ms = cfg.idle_interval_mins * 60 * 1000
        
        self.reset_to_active_mode()

    def check_for_wakeup(self):
        """Вызывается каждую секунду для проверки выхода из простоя."""
        if not self.is_in_idle_mode:
            return
        if not idle_detector.is_user_idle(self.idle_threshold_seconds):
            self.exit_idle_mode()

    def main_update_loop(self):
        """Основной цикл, вызываемый по главному таймеру."""
        if self.idle_enabled and not self.is_in_idle_mode:
            if idle_detector.is_user_idle(self.idle_threshold_seconds):
                self.enter_idle_mode()
                return
        self.update_location_icon()

    def enter_idle_mode(self):
        if self.is_in_idle_mode: return
        self.is_in_idle_mode = True
        print("Entering idle mode...")
        self.setIcon(self.moon_icon or self.app_icon)
        self.setToolTip(self.tr.get("idle_mode_tooltip"))
        self.timer.start(self.idle_interval_ms)

    def exit_idle_mode(self):
        if not self.is_in_idle_mode: return
        self.is_in_idle_mode = False
        print("Exiting idle mode...")
        self.update_location_icon(is_forced_by_user=True)

    def schedule_next_update(self):
        if self.is_in_idle_mode:
            self.timer.start(self.idle_interval_ms)
        else:
            # --- НАЧАЛО НОВОЙ ЛОГИКИ С ПРОЦЕНТНЫМ ДЖИТТЕРОМ ---
            base_interval_seconds = self.config.update_interval
            
            # 1. Вычисляем джиттер как 30% от базового интервала
            jitter_amount_seconds = base_interval_seconds * 0.30
            
            # 2. Определяем минимальную и максимальную границы
            min_interval = base_interval_seconds - jitter_amount_seconds
            max_interval = base_interval_seconds + jitter_amount_seconds
            
            # 3. Генерируем случайный интервал в этих границах
            random_interval_seconds = random.uniform(min_interval, max_interval)
            
            # 4. Округляем до ближайшего целого числа секунд
            rounded_seconds = round(random_interval_seconds)
            
            # 5. Превращаем в миллисекунды
            interval_ms = rounded_seconds * 1000
            
            # 6. Гарантируем, что интервал не меньше 1 секунды
            final_interval_ms = max(1000, interval_ms)
            
            self.timer.start(final_interval_ms)

    def reset_to_active_mode(self):
        self.is_in_idle_mode = False
        self.schedule_next_update()

# File: src/app.py

    def update_location_icon(self, is_forced_by_user=False):
        if is_forced_by_user:
            if self.timer.isActive(): self.timer.stop()
            self.reset_to_active_mode()

        ip_data = get_ip_data_from_go()
        
        if not ip_data or ip_data.get('ip') == "N/A":
            self.setIcon(self.no_internet_icon)
            self.setToolTip(self.tr.get("error_tooltip", error=self.tr.get("no_external_ip_detected")))
            self.base_tooltip_text = ""
            if self.last_known_external_ip != "N/A": self.play_alert_sound_threaded()
            self.last_known_external_ip = "N/A"
        else:
            # --- НАЧАЛО ИЗМЕНЕНИЙ ---
            
            # 1. Сразу обновляем время, так как запрос был успешным
            self.last_update_time = time.time()
            
            current_ip = ip_data.get('ip')
            full_data = ip_data.get('full_data', {})
            
            # 2. Проверяем, изменился ли IP или это принудительное обновление
            if current_ip != self.last_known_external_ip or is_forced_by_user:
                # Если да, то обновляем ВСЕ данные (флаг, меню, и т.д.)
                if full_data: self.current_location_data = full_data
                else: self.current_location_data = {'ip': current_ip, 'country_code': '??', 'city': 'N/A', 'isp': 'N/A'}
                
                if self.last_known_external_ip != current_ip:
                    if self.location_history and self.location_history[-1]['ip'] != self.current_location_data['ip']:
                        self.location_history.append(self.current_location_data)
                    elif not self.location_history:
                        self.location_history.append(self.current_location_data)
                
                self.last_known_external_ip = current_ip
                self.update_gui_with_new_data() # Эта функция обновит и базовый тултип
            # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        
        if not is_forced_by_user:
            self.schedule_next_update()

# File: src/app.py

# File: src/app.py

    def update_gui_with_new_data(self):
        data = self.current_location_data
        country_code = data.get('country_code', '')
        icon = self._load_icon(f"{country_code}.png", "flags")
        self.setIcon(icon or self.app_icon)
        
        # --- НАЧАЛО НОВОЙ, ПРОСТОЙ ЛОГИКИ ТУЛТИПА ---
        
        # Получаем текущее время в формате ЧЧ:ММ:СС
        update_time_str = time.strftime("%H:%M:%S")
        
        # Формируем полный тултип со статичным временем
        tooltip_text = (f"{data.get('ip', 'N/A')}\n"
                        f"{country_code.upper()}\n"
                        f"{truncate_text(data.get('city', 'N/A'), 17)}\n"
                        f"{truncate_text(clean_isp_name(data.get('isp', 'N/A')), 17)}\n"
                        f"({self.tr.get('tooltip_updated_at', time=update_time_str)})")
        
        self.setToolTip(tooltip_text)
        # --- КОНЕЦ НОВОЙ ЛОГИКИ ---
        
        self.menu_manager.update_menu_content()
        
        if self.notifications_enabled:
            self.showMessage(self.tr.get("location_updated_title"), 
                             self.tr.get("location_updated_message", ip=data.get('ip'), city=data.get('city'), country_code=country_code.upper()), 
                             self.icon(), 5000)
        self.play_notification_sound_threaded()

    def reload_ui_texts(self):
        """Перезагружает все тексты в UI после смены языка."""
        # Создаем новый объект переводчика
        self.tr = Translator(resource_path("assets/i18n"))
        lang_code = get_initial_language_code(self.config.language)
        self.tr.load_language(lang_code)
        
        # Пересоздаем меню с новым переводчиком
        self.menu_manager = TrayMenuManager(self)
        self.setContextMenu(self.menu_manager.menu)
        
        # Обновляем содержимое меню (без звука!)
        if self.current_location_data:
            self.menu_manager.update_menu_content()
        
        # Обновляем тултип
        if self.is_in_idle_mode:
            self.setToolTip(self.tr.get("idle_mode_tooltip"))
        elif self.current_location_data:
            # Обновляем тултип с данными, используя truncate_text и clean_isp_name
            data = self.current_location_data
            country_code = data.get('country_code', '')
            tooltip_text = (f"{data.get('ip', 'N/A')}\n"
                            f"{country_code.upper()}\n"
                            f"{truncate_text(data.get('city', 'N/A'), 17)}\n"
                            f"{truncate_text(clean_isp_name(data.get('isp', 'N/A')), 17)}")
            self.setToolTip(tooltip_text)
        else:
            self.setToolTip(self.tr.get("initializing_tooltip"))
      
# --- НАЧАЛО БЛОКА ДЛЯ ЗАМЕНЫ ---
    def open_settings_dialog(self):
        # Если окно уже существует, выводим его на передний план и выходим
        if self.settings_dialog and self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return

        # Если окна нет, создаем его и сохраняем ссылку
        self.settings_dialog = SettingsDialog(self.app_icon, self.tr, self.tr.available_languages, self.config, None)
        
        # Привязываем наши действия к сигналам закрытия окна
        self.settings_dialog.accepted.connect(self.on_settings_accepted)
        self.settings_dialog.rejected.connect(self.on_settings_rejected)
        
        # Показываем окно (неблокирующий вызов)
        self.settings_dialog.show()

    def on_settings_accepted(self):
        """Вызывается при нажатии OK в настройках."""
        if not self.settings_dialog: return

        # Запоминаем старый язык
        old_lang = self.config.language
        
        # Получаем и сохраняем новые настройки
        new_settings = self.settings_dialog.get_settings()
        self.config.save_settings(new_settings)
        set_autostart_shortcut(new_settings['autostart'])
        self.load_app_settings()
        
        # Если язык изменился, обновляем UI
        if old_lang != self.config.language:
            self.reload_ui_texts()
            
        self.settings_dialog = None  # Сбрасываем ссылку

    def on_settings_rejected(self):
        """Вызывается при нажатии Cancel или крестика."""
        if not self.settings_dialog: return
        self.settings_dialog = None # Просто сбрасываем ссылку
    # --- КОНЕЦ БЛОКА ДЛЯ ЗАМЕНЫ ---

    def open_about_dialog(self):
        # Если окно уже создано и видимо, выводим его на передний план и выходим
        if self.about_dialog and self.about_dialog.isVisible():
            self.about_dialog.raise_()
            self.about_dialog.activateWindow()
            return

        # Если окна нет, создаем его, сохраняем ссылку и показываем
        self.about_dialog = AboutDialog(self.app_icon, self.tr, __version__, RELEASE_DATE, None)
        self.about_dialog.exec()

    def on_activated(self, reason):
        if self.is_in_idle_mode:
            self.exit_idle_mode()
        elif reason == self.ActivationReason.Trigger:
            self.update_location_icon(is_forced_by_user=True)

    def _load_icon(self, filename, subfolder="icons", size=20):
        try:
            path = resource_path(os.path.join("assets", subfolder, filename))
            if not os.path.isfile(path): return None
            pixmap = QtGui.QPixmap(path)
            return QtGui.QIcon(pixmap.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"Error loading icon {filename}: {e}"); return None

    def _load_sound_file(self, filename):
        if not sound_libs_available: return None, None
        try:
            path = resource_path(os.path.join("assets", "sounds", filename))
            return sf.read(path, dtype='float32')
        except Exception as e:
            print(f"Error loading sound {filename}: {e}"); return None, None

    def play_notification_sound_threaded(self):
        if not self.sound_enabled: return
        self._start_sound_thread(self.sound_samples, self.sound_samplerate)

    def play_alert_sound_threaded(self):
        if not self.sound_enabled: return
        self._start_sound_thread(self.alert_sound_samples, self.alert_sound_samplerate)

    def _start_sound_thread(self, samples, samplerate):
        if not sound_libs_available or samples is None: return
        threading.Thread(target=self._play_sound_task, args=(samples, samplerate)).start()

    def _play_sound_task(self, samples, samplerate):
        try:
            sd.play(samples, samplerate); sd.wait()
        except Exception as e:
            print(f"Error in sound playback thread: {e}")

    def copy_ip_to_clipboard(self):
        if self.current_location_data and 'ip' in self.current_location_data:
            self.copy_text_to_clipboard(self.current_location_data['ip'])

    def copy_historical_ip(self, ip_to_copy):
        self.copy_text_to_clipboard(ip_to_copy)
    
    def copy_text_to_clipboard(self, text):
        QtWidgets.QApplication.clipboard().setText(text)
        if self.notifications_enabled:
            self.showMessage(self.tr.get("copied_title"), self.tr.get("copied_message_simple", text=text), self.icon(), 2000)

    def open_weblink(self):
        if self.current_location_data and 'ip' in self.current_location_data:
            webbrowser.open(f"https://www.ip-tracker.org/lookup.php?ip={self.current_location_data['ip']}")

    def open_speedtest_website(self):
        """Просто открывает сайт Speedtest.net в браузере по умолчанию."""
        webbrowser.open('https://www.speedtest.net')
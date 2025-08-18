# File: src/app.py (ФИНАЛЬНАЯ ВЕРСИЯ С ДВУМЯ УЛУЧШЕНИЯМИ)

import time
import os
import random
import threading
import webbrowser
from collections import deque
from PySide6 import QtWidgets, QtGui, QtCore

from utils import resource_path, create_no_internet_icon, set_autostart_shortcut, truncate_text, clean_isp_name, create_desktop_shortcut 
from config import ConfigManager, SETTINGS_FILE_PATH
from constants import __version__, RELEASE_DATE
from translator import Translator, get_initial_language_code
from ip_fetcher import get_ip_data_from_rust
from dialogs import AboutDialog, SettingsDialog, CustomQuestionDialog
from tray_menu import TrayMenuManager
import idle_detector

try:
    import soundfile as sf
    import sounddevice as sd
    sound_libs_available = True
except ImportError:
    sound_libs_available = False

class App(QtWidgets.QSystemTrayIcon):
    ipDataReceived = QtCore.Signal(object, bool) # (ip_data, is_forced)
    def __init__(self):
        super().__init__()

        self.ipDataReceived.connect(self.on_ip_data_received)
        
        self.config = ConfigManager()
        self.tr = Translator(resource_path("assets/i18n"))
        
        self.current_location_data = {}
        self.location_history = deque(maxlen=3)
        self.last_known_external_ip = ""
        self.is_in_idle_mode = False
        
        self.settings_dialog = None
        self.about_dialog = None
        
        # --- ВОЗВРАЩАЕМ НЕДОСТАЮЩИЕ ПЕРЕМЕННЫЕ ---
        self.last_update_time = 0
        self.base_tooltip_text = ""

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.main_update_loop)
        
        self.idle_check_timer = QtCore.QTimer()
        self.idle_check_timer.setInterval(1000)
        self.idle_check_timer.timeout.connect(self.on_second_tick)
        self.idle_check_timer.start()
        
        self.load_app_settings()
        
        self.app_icon = self._load_icon("logo.ico")
        self.moon_icon = self._load_icon("moon.png")
        self.no_internet_icon = create_no_internet_icon()
        self.about_logo_pixmap = self._load_pixmap("about_logo.png", 96)
        
        self.sound_samples, self.sound_samplerate = self._load_sound_file(f"notification_{self.volume_level}.wav")
        self.alert_sound_samples, self.alert_sound_samplerate = self._load_sound_file(f"alert_{self.volume_level}.wav")
        
        self.menu_manager = TrayMenuManager(self)
        self.setContextMenu(self.menu_manager.menu)
        
        self.setIcon(self.app_icon or self.no_internet_icon)
        self.show()
        self.setToolTip(self.tr.get("initializing_tooltip"))
        
        self.activated.connect(self.on_activated)
        
        # Запускаем наши циклы с небольшой задержкой
        QtCore.QTimer.singleShot(100, self._handle_first_launch_tasks)
        QtCore.QTimer.singleShot(200, self.main_update_loop)

    def _handle_first_launch_tasks(self):
        """
        Выполняет действия, необходимые только при первом запуске.
        """
        # Проверяем флаг, который мы теперь будем использовать
        if self.config.shortcut_prompted:
            return

        dialog = CustomQuestionDialog(
            self.tr.get("shortcut_dialog_title"),
            self.tr.get("shortcut_dialog_text"),
            self.tr,
            self.app_icon
        )
        
        if dialog.exec():
            create_desktop_shortcut()
        
        # Устанавливаем флаг, чтобы больше не спрашивать.
        self.config.settings.setValue("main/shortcut_prompted", True)
        self.config.shortcut_prompted = True

    def load_app_settings(self):
        cfg = self.config
        lang_code = get_initial_language_code(cfg.language)
        cfg.language = lang_code
        self.tr.load_language(lang_code)
        
        self.update_interval_ms = cfg.update_interval * 1000
        self.notifications_enabled = cfg.notifications
        self.sound_enabled = cfg.sound
        self.volume_level = cfg.volume_level
        self.idle_enabled = cfg.idle_enabled
        self.idle_threshold_seconds = cfg.idle_threshold_mins * 60
        self.idle_interval_ms = cfg.idle_interval_mins * 60 * 1000
        
        self.reset_to_active_mode()

    # --- ДОБАВЛЕНО: Диспетчер секундного таймера ---
    def on_second_tick(self):
        self.check_for_wakeup()
        self.update_tooltip_time()

    def check_for_wakeup(self):
        if not self.is_in_idle_mode: return
        if not idle_detector.is_user_idle(self.idle_threshold_seconds):
            self.exit_idle_mode()

    def main_update_loop(self):
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
            base_interval_seconds = self.config.update_interval
            jitter_amount_seconds = base_interval_seconds * 0.30
            min_interval = base_interval_seconds - jitter_amount_seconds
            max_interval = base_interval_seconds + jitter_amount_seconds
            random_interval_seconds = random.uniform(min_interval, max_interval)
            rounded_seconds = round(random_interval_seconds)
            interval_ms = rounded_seconds * 1000
            final_interval_ms = max(1000, interval_ms)
            self.timer.start(final_interval_ms)

    
    def reset_to_active_mode(self):
            """Просто устанавливает флаг активного режима."""
            self.is_in_idle_mode = False

# File: src/app.py

    # --- ЗАМЕНИТЕ ВАШУ СТАРУЮ update_location_icon НА ЭТУ ---
    def update_location_icon(self, is_forced_by_user=False):
        #### print("DEBUG: 1. update_location_icon called. Starting background task...")
        """Запускает фоновую задачу по обновлению IP."""
        
        # --- НАЧАЛО ИСПРАВЛЕНИЙ ---
        if is_forced_by_user:
            # Если это ручной запуск, останавливаем текущий таймер, чтобы избежать гонки
            if self.timer.isActive():
                self.timer.stop()
        
        # В любом случае (и ручном, и автоматическом) запускаем проверку в фоне
        threading.Thread(target=self._update_location_task, args=(is_forced_by_user,), daemon=True).start()
        
        # В любом случае планируем СЛЕДУЮЩЕЕ обновление
        self.schedule_next_update()
        # --- КОНЕЦ ИСПРАВЛЕНИЙ ---

    # --- ДОБАВЬТЕ ЭТИ ДВА НОВЫХ МЕТОДА В КЛАСС App ---
    def _update_location_task(self, is_forced):
        #### print("DEBUG: 2. _update_location_task started in background thread.")
        """
        Эта функция выполняется в фоновом потоке.
        Она делает "тяжелый" вызов и отправляет результат в главный поток через сигнал.
        """
        # Переименовываем, как и договаривались
        ip_data = get_ip_data_from_rust() 
        self.ipDataReceived.emit(ip_data, is_forced)

    @QtCore.Slot(object, bool) # <-- Принимаем ДВА аргумента
    def on_ip_data_received(self, ip_data, is_forced):
        #### print(f"DEBUG: 4. Main thread received data: {ip_data}")
        """
        Этот слот выполняется в ГЛАВНОМ потоке и безопасно обновляет GUI.
        Здесь находится вся старая логика обработки результата.
        """
        if not ip_data or ip_data.get('ip') == "N/A":
            self.setIcon(self.no_internet_icon)
            self.setToolTip(self.tr.get("error_tooltip", error=self.tr.get("no_external_ip_detected")))
            self.base_tooltip_text = ""
            if self.last_known_external_ip != "N/A":
                self.play_alert_sound_threaded()
            self.last_known_external_ip = "N/A"
        else:
            self.last_update_time = time.time()
            current_ip = ip_data.get('ip')
            full_data = ip_data.get('full_data', {})
            
            # Здесь is_forced_by_user не нужен, т.к. мы обновляем GUI
            # каждый раз, когда получаем новые данные.
            if current_ip != self.last_known_external_ip or is_forced:
                if full_data:
                    self.current_location_data = full_data
                else:
                    self.current_location_data = {'ip': current_ip, 'country_code': '??', 'city': 'N/A', 'isp': 'N/A'}
                
                if self.last_known_external_ip != current_ip:
                    if self.location_history and self.location_history[-1]['ip'] != self.current_location_data['ip']:
                        self.location_history.append(self.current_location_data)
                    elif not self.location_history:
                        self.location_history.append(self.current_location_data)
                
                self.last_known_external_ip = current_ip
                self.update_gui_with_new_data()
            else:
                self.update_tooltip_time()

    def update_gui_with_new_data(self):
        #### print("DEBUG: 5. update_gui_with_new_data called. Updating UI.")
        data = self.current_location_data
        country_code = data.get('country_code', '')
        icon = self._load_icon(f"{country_code}.png", "flags")
        self.setIcon(icon or self.app_icon)
        
        # Получаем текущее время в формате ЧЧ:ММ:СС
        update_time_str = time.strftime("%H:%M:%S")
        
        # Формируем полный тултип со статичным временем
        tooltip_text = (f"{data.get('ip', 'N/A')}\n"
                        f"{country_code.upper()}\n"
                        f"{truncate_text(data.get('city', 'N/A'), 17)}\n"
                        f"{truncate_text(clean_isp_name(data.get('isp', 'N/A')), 17)}\n"
                        f"({self.tr.get('tooltip_updated_at', time=update_time_str)})")
        
        self.setToolTip(tooltip_text)
        
        self.menu_manager.update_menu_content()
        
        if self.notifications_enabled:
            self.showMessage(self.tr.get("location_updated_title"), 
                             self.tr.get("location_updated_message", ip=data.get('ip'), city=data.get('city'), country_code=country_code.upper()), 
                             self.icon(), 5000)
        self.play_notification_sound_threaded()

    # --- ДОБАВЛЕНО: Функция для обновления тултипа ---
    def update_tooltip_time(self):
        if self.is_in_idle_mode:
            self.setToolTip(self.tr.get("idle_mode_tooltip"))
            return
        if not self.current_location_data or not self.base_tooltip_text: return
        if self.last_update_time > 0:
            seconds_ago = int(time.time() - self.last_update_time)
            time_str = self.tr.get("tooltip_updated_ago", seconds=seconds_ago)
            full_tooltip = f"{self.base_tooltip_text}\n({time_str})"
        else:
            full_tooltip = self.base_tooltip_text
        self.setToolTip(full_tooltip)

    def open_settings_dialog(self):
        # Если окно уже существует, выводим его на передний план и выходим
        if self.settings_dialog:
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return

        # Если окна нет, создаем его и сохраняем ссылку
        self.settings_dialog = SettingsDialog(self.app_icon, self.tr, self.tr.available_languages, self.config, None)
        
        # Привязываем наши действия к сигналам
        self.settings_dialog.accepted.connect(self.on_settings_accepted)
        self.settings_dialog.rejected.connect(self.on_settings_rejected)
        
        # Показываем окно (неблокирующий вызов)
        self.settings_dialog.show()

    def on_settings_accepted(self):
        """Вызывается при нажатии OK в настройках."""
        if not self.settings_dialog: return

        old_lang = self.config.language
        
        new_settings = self.settings_dialog.get_settings()
        self.config.save_settings(new_settings)
        set_autostart_shortcut(new_settings['autostart'])
        self.load_app_settings()
        
        # Перезагружаем звуки с новым уровнем громкости
        self.sound_samples, self.sound_samplerate = self._load_sound_file(f"notification_{self.volume_level}.wav")
        self.alert_sound_samples, self.alert_sound_samplerate = self._load_sound_file(f"alert_{self.volume_level}.wav")

        if old_lang != self.config.language:
            self.reload_ui_texts()
            
        self.settings_dialog.close() # Закрываем окно
        self.settings_dialog = None  # Сбрасываем ссылку

    def on_settings_rejected(self):
        """Вызывается при нажатии Cancel или крестика."""
        if not self.settings_dialog: return
        self.settings_dialog.close() # Закрываем окно
        self.settings_dialog = None # Просто сбрасываем ссылку

    def reload_ui_texts(self):
        self.tr = Translator(resource_path("assets/i18n"))
        lang_code = get_initial_language_code(self.config.language)
        self.tr.load_language(lang_code)
        self.menu_manager = TrayMenuManager(self)
        self.setContextMenu(self.menu_manager.menu)
        if self.current_location_data: self.menu_manager.update_menu_content()
        self.update_tooltip_time()

    def open_about_dialog(self):
        if self.about_dialog and self.about_dialog.isVisible():
            self.about_dialog.raise_(); self.about_dialog.activateWindow(); return
        # --- ИЗМЕНЕНИЕ: Передаем готовый pixmap ---
        self.about_dialog = AboutDialog(self.app_icon, self.tr, __version__, RELEASE_DATE, self.about_logo_pixmap, None)
        self.about_dialog.exec()

    def on_activated(self, reason):
            """Вызывается при клике на иконку."""
            # ЛКМ (Trigger) теперь всегда вызывает принудительное обновление.
            # А `update_location_icon` сама разберется, нужно ли выходить из простоя.
            if reason == self.ActivationReason.Trigger:
                self.update_location_icon(is_forced_by_user=True)

    def _load_icon(self, filename, subfolder="icons", size=20):
        try:
            path = resource_path(os.path.join("assets", subfolder, filename))
            if not os.path.isfile(path): return None
            pixmap = QtGui.QPixmap(path)
            return QtGui.QIcon(pixmap.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"Error loading icon {filename}: {e}"); return None

    # --- ДОБАВЛЕНО: Функция для загрузки QPixmap ---
    def _load_pixmap(self, filename, size):
        try:
            path = resource_path(os.path.join("assets", "icons", filename))
            if not os.path.isfile(path): return None
            pixmap = QtGui.QPixmap(path)
            return pixmap.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        except Exception as e:
            print(f"Error loading pixmap {filename}: {e}"); return None

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
        threading.Thread(target=self._play_sound_task, args=(samples, samplerate), daemon=True).start()

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
# В классе App
    def open_dns_leak_test_website(self):
        webbrowser.open('https://ipleak.net/')
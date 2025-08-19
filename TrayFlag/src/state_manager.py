# File: src/state_manager.py

from collections import deque

class AppState:
    """Хранит и управляет всем состоянием приложения."""
    def __init__(self):
        self.current_location_data = {}
        self.location_history = deque(maxlen=3)
        self.last_known_external_ip = ""
        self.is_in_idle_mode = False
        self.last_update_time = 0
        self.base_tooltip_text = ""

    def update_location(self, new_data):
        """Обновляет данные о местоположении и историю."""
        current_ip = new_data.get('ip')
        if not current_ip:
            return

        # Обновляем историю, только если IP действительно изменился
        if self.last_known_external_ip != current_ip:
            if self.current_location_data: # Добавляем предыдущее состояние в историю
                self.location_history.append(self.current_location_data)
            self.last_known_external_ip = current_ip
        
        self.current_location_data = new_data

    def set_idle_mode(self, status: bool):
        """Устанавливает флаг экономного режима."""
        self.is_in_idle_mode = status

    def clear_network_state(self):
        """Сбрасывает сетевое состояние при потере соединения."""
        self.last_known_external_ip = "N/A"
        self.base_tooltip_text = ""
        # self.current_location_data можно не сбрасывать, чтобы сохранить последние данные
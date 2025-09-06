# File: src/state_manager.py

from collections import deque

class AppState:
    """Store and manage application state."""
    def __init__(self):
        self.current_location_data = {}
        self.location_history = deque(maxlen=3)
        self.last_known_external_ip = ""
        self.is_in_idle_mode = False
        self.last_update_time = 0
        self.base_tooltip_text = ""

    def update_location(self, new_data):
        """Update location data and history."""
        current_ip = new_data.get('ip')
        if not current_ip:
            return

        # Update history only if IP actually changed
        if self.last_known_external_ip != current_ip:
            if self.current_location_data: # Добавляем предыдущее состояние в историю
                self.location_history.append(self.current_location_data)
            self.last_known_external_ip = current_ip
        
        self.current_location_data = new_data

    def set_idle_mode(self, status: bool):
        """Set idle mode flag."""
        self.is_in_idle_mode = status

    def clear_network_state(self):
        """Reset network state after connection loss."""
        self.last_known_external_ip = "N/A"
        self.base_tooltip_text = ""
        # self.current_location_data # You can keep the current location data without resetting

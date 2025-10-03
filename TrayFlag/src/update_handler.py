# File: src/update_handler.py

import random
import threading
from PySide6 import QtCore

from ip_fetcher import get_ip_data_from_rust
import idle_detector

class UpdateHandler(QtCore.QObject):
    # Signal that will send data to the main thread
    ipDataReceived = QtCore.Signal(object, bool) # (ip_data, is_forced)
    enteredIdleMode = QtCore.Signal()

    def __init__(self, config, state):
        super().__init__()
        self.config = config
        self.state = state
        
        # Main timer for checking IP
        self.main_timer = QtCore.QTimer()
        self.main_timer.timeout.connect(self.main_update_loop)
        
        # "Pulse timer" for checking idleness
        self.idle_check_timer = QtCore.QTimer()
        self.idle_check_timer.setInterval(1000)
        self.idle_check_timer.timeout.connect(self.check_for_wakeup)

    def start(self):
        """Runs the main update loop and "pulse" timer."""
        self.idle_check_timer.start()
        # Run the main update loop after 200ms
        QtCore.QTimer.singleShot(200, self.main_update_loop)

    def check_for_wakeup(self):
        """Checks if the user has woken up from idle mode."""
        if not self.state.is_in_idle_mode:
            return

        threshold_mins = self.config.idle_threshold_mins

        # "Easter egg" for debugging: if 0 is selected, use 5 seconds
        if threshold_mins == 0:
            threshold_seconds = 5
        else:
            threshold_seconds = threshold_mins * 60

        if not idle_detector.is_user_idle(threshold_seconds):
            self.exit_idle_mode()

    def main_update_loop(self):
        """Main update loop, called every time the main timer fires."""
        if self.config.idle_enabled and not self.state.is_in_idle_mode:

            threshold_mins = self.config.idle_threshold_mins
            
            # "Easter egg" for debugging: if 0 is selected, use 5 seconds
            if threshold_mins == 0:
                threshold_seconds = 5
            else:
                threshold_seconds = threshold_mins * 60

            if idle_detector.is_user_idle(threshold_seconds):
                self.enter_idle_mode()
                return
        self.update_location_icon()

    def enter_idle_mode(self):
        if self.state.is_in_idle_mode: return
        self.state.set_idle_mode(True)
        print("Entering idle mode...")
        self.enteredIdleMode.emit()
        self.main_timer.start(self.config.idle_interval_mins * 60 * 1000)

    def exit_idle_mode(self):
        if not self.state.is_in_idle_mode: return
        self.state.set_idle_mode(False)
        print("Exiting idle mode...")
        self.update_location_icon(is_forced_by_user=True)

    def schedule_next_update(self):
        if self.state.is_in_idle_mode:
            self.main_timer.start(self.config.idle_interval_mins * 60 * 1000)
        else:
            base_seconds = self.config.update_interval
            jitter = base_seconds * 0.30
            rand_seconds = random.uniform(base_seconds - jitter, base_seconds + jitter)
            interval_ms = round(rand_seconds) * 1000
            self.main_timer.start(max(1000, interval_ms))

    def reset_to_active_mode(self):
        self.state.set_idle_mode(False)
        self.schedule_next_update()

    def update_location_icon(self, is_forced_by_user=False):
        if is_forced_by_user:
            if self.main_timer.isActive(): self.main_timer.stop()
            self.reset_to_active_mode()
        
        threading.Thread(target=self._update_location_task, args=(is_forced_by_user,), daemon=True).start()
        
        if not is_forced_by_user:
            self.schedule_next_update()

    def _update_location_task(self, is_forced):
        ip_data = get_ip_data_from_rust()
        self.ipDataReceived.emit(ip_data, is_forced)

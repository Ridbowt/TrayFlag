# File: src/config.py

import os
from PySide6.QtCore import QSettings
from utils import resource_path
from constants import APP_NAME, __version__

SETTINGS_FILE_PATH = resource_path(f"{APP_NAME}.ini")

class ConfigManager:
    def __init__(self):
        self.settings = QSettings(SETTINGS_FILE_PATH, QSettings.Format.IniFormat)
        
        # Check if the file exists. If not, create it and populate it.
        if not os.path.exists(SETTINGS_FILE_PATH) or not self.settings.childGroups():
            print(f"INI file not found or empty. Creating a new one with default settings at: {SETTINGS_FILE_PATH}")
            self._create_default_ini()

        self.load_settings()

    def _create_default_ini(self):
        """Creates a .ini file and fills it with default values."""
        
        # Section with Version
        self.settings.setValue(f"{APP_NAME}/version", __version__)
        
        # Section [main]
        self.settings.setValue("main/language", "") # Empty, to let the system language be detected
        self.settings.setValue("main/autostart", False)
        self.settings.setValue("main/notifications", True)
        self.settings.setValue("main/sound", True)

        self.settings.setValue("main/volume_level", "medium")
        self.settings.setValue("main/shortcut_prompted", False)
        
        # Section [intervals]
        self.settings.setValue("intervals/active", 7)
        
        # Section [idle]
        self.settings.setValue("idle/enabled", True)
        self.settings.setValue("idle/threshold_mins", 15)
        self.settings.setValue("idle/interval_mins", 60)
        
        # Make sure everything is written to disk
        self.settings.sync()

    def load_settings(self):
        """Loads all settings from the .ini file into class attributes."""
        # Now we can be sure that the keys exist,
        # but we still keep default values in case the user manually deletes a line.
        self.language = self.settings.value("main/language", "", type=str)
        self.volume_level = self.settings.value("main/volume_level", "medium", type=str) # low, medium, high
        self.shortcut_prompted = self.settings.value("main/shortcut_prompted", False, type=bool)
        self.autostart = self.settings.value("main/autostart", False, type=bool)
        self.notifications = self.settings.value("main/notifications", True, type=bool)
        self.sound = self.settings.value("main/sound", True, type=bool)
        
        self.update_interval = self.settings.value("intervals/active", 7, type=int)
        
        self.idle_enabled = self.settings.value("idle/enabled", True, type=bool)
        self.idle_threshold_mins = self.settings.value("idle/threshold_mins", 15, type=int)
        self.idle_interval_mins = self.settings.value("idle/interval_mins", 60, type=int)
        
        self._check_and_update_version()

    def save_settings(self, values):
        """Saves the settings dictionary to a .ini file."""
        self.settings.setValue("main/language", values['language'])
        self.settings.setValue("main/autostart", values['autostart'])
        self.settings.setValue("main/notifications", values['notifications'])
        self.settings.setValue("main/sound", values['sound'])
        self.settings.setValue("main/volume_level", values['volume_level'])
        
        self.settings.setValue("intervals/active", values['update_interval'])
        
        self.settings.setValue("idle/enabled", values['idle_enabled'])
        self.settings.setValue("idle/threshold_mins", values['idle_threshold_mins'])
        self.settings.setValue("idle/interval_mins", values['idle_interval_mins'])
        
        self.load_settings()

    def _check_and_update_version(self):
        """Checks the version in the .ini and updates it if necessary."""
        ini_version = self.settings.value(f"{APP_NAME}/version", "0.0.0", type=str)
        if ini_version != __version__:
            print(f"INFO: INI version mismatch. Updating from {ini_version} to {__version__}.")
            self.settings.setValue(f"{APP_NAME}/version", __version__)

# File: src/sound_manager.py

import os
import threading
from utils import resource_path

try:
    import soundfile as sf
    import sounddevice as sd
    SOUND_LIBS_AVAILABLE = True
except ImportError:
    SOUND_LIBS_AVAILABLE = False

class SoundManager:
    def __init__(self, config):
        """
        Initializes the sound manager.
        :param config: Example of ConfigManager for access to settings.
        """
        self.config = config
        self.sound_samples = None
        self.sound_samplerate = None
        self.alert_sound_samples = None
        self.alert_sound_samplerate = None
        
        if SOUND_LIBS_AVAILABLE:
            self._load_sounds()

    def reload_sounds(self):
        """Public method for reloading with a log."""
        print(f"Sounds reloaded for volume level: {self.config.volume_level}")
        self._load_sounds()

    def _load_sounds(self):
        """Internal method that simply loads files."""
        volume_level = self.config.volume_level
        self.sound_samples, self.sound_samplerate = self._load_sound_file(f"notification_{volume_level}.wav")
        self.alert_sound_samples, self.alert_sound_samplerate = self._load_sound_file(f"alert_{volume_level}.wav")

    def _load_sound_file(self, filename):
        """Loads a sound file from the assets folder."""
        try:
            path = resource_path(os.path.join("assets", "sounds", filename))
            return sf.read(path, dtype='float32')
        except Exception as e:
            print(f"Error loading sound {filename}: {e}")
            return None, None

    def play_notification(self):
        """Plays a notification sound in a separate thread."""
        if self.config.sound:
            self._start_sound_thread(self.sound_samples, self.sound_samplerate)

    def play_alert(self):
        """Plays an alert sound in a separate thread."""
        if self.config.sound:
            self._start_sound_thread(self.alert_sound_samples, self.alert_sound_samplerate)

    def _start_sound_thread(self, samples, samplerate):
        if not SOUND_LIBS_AVAILABLE or samples is None:
            return
        threading.Thread(target=self._play_sound_task, args=(samples, samplerate), daemon=True).start()

    def _play_sound_task(self, samples, samplerate):
        try:
            sd.play(samples, samplerate)
            sd.wait()
        except Exception as e:
            print(f"Error in sound playback thread: {e}")

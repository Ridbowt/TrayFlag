# File: src/translator.py

import os
import json
import locale
from utils import resource_path

class Translator:
    def __init__(self, i18n_dir_path, default_lang="en"):
        self.i18n_dir = i18n_dir_path
        self.default_lang = default_lang
        self.current_lang = default_lang
        self.translations = {}
        self.available_languages = self._find_languages()

    def _find_languages(self):
        langs = {}
        if not os.path.isdir(self.i18n_dir):
            print(f"Warning: i18n directory not found at {self.i18n_dir}")
            return langs
        for filename in os.listdir(self.i18n_dir):
            if filename.endswith(".json"):
                lang_code = filename[:-5]
                langs[lang_code] = lang_code.upper()
        return langs

    def load_language(self, lang_code, is_reload=False):
        """
        Public method for loading/reloading the language.
        Prints a message only if this is a reload.
        """
        if is_reload:
            print(f"Language changed to '{lang_code}'. Reloading translations...")
        
        return self._load_language_internal(lang_code)

    def _load_language_internal(self, lang_code):
        self.current_lang = lang_code
        if lang_code not in self.available_languages:
            self.current_lang = self.default_lang
        
        filepath = os.path.join(self.i18n_dir, f"{self.current_lang}.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except Exception as e:
            print(f"Failed to load language '{self.current_lang}': {e}. Loading default.")
            if self.current_lang != self.default_lang:
                self._load_language_internal(self.default_lang)

        return self.current_lang

    def get(self, key, **kwargs):
        text = self.translations.get(key, f"<{key}>")
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text

def get_initial_language_code(config_lang):
    if config_lang:
        return config_lang
    try:
        system_lang, _ = locale.getdefaultlocale()
        return system_lang[:2] if system_lang else "en"
    except Exception:
        return "en"

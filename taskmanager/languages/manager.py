from typing import Dict, Optional
import importlib
import os

class LanguageManager:
    _instance = None
    _translations: Dict[str, Dict[str, str]] = {}
    _available_languages = {
        'en': 'English',
        'fa': 'فارسی',
        'ar': 'العربية'
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LanguageManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._translations:
            self._load_translations()
    
    def _load_translations(self):
        """Load all translation files from the languages directory."""
        languages_dir = os.path.dirname(os.path.abspath(__file__))
        for lang_code in self._available_languages.keys():
            try:
                module = importlib.import_module(f'.{lang_code}', package='taskmanager.languages')
                self._translations[lang_code] = module.translations
            except ImportError as e:
                print(f"Error loading translations for {lang_code}: {e}")
    
    def get_text(self, key: str, lang_code: str, **kwargs) -> str:
        """Get translated text for the given key and language."""
        print(f"Debug: Getting text for key '{key}' in language '{lang_code}'")  # Debug log
        if lang_code not in self._translations:
            print(f"Debug: Language '{lang_code}' not found, falling back to English")  # Debug log
            lang_code = 'en'  # Fallback to English
        
        translations = self._translations[lang_code]
        text = translations.get(key)
        
        # If translation not found in current language, try English
        if text is None and lang_code != 'en':
            print(f"Debug: Translation for key '{key}' not found in '{lang_code}', trying English")  # Debug log
            text = self._translations['en'].get(key)
        
        # If still not found, return the key itself
        if text is None:
            print(f"Warning: Translation missing for key '{key}' in language '{lang_code}'")
            return key
        
        # Apply any formatting kwargs
        try:
            return text.format(**kwargs)
        except KeyError as e:
            print(f"Warning: Missing format parameter '{e}' for key '{key}' in language '{lang_code}'")
            return text
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get dictionary of available language codes and their names."""
        return self._available_languages.copy()
    
    def is_valid_language(self, lang_code: str) -> bool:
        """Check if the given language code is valid."""
        return lang_code in self._available_languages

# Create a global instance
language_manager = LanguageManager() 
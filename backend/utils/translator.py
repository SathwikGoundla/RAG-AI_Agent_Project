"""
Translator Module
Handles translation between languages
"""

from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class Translator:
    """Translate between languages"""
    
    SUPPORTED_LANGUAGES = {
        "english": "en",
        "telugu": "te",
        "hindi": "hi"
    }
    
    @staticmethod
    def translate(text: str, source_language: str = "auto", target_language: str = "en") -> str:
        """
        Translate text
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Translated text
        """
        try:
            from google_trans_new import google_translator
            
            translator = google_translator()
            
            # Translate
            translated = translator.translate(text, lang_src=source_language, lang_tgt=target_language)
            
            logger.info(f"Translated from {source_language} to {target_language}")
            return translated
        
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return text
    
    @staticmethod
    def translate_to_english(text: str, source_language: str = "auto") -> str:
        """Translate to English"""
        return Translator.translate(text, source_language, "en")
    
    @staticmethod
    def translate_to_telugu(text: str, source_language: str = "auto") -> str:
        """Translate to Telugu"""
        return Translator.translate(text, source_language, "te")
    
    @staticmethod
    def translate_batch(texts: list, source_language: str = "auto", target_language: str = "en") -> list:
        """Translate multiple texts"""
        try:
            from google_trans_new import google_translator
            
            translator = google_translator()
            translated_texts = []
            
            for text in texts:
                translated = translator.translate(text, lang_src=source_language, lang_tgt=target_language)
                translated_texts.append(translated)
            
            logger.info(f"Translated {len(texts)} texts")
            return translated_texts
        
        except Exception as e:
            logger.error(f"Batch translation error: {str(e)}")
            return texts

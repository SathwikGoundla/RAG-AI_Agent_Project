"""
Language Detection Module
Detects language and provides multi-language support
"""

from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detect language and provide translation support"""
    
    SUPPORTED_LANGUAGES = {
        "english": "en",
        "telugu": "te",
    }
    
    @staticmethod
    def detect(text: str) -> str:
        """
        Detect language of text
        
        Args:
            text: Input text
            
        Returns:
            Language code ('english', 'telugu', etc.)
        """
        try:
            from langdetect import detect, DetectorFactory
            DetectorFactory.seed = 0
            
            lang_code = detect(text)
            
            # Map to our language names
            language_map = {
                "en": "english",
                "te": "telugu",
                "hi": "hindi"
            }
            
            return language_map.get(lang_code, "english")
        
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}, defaulting to English")
            return "english"
    
    @staticmethod
    def detect_batch(texts: list) -> dict:
        """
        Detect language for multiple texts
        
        Args:
            texts: List of texts
            
        Returns:
            Dictionary with language counts
        """
        languages = {}
        
        for text in texts:
            lang = LanguageDetector.detect(text)
            languages[lang] = languages.get(lang, 0) + 1
        
        return languages
    
    @staticmethod
    def is_telugu(text: str) -> bool:
        """Check if text is Telugu"""
        detected = LanguageDetector.detect(text)
        return detected == "telugu"
    
    @staticmethod
    def is_english(text: str) -> bool:
        """Check if text is English"""
        detected = LanguageDetector.detect(text)
        return detected == "english"

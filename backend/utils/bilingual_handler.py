"""
Bilingual Handler Module
Manages Telugu and English interactions with context preservation
"""

import logging
from typing import Dict, Optional, Tuple, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Supported languages"""
    ENGLISH = "english"
    TELUGU = "telugu"


@dataclass
class BilingualContext:
    """Context for bilingual conversation"""
    current_language: Language = Language.ENGLISH
    detected_language: Language = Language.ENGLISH
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    original_queries: List[str] = field(default_factory=list)  # Original language
    translated_queries: List[str] = field(default_factory=list)  # Translated to English
    original_answers: List[str] = field(default_factory=list)  # In original language
    timestamps: List[datetime] = field(default_factory=list)
    user_language_preference: Optional[Language] = None
    
    def add_interaction(self, query: str, answer: str, language: Language):
        """Add interaction to history"""
        self.conversation_history.append({
            "query": query,
            "answer": answer,
            "language": language.value,
            "timestamp": datetime.now().isoformat()
        })
        self.original_queries.append(query)
        self.original_answers.append(answer)
        self.timestamps.append(datetime.now())
        self.current_language = language
    
    def get_recent_context(self, num_messages: int = 5) -> str:
        """Get recent conversation context"""
        recent = self.conversation_history[-num_messages:]
        context = "\n".join([
            f"Q: {msg['query']}\nA: {msg['answer']}"
            for msg in recent
        ])
        return context
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        self.original_queries.clear()
        self.translated_queries.clear()
        self.original_answers.clear()
        self.timestamps.clear()


class BilingualHandler:
    """Handle bilingual interactions"""
    
    @staticmethod
    def detect_language(text: str) -> Language:
        """
        Detect language of text
        
        Args:
            text: Input text
            
        Returns:
            Language enum (ENGLISH or TELUGU)
        """
        try:
            from langdetect import detect, DetectorFactory
            DetectorFactory.seed = 0
            
            lang_code = detect(text)
            
            if lang_code == "te":
                return Language.TELUGU
            else:
                return Language.ENGLISH
        
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}, defaulting to English")
            return Language.ENGLISH
    
    @staticmethod
    def translate(
        text: str,
        source_language: Language = Language.ENGLISH,
        target_language: Language = Language.TELUGU
    ) -> str:
        """
        Translate text between languages
        
        Args:
            text: Text to translate
            source_language: Source language
            target_language: Target language
            
        Returns:
            Translated text
        """
        if source_language == target_language:
            return text
        
        try:
            from google_trans_new import google_translator
            
            translator = google_translator()
            
            # Map language to language codes
            lang_map = {
                Language.ENGLISH: "en",
                Language.TELUGU: "te",
            }
            
            source_code = lang_map.get(source_language, "en")
            target_code = lang_map.get(target_language, "te")
            
            translated = translator.translate(
                text,
                lang_src=source_code,
                lang_tgt=target_code
            )
            
            logger.info(f"Translated from {source_language.value} to {target_language.value}")
            return translated
        
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return text
    
    @staticmethod
    def prepare_multilingual_context(
        detected_language: Language,
        user_language_preference: Optional[Language],
        recent_context: str
    ) -> str:
        """
        Prepare context that works across languages
        
        Args:
            detected_language: Detected language of current query
            user_language_preference: User's preferred language
            recent_context: Recent conversation context
            
        Returns:
            Prepared context string
        """
        context_lines = []
        
        # Language info
        if detected_language == Language.TELUGU:
            context_lines.append("[Query Language: Telugu]")
        else:
            context_lines.append("[Query Language: English]")
        
        if user_language_preference:
            response_lang = "Telugu" if user_language_preference == Language.TELUGU else "English"
            context_lines.append(f"[Response Language: {response_lang}]")
        
        # Add recent context
        if recent_context:
            context_lines.append("[Recent Context]")
            context_lines.append(recent_context)
        
        return "\n".join(context_lines)
    
    @staticmethod
    def should_translate_answer(
        query_language: Language,
        response_language: Optional[Language]
    ) -> bool:
        """
        Determine if answer should be translated
        
        Args:
            query_language: Language of the query
            response_language: Preferred response language
            
        Returns:
            True if translation needed
        """
        if response_language is None:
            return False
        return query_language != response_language
    
    @staticmethod
    def get_language_specific_prompt(language: Language) -> str:
        """
        Get language-specific system prompt
        
        Args:
            language: Target language
            
        Returns:
            Language-specific prompt instruction
        """
        if language == Language.TELUGU:
            return (
                "You are a helpful assistant that answers questions in Telugu. "
                "Provide clear, accurate, and informative answers in Telugu. "
                "When citing sources, maintain the citation format but provide explanations in Telugu."
            )
        else:
            return (
                "You are a helpful assistant that answers questions in English. "
                "Provide clear, accurate, and informative answers in English. "
                "When citing sources, maintain proper citation format."
            )
    
    @staticmethod
    def format_answer_for_language(
        answer: str,
        language: Language,
        sources: Optional[List[Dict]] = None
    ) -> str:
        """
        Format answer appropriately for language
        
        Args:
            answer: The answer text
            language: Target language
            sources: Optional sources to cite
            
        Returns:
            Formatted answer
        """
        if language == Language.TELUGU:
            # Ensure Telugu-specific formatting
            formatted = f"సమాధానం (Answer in Telugu):\n{answer}"
        else:
            # English formatting
            formatted = f"Answer:\n{answer}"
        
        if sources:
            if language == Language.TELUGU:
                formatted += "\n\nసూచనలు (Sources):\n"
            else:
                formatted += "\n\nSources:\n"
        
        return formatted
    
    @staticmethod
    def get_bilingual_summary(
        english_text: str,
        telugu_text: str
    ) -> Dict[str, str]:
        """
        Create bilingual summary
        
        Args:
            english_text: English version
            telugu_text: Telugu version
            
        Returns:
            Dictionary with both versions
        """
        return {
            "english": english_text,
            "telugu": telugu_text,
            "language_pair": "en-te"
        }
    
    @staticmethod
    def process_bilingual_query(
        query: str,
        user_language_preference: Optional[str] = None,
        context: Optional[BilingualContext] = None
    ) -> Tuple[str, Language, Language]:
        """
        Process query and determine languages for interaction
        
        Args:
            query: User query
            user_language_preference: User's preferred language for response
            context: Bilingual context for conversation
            
        Returns:
            Tuple of (processed_query, query_language, response_language)
        """
        # Detect query language
        query_language = BilingualHandler.detect_language(query)
        
        # Determine response language
        if user_language_preference:
            if user_language_preference.lower() == "telugu" or user_language_preference.lower() == "te":
                response_language = Language.TELUGU
            else:
                response_language = Language.ENGLISH
        else:
            response_language = query_language
        
        # Translate query to English if needed (for processing)
        if query_language == Language.TELUGU:
            processed_query = BilingualHandler.translate(
                query,
                Language.TELUGU,
                Language.ENGLISH
            )
        else:
            processed_query = query
        
        # Update context if provided
        if context:
            context.detected_language = query_language
            context.current_language = response_language
        
        return processed_query, query_language, response_language


class BilingualContextManager:
    """Manage bilingual contexts for users/sessions"""
    
    def __init__(self):
        self.contexts: Dict[str, BilingualContext] = {}
    
    def get_or_create_context(self, session_id: str) -> BilingualContext:
        """Get or create context for session"""
        if session_id not in self.contexts:
            self.contexts[session_id] = BilingualContext()
        return self.contexts[session_id]
    
    def clear_context(self, session_id: str):
        """Clear context for session"""
        if session_id in self.contexts:
            del self.contexts[session_id]
    
    def get_all_contexts(self) -> Dict[str, BilingualContext]:
        """Get all contexts"""
        return self.contexts

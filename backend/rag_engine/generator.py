"""
Response Generator Module
Generates LLM responses using OpenAI with retrieved context
"""

from typing import List, Dict, Optional
import logging
import requests
import json
import os
from backend.config import settings

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generate responses using OpenAI API with context from retriever
    """
    
    def __init__(self, model: str = "phi3", temperature: float = 0.3,
                max_tokens: int = 500):
        """
        Initialize response generator
        
        Args:
            model: Ollama model to use
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize Ollama client
        self.base_url = settings.OLLAMA_BASE_URL
        self.client = None
        
        logger.info(f"ResponseGenerator initialized with Ollama model: {model} at {self.base_url}")
    
    def generate_response(self, query: str, context_documents: List[Dict],
                         language: str = "english", system_prompt: Optional[str] = None) -> Dict:
        """
        Generate response using OpenAI with context
        
        Args:
            query: User query
            context_documents: Retrieved documents to use as context
            language: Response language ("english" or "telugu")
            system_prompt: Optional custom system prompt for language-specific guidance
            
        Returns:
            Dictionary with generated response and metadata
        """
        try:
            # Build context string from documents
            context_text = self._build_context(context_documents)
            
            # Build system prompt - use provided one or generate based on language
            if system_prompt is None:
                system_prompt = self._build_system_prompt(language)
            
            # Build user prompt
            user_prompt = self._build_user_prompt(query, context_text, language)
            
            logger.info(f"Generating response for query: {query[:50]}... in {language}")
            
            # Call Ollama API
            answer = self._call_ollama([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            return {
                "status": "success",
                "answer": answer,
                "model": self.model,
                "language": language,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                "context_docs_used": len(context_documents)
            }
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "answer": "Unable to generate response. Please try again.",
                "language": language
            }
    
    def _build_context(self, documents: List[Dict]) -> str:
        """
        Build context string from retrieved documents
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No context available."
        
        context_parts = []
        for idx, doc in enumerate(documents, 1):
            source = doc.get("source_file", "Unknown")
            content = doc.get("content", "")
            score = doc.get("similarity_score", 0)
            
            context_parts.append(
                f"Source {idx} [{source}] (Relevance: {score:.2f}):\n{content}\n"
            )
        
        return "\n".join(context_parts)
    
    @staticmethod
    def _build_system_prompt(language: str = "english") -> str:
        """
        Build system prompt for LLM
        
        Args:
            language: Response language
            
        Returns:
            System prompt
        """
        if language == "telugu":
            return """మీరు సహాయక AI సహాయకుడు. మీకు ఇవ్వబడిన సందర్భం ఆధారంగా ప్రశ్నలకు సమాధానం ఇవ్వండి.
- సమాధానం సందర్భం నుండి చేయండి
- లేకపోతే, మీరు తెలుసుకోనని చెప్పండి
- సమాధానం స్పష్టమైనది మరియు సంక్షిప్తమైనది చేయండి
- సందర్భం ఆధారంగా అందించిన సోర్సులను సూచించండి
"""
        else:
            return """You are a helpful AI assistant. Answer questions based on the provided context.
- Only use information from the context provided
- If the answer is not in the context, say so clearly
- Be clear, concise, and well-structured
- Cite sources from the provided context when relevant
- Provide accurate and factual information
"""
    
    @staticmethod
    def _build_user_prompt(query: str, context: str, language: str = "english") -> str:
        """
        Build user prompt for LLM
        
        Args:
            query: User query
            context: Context documents
            language: Language
            
        Returns:
            User prompt
        """
        if language == "telugu":
            return f"""సందర్భం:
{context}

ప్రశ్న: {query}

సమాధానం (తెలుగులో):"""
        else:
            return f"""Context:
{context}

Question: {query}

Answer:"""
    
    def generate_response_stream(self, query: str, context_documents: List[Dict],
                                language: str = "english"):
        """
        Generate response with streaming (for real-time display)
        
        Args:
            query: User query
            context_documents: Retrieved documents
            language: Response language
            
        Yields:
            Response chunks as they arrive
        """
        try:
            context_text = self._build_context(context_documents)
            system_prompt = self._build_system_prompt(language)
            user_prompt = self._build_user_prompt(query, context_text, language)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            yield f"Error: {str(e)}"
    
    def _call_ollama(self, messages: List[Dict]) -> str:
        """
        Call Ollama API with message history
        
        Args:
            messages: List of messages with role and content
            
        Returns:
            Generated response text
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "temperature": self.temperature
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Ollama at {self.base_url}. Make sure Ollama is running.")
            raise
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise
    
    def generate_with_language_detection(self, query: str, context_documents: List[Dict]) -> Dict:
        """
        Generate response with automatic language detection
        
        Args:
            query: User query
            context_documents: Retrieved documents
            
        Returns:
            Generated response
        """
        from backend.utils.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        detected_language = detector.detect(query)
        
        logger.info(f"Detected language: {detected_language}")
        
        return self.generate_response(query, context_documents, language=detected_language)

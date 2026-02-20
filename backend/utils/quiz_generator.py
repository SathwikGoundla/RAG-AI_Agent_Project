"""
Quiz Generator Module
Generates quiz questions from document content with multiple question types
"""

from typing import List, Dict, Optional
import logging
import requests
import json
import os
from datetime import datetime
from backend.config import settings

logger = logging.getLogger(__name__)


class QuizGenerator:
    """Generate quizzes from document content with multiple question types"""
    
    def __init__(self):
        """Initialize quiz generator"""
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        logger.info(f"QuizGenerator initialized with Ollama model: {self.model}")
    
    def generate_questions(
        self,
        content: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        language: str = "english",
        question_types: Optional[List[str]] = None,
        topic: Optional[str] = None
    ) -> Dict:
        """
        Generate quiz questions from content
        
        Args:
            content: Document content to generate questions from
            num_questions: Number of questions to generate (1-50)
            difficulty: Question difficulty (easy, medium, hard)
            language: Language for questions (english, telugu)
            question_types: List of question types to mix (multiple_choice, short_answer, true_false)
            topic: Optional topic filter for questions
            
        Returns:
            Dictionary with generated questions and metadata
        """
        try:
            # Validate inputs
            num_questions = min(max(1, num_questions), 50)
            
            # Default question types if not specified
            if question_types is None:
                question_types = ["multiple_choice", "short_answer", "true_false"]
            
            prompt = self._build_prompt(
                content,
                num_questions,
                difficulty,
                language,
                question_types,
                topic
            )
            
            questions_text = self._call_ollama(prompt)
            questions = self._parse_questions(questions_text)
            
            # Add metadata to each question
            questions = self._add_metadata(questions, difficulty, topic, language)
            
            logger.info(f"Generated {len(questions)} quiz questions")
            
            return {
                "status": "success",
                "questions": questions,
                "count": len(questions),
                "difficulty": difficulty,
                "language": language,
                "topic": topic,
                "question_types": question_types,
                "generated_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "count": 0,
                "questions": []
            }
    
    @staticmethod
    def _build_prompt(
        content: str,
        num_questions: int,
        difficulty: str,
        language: str,
        question_types: List[str],
        topic: Optional[str]
    ) -> str:
        """Build prompt for question generation with multiple types"""
        
        # Distribute questions across types
        num_mcq = max(1, num_questions // 3)
        num_short = max(1, num_questions // 3)
        num_tf = num_questions - num_mcq - num_short
        
        type_spec = f"""
        - {num_mcq} Multiple Choice questions (4 options each)
        - {num_short} Short Answer questions
        - {num_tf} True/False questions
        """ if all(t in question_types for t in ["multiple_choice", "short_answer", "true_false"]) else ""
        
        topic_filter = f"\nFocus on topic: {topic}" if topic else ""
        
        if language == "telugu":
            return f"""కింది సందర్భం నుండి {num_questions} {difficulty} స్థాయి క్విజ్ ప్రశ్నలను సృష్టించండి.{type_spec}{topic_filter}

సందర్భం:
{content[:3000]}

దయచేసి ఈ జసన్ ఫార్మాట్‌లో JSON లో సమాధానాలను ఇవ్వండి:
{{
    "questions": [
        {{
            "question_number": 1,
            "question_type": "multiple_choice|short_answer|true_false",
            "question": "ప్రశ్న టెక్స్ట్",
            "options": ["ఎ", "బి", "సి", "డి"],
            "correct_answer": "ఎ",
            "explanation": "వివరణ"
        }}
    ]
}}

IMPORTANT: Return ONLY valid JSON, no additional text."""
        else:
            return f"""Generate {num_questions} {difficulty} level quiz questions from the following content.{type_spec}{topic_filter}

Content:
{content[:3000]}

Please provide answers in this exact JSON format:
{{
    "questions": [
        {{
            "question_number": 1,
            "question_type": "multiple_choice|short_answer|true_false",
            "question": "Question text",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "Explanation"
        }}
    ]
}}

IMPORTANT: Return ONLY valid JSON, no additional text."""
    
    @staticmethod
    def _parse_questions(response_text: str) -> List[Dict]:
        """Parse JSON response into questions"""
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                questions = data.get("questions", [])
                
                # Normalize question structure
                normalized = []
                for q in questions:
                    normalized_q = {
                        "question_number": q.get("question_number", len(normalized) + 1),
                        "question_type": q.get("question_type", "multiple_choice"),
                        "question": q.get("question", ""),
                        "options": q.get("options"),
                        "correct_answer": q.get("correct_answer"),
                        "expected_answer": q.get("expected_answer"),
                        "explanation": q.get("explanation", "")
                    }
                    normalized.append(normalized_q)
                
                return normalized
        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse questions JSON: {e}")
        
        return []
    
    @staticmethod
    def _add_metadata(
        questions: List[Dict],
        difficulty: str,
        topic: Optional[str],
        language: str
    ) -> List[Dict]:
        """Add metadata to questions"""
        for q in questions:
            q["difficulty"] = difficulty
            q["language"] = language
            if topic:
                q["topic"] = topic
            
            # Ensure question_type is valid
            if q.get("question_type") not in ["multiple_choice", "short_answer", "true_false"]:
                q["question_type"] = "multiple_choice"
        
        return questions
    
    @staticmethod
    def grade_short_answer(user_answer: str, expected_answer: str, keywords: Optional[List[str]] = None) -> Dict:
        """
        Grade short answer questions
        
        Args:
            user_answer: User's provided answer
            expected_answer: Expected correct answer
            keywords: Keywords that should appear in answer
            
        Returns:
            Dictionary with grading result
        """
        user_answer_lower = user_answer.lower().strip()
        expected_lower = expected_answer.lower().strip()
        
        # Exact match or contains expected answer
        if user_answer_lower == expected_lower or expected_lower in user_answer_lower:
            return {"is_correct": True, "confidence": 0.95}
        
        # Check keywords if provided
        if keywords:
            matching_keywords = sum(1 for kw in keywords if kw.lower() in user_answer_lower)
            if len(keywords) > 0 and matching_keywords >= len(keywords) * 0.7:  # 70% keyword match
                return {"is_correct": True, "confidence": 0.75}
        
        # Partial credit based on similarity
        similarity = QuizGenerator._calculate_similarity(user_answer_lower, expected_lower)
        if similarity > 0.7:
            return {"is_correct": True, "confidence": similarity}
        elif similarity > 0.4:
            return {"is_correct": False, "confidence": 0.5}  # Partial credit
        else:
            return {"is_correct": False, "confidence": 0.1}
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API"""
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise
    
    @staticmethod
    def _calculate_similarity(str1: str, str2: str) -> float:
        """Calculate similarity between two strings (Jaccard similarity)"""
        set1 = set(str1.split())
        set2 = set(str2.split())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0

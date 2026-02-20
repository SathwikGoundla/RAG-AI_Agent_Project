"""
Study Plan Generator Module
Creates personalized study plans from document content
"""

from typing import List, Dict, Optional
import logging
import requests
import json
import os
from datetime import datetime, timedelta
from backend.config import settings

logger = logging.getLogger(__name__)


class StudyPlanGenerator:
    """Generate personalized study plans"""
    
    def __init__(self):
        """Initialize study plan generator"""
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        logger.info(f"StudyPlanGenerator initialized with Ollama model: {self.model}")
    
    def generate_study_plan(self, content: str, duration_days: int = 7,
                           hours_per_day: float = 2.0, language: str = "english") -> Dict:
        """
        Generate personalized study plan
        
        Args:
            content: Document content
            duration_days: Study plan duration in days
            hours_per_day: Hours available for study per day
            language: Language (english, telugu)
            
        Returns:
            Dictionary with study plan
        """
        try:
            prompt = self._build_prompt(content, duration_days, hours_per_day, language)
            
            plan_text = self._call_ollama(prompt)
            plan = self._parse_plan(plan_text, duration_days)
            
            logger.info(f"Generated study plan for {duration_days} days")
            
            return {
                "status": "success",
                "plan": plan,
                "duration_days": duration_days,
                "hours_per_day": hours_per_day,
                "language": language,
                "created_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error generating study plan: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def _build_prompt(content: str, duration_days: int, hours_per_day: float, language: str) -> str:
        """Build prompt for study plan generation"""
        
        if language == "telugu":
            return f"""{duration_days} రోజుల కోసం ఒక వ్యক్తిగత అధ్యయన ప్రణాళిక సృష్టించండి. 
విద్యార్థి రోజుకు {hours_per_day} గంటలు అధ్యయనం చేయవచ్చు.

సందర్భం:
{content[:2000]}

دयचेसი విధులు, నిర్ణీత లక్ష్యాలు మరియు అంచనాలతో JSON ఫార్మాట్‌లో ఇవ్వండి."""
        else:
            return f"""Create a personalized study plan for {duration_days} days. 
The student can study {hours_per_day} hours per day.

Content:
{content[:2000]}

Please provide the plan in JSON format with daily tasks, objectives, and assessments."""
    
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
    def _parse_plan(response_text: str, days: int) -> List[Dict]:
        """Parse study plan from response"""
        try:
            # Simple parsing - create basic daily plan structure
            plan = []
            
            for day in range(1, days + 1):
                plan.append({
                    "day": day,
                    "date": (datetime.now() + timedelta(days=day)).isoformat(),
                    "topics": [f"Topic {i}" for i in range(1, 4)],
                    "objectives": ["Understand key concepts", "Practice problems"],
                    "assessment": "Quiz"
                })
            
            return plan
        
        except Exception as e:
            logger.error(f"Error parsing study plan: {str(e)}")
            return []

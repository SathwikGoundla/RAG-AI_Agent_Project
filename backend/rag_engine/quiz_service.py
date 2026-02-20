"""
Quiz Service Module
Handles quiz session management, question tracking, and result calculation
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
import logging

from backend.database import QuizSession, QuizQuestion, UserQuizAnswer
from backend.utils.quiz_generator import QuizGenerator

logger = logging.getLogger(__name__)


class QuizService:
    """Service for managing quiz sessions and tracking"""
    
    def __init__(self, db: Session):
        """Initialize quiz service with database session"""
        self.db = db
        self.generator = QuizGenerator()
    
    def create_quiz_session(
        self,
        user_id: int,
        questions_data: List[Dict],
        num_questions: int,
        difficulty: str,
        language: str,
        topic: Optional[str] = None
    ) -> str:
        """
        Create a new quiz session
        
        Args:
            user_id: User ID
            questions_data: List of question dictionaries
            num_questions: Total number of questions
            difficulty: Difficulty level
            language: Language
            topic: Optional topic
            
        Returns:
            Quiz session ID
        """
        session_id = str(uuid.uuid4())
        
        try:
            # Create quiz session
            quiz_session = QuizSession(
                id=session_id,
                user_id=user_id,
                num_questions=num_questions,
                difficulty=difficulty,
                language=language,
                topic=topic,
                status="in_progress",
                start_time=datetime.utcnow()
            )
            self.db.add(quiz_session)
            self.db.flush()
            
            # Create quiz questions
            for idx, question_data in enumerate(questions_data, 1):
                question_id = str(uuid.uuid4())
                
                # Handle options - they might be a JSON string or list
                options = question_data.get("options")
                if isinstance(options, list):
                    import json
                    options = json.dumps(options)
                
                # Handle keywords for short answer - they might be a list
                keywords = question_data.get("answer_keywords")
                if isinstance(keywords, list):
                    import json
                    keywords = json.dumps(keywords)
                
                quiz_question = QuizQuestion(
                    id=question_id,
                    quiz_session_id=session_id,
                    question_number=question_data.get("question_number", idx),
                    question_type=question_data.get("question_type", "multiple_choice"),
                    question_text=question_data.get("question", ""),
                    difficulty=question_data.get("difficulty", difficulty),
                    topic=question_data.get("topic"),
                    options=options,
                    correct_answer=question_data.get("correct_answer"),
                    expected_answer=question_data.get("expected_answer"),
                    answer_keywords=keywords,
                    explanation=question_data.get("explanation", ""),
                    source_document=question_data.get("source_document")
                )
                self.db.add(quiz_question)
            
            self.db.commit()
            logger.info(f"Created quiz session {session_id} for user {user_id}")
            return session_id
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating quiz session: {str(e)}")
            raise
    
    def get_quiz_session(self, session_id: str, user_id: int) -> Optional[QuizSession]:
        """Get quiz session (with user isolation check)"""
        return self.db.query(QuizSession).filter(
            QuizSession.id == session_id,
            QuizSession.user_id == user_id
        ).first()
    
    def get_quiz_question(self, question_id: str, session_id: str) -> Optional[QuizQuestion]:
        """Get quiz question by ID and session"""
        return self.db.query(QuizQuestion).filter(
            QuizQuestion.id == question_id,
            QuizQuestion.quiz_session_id == session_id
        ).first()
    
    def get_next_question(self, session_id: str) -> Optional[QuizQuestion]:
        """Get next unanswered question in session"""
        # Get questions that haven't been answered yet
        answered_question_ids = self.db.query(UserQuizAnswer.question_id).filter(
            UserQuizAnswer.quiz_session_id == session_id
        ).all()
        answered_ids = [q[0] for q in answered_question_ids]
        
        next_question = self.db.query(QuizQuestion).filter(
            QuizQuestion.quiz_session_id == session_id,
            ~QuizQuestion.id.in_(answered_ids) if answered_ids else True
        ).order_by(QuizQuestion.question_number).first()
        
        return next_question
    
    def submit_answer(
        self,
        session_id: str,
        question_id: str,
        user_answer: str,
        time_taken_seconds: Optional[int] = None
    ) -> Dict:
        """
        Submit an answer to a quiz question
        
        Args:
            session_id: Quiz session ID
            question_id: Question ID
            user_answer: User's answer
            time_taken_seconds: Time spent on question
            
        Returns:
            Dictionary with result
        """
        try:
            question = self.get_quiz_question(question_id, session_id)
            if not question:
                return {"status": "error", "message": "Question not found"}
            
            # Determine if answer is correct
            is_correct = False
            feedback = ""
            confidence = 0.0
            
            if question.question_type == "multiple_choice":
                is_correct = user_answer.strip() == question.correct_answer.strip()
                feedback = "Correct!" if is_correct else f"Incorrect. The correct answer is: {question.correct_answer}"
                confidence = 0.95 if is_correct else 0.1
            
            elif question.question_type == "true_false":
                is_correct = user_answer.strip().lower() == question.correct_answer.strip().lower()
                feedback = "Correct!" if is_correct else f"Incorrect. The correct answer is: {question.correct_answer}"
                confidence = 0.95 if is_correct else 0.1
            
            elif question.question_type == "short_answer":
                # Use the quiz generator's grading method
                import json
                keywords = []
                if question.answer_keywords:
                    try:
                        keywords = json.loads(question.answer_keywords)
                    except:
                        keywords = []
                
                grading_result = QuizGenerator.grade_short_answer(
                    user_answer,
                    question.expected_answer or question.correct_answer,
                    keywords
                )
                is_correct = grading_result["is_correct"]
                confidence = grading_result["confidence"]
                feedback = "Your answer is acceptable." if is_correct else "Your answer doesn't match the expected answer."
            
            # Record the answer
            user_answer_record = UserQuizAnswer(
                id=str(uuid.uuid4()),
                quiz_session_id=session_id,
                question_id=question_id,
                user_answer=user_answer,
                is_correct=is_correct,
                time_taken_seconds=time_taken_seconds,
                feedback=feedback,
                confidence_score=confidence
            )
            self.db.add(user_answer_record)
            self.db.flush()
            
            # Update session statistics
            session = self.get_quiz_session(session_id, question.quiz_session_id)
            session.attempted_count += 1
            if is_correct:
                session.correct_count += 1
            self.db.commit()
            
            return {
                "status": "success",
                "is_correct": is_correct,
                "feedback": feedback,
                "explanation": question.explanation,
                "confidence": confidence
            }
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error submitting answer: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_quiz_results(self, session_id: str, user_id: int) -> Optional[Dict]:
        """Get results for completed quiz session"""
        session = self.get_quiz_session(session_id, user_id)
        if not session:
            return None
        
        # Calculate score
        score = 0.0
        if session.num_questions > 0:
            score = (session.correct_count / session.num_questions) * 100
        
        # Calculate duration
        duration_seconds = None
        if session.end_time:
            duration_seconds = int((session.end_time - session.start_time).total_seconds())
        
        # Update session
        session.score = score
        session.duration_seconds = duration_seconds
        self.db.commit()
        
        return {
            "session_id": session_id,
            "num_questions": session.num_questions,
            "correct_count": session.correct_count,
            "attempted_count": session.attempted_count,
            "score": score,
            "difficulty": session.difficulty,
            "language": session.language,
            "status": session.status,
            "duration_seconds": duration_seconds,
            "created_at": session.created_at
        }
    
    def complete_quiz_session(self, session_id: str, user_id: int) -> bool:
        """Mark quiz session as completed"""
        try:
            session = self.get_quiz_session(session_id, user_id)
            if not session:
                return False
            
            session.status = "completed"
            session.end_time = datetime.utcnow()
            self.db.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error completing quiz session: {str(e)}")
            return False
    
    def get_user_quiz_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's quiz history"""
        sessions = self.db.query(QuizSession).filter(
            QuizSession.user_id == user_id,
            QuizSession.status == "completed"
        ).order_by(QuizSession.created_at.desc()).limit(limit).all()
        
        history = []
        for session in sessions:
            score = 0.0
            if session.num_questions > 0:
                score = (session.correct_count / session.num_questions) * 100
            
            history.append({
                "session_id": session.id,
                "num_questions": session.num_questions,
                "correct_count": session.correct_count,
                "attempted_count": session.attempted_count,
                "score": score,
                "difficulty": session.difficulty,
                "status": session.status,
                "created_at": session.created_at
            })
        
        return history
    
    def get_user_quiz_statistics(self, user_id: int) -> Dict:
        """Get user's quiz statistics"""
        sessions = self.db.query(QuizSession).filter(
            QuizSession.user_id == user_id,
            QuizSession.status == "completed"
        ).all()
        
        if not sessions:
            return {
                "total_quizzes": 0,
                "total_questions_attempted": 0,
                "total_correct": 0,
                "average_score": 0.0
            }
        
        total_questions = sum(s.num_questions for s in sessions)
        total_correct = sum(s.correct_count for s in sessions)
        
        return {
            "total_quizzes": len(sessions),
            "total_questions_attempted": total_questions,
            "total_correct": total_correct,
            "average_score": (total_correct / total_questions * 100) if total_questions > 0 else 0.0
        }

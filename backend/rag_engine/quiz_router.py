"""
Quiz Router Module
API endpoints for quiz generation, session management, and result tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from backend.auth.security import get_current_user
from backend.database import get_db
from backend.models import (
    QuizGenerateRequest,
    QuizSessionResponse,
    QuizSessionStartResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    QuizResultsResponse,
    QuizHistoryResponse,
    QuizHistoryItem,
    QuizDisplayQuestion
)
from backend.rag_engine.quiz_service import QuizService
from backend.utils.quiz_generator import QuizGenerator

router = APIRouter()
retriever_service = None  # Will be initialized lazily
generator = QuizGenerator()


def get_retriever():
    """Get retriever service instance"""
    global retriever_service
    if retriever_service is None:
        from backend.rag_engine.retriever import RetrieverService
        retriever_service = RetrieverService()
    return retriever_service


@router.post("/generate", response_model=QuizSessionStartResponse, tags=["Quiz"])
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new quiz from user's uploaded documents
    
    Args:
        request: Quiz generation parameters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Quiz session with first question
    """
    try:
        user_id = current_user.get("user_id")
        
        # Retrieve relevant document chunks for the quiz
        logger.info(f"Generating quiz for user {user_id}: {request.num_questions} questions, {request.difficulty} difficulty")
        
        # Get user's documents
        try:
            # Retrieve documents as context
            retriever = get_retriever()
            context_query = "important key concepts summary overview"
            retrieved_docs = retriever.retrieve_chunks(
                query_text=context_query,
                user_id=str(user_id),
                n_results=10
            )
            
            if not retrieved_docs:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No documents uploaded. Please upload documents first to generate a quiz."
                )
            
            # Combine retrieved documents into context
            combined_content = "\n\n".join([
                doc.get("text", "") or doc.get("chunk_content", "") for doc in retrieved_docs[:10]
            ])
            
            # Filter by topic if specified
            if request.topic:
                combined_content = f"Topic: {request.topic}\n\n{combined_content}"
        
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Error retrieving documents: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error retrieving documents for quiz generation"
            )
        
        # Generate quiz questions
        quiz_result = generator.generate_questions(
            content=combined_content,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            language=request.language,
            question_types=request.question_types,
            topic=request.topic
        )
        
        if quiz_result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate quiz: {quiz_result.get('message', 'Unknown error')}"
            )
        
        questions_data = quiz_result.get("questions", [])
        
        if not questions_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No questions were generated. Please try again."
            )
        
        # Create quiz session in database
        quiz_service = QuizService(db)
        session_id = quiz_service.create_quiz_session(
            user_id=user_id,
            questions_data=questions_data,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            language=request.language,
            topic=request.topic
        )
        
        # Get first question
        first_question_obj = quiz_service.get_next_question(session_id)
        if not first_question_obj:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load first question"
            )
        
        # Format first question for display
        import json
        options = None
        if first_question_obj.options:
            try:
                options = json.loads(first_question_obj.options)
            except:
                options = first_question_obj.options
        
        first_question = QuizDisplayQuestion(
            id=first_question_obj.id,
            question_number=first_question_obj.question_number,
            question_type=first_question_obj.question_type,
            question_text=first_question_obj.question_text,
            difficulty=first_question_obj.difficulty,
            options=options
        )
        
        logger.info(f"Quiz session {session_id} created for user {user_id}")
        
        return QuizSessionStartResponse(
            session_id=session_id,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            language=request.language,
            first_question=first_question,
            created_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{session_id}", response_model=QuizSessionResponse, tags=["Quiz"])
async def get_quiz_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quiz session details"""
    try:
        user_id = current_user.get("user_id")
        quiz_service = QuizService(db)
        
        session = quiz_service.get_quiz_session(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz session not found"
            )
        
        questions = []
        for q in session.questions:
            import json
            options = None
            if q.options:
                try:
                    options = json.loads(q.options)
                except:
                    options = q.options
            
            questions.append({
                "id": q.id,
                "question_number": q.question_number,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "difficulty": q.difficulty,
                "options": options,
                "correct_answer": q.correct_answer,
                "expected_answer": q.expected_answer,
                "explanation": q.explanation,
                "source_document": q.source_document,
                "topic": q.topic
            })
        
        return QuizSessionResponse(
            session_id=session.id,
            num_questions=session.num_questions,
            difficulty=session.difficulty,
            language=session.language,
            topic=session.topic,
            status=session.status,
            questions=questions,
            created_at=session.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz session: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{session_id}/answer", response_model=SubmitAnswerResponse, tags=["Quiz"])
async def submit_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit an answer to a quiz question"""
    try:
        user_id = current_user.get("user_id")
        quiz_service = QuizService(db)
        
        # Verify session belongs to user
        session = quiz_service.get_quiz_session(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz session not found"
            )
        
        # Submit answer
        result = quiz_service.submit_answer(
            session_id=session_id,
            question_id=request.question_id,
            user_answer=request.user_answer,
            time_taken_seconds=request.time_taken_seconds
        )
        
        if result.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to submit answer")
            )
        
        # Check if all questions have been answered
        remaining_question = quiz_service.get_next_question(session_id)
        next_question = None
        session_status = "in_progress"
        
        if not remaining_question:
            # Quiz completed
            session_status = "completed"
            quiz_service.complete_quiz_session(session_id, user_id)
        else:
            # Format next question
            import json
            options = None
            if remaining_question.options:
                try:
                    options = json.loads(remaining_question.options)
                except:
                    options = remaining_question.options
            
            next_question = QuizDisplayQuestion(
                id=remaining_question.id,
                question_number=remaining_question.question_number,
                question_type=remaining_question.question_type,
                question_text=remaining_question.question_text,
                difficulty=remaining_question.difficulty,
                options=options
            )
        
        return SubmitAnswerResponse(
            is_correct=result.get("is_correct"),
            explanation=result.get("explanation", ""),
            feedback=result.get("feedback"),
            next_question=next_question,
            session_status=session_status
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting answer: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{session_id}/results", response_model=QuizResultsResponse, tags=["Quiz"])
async def get_quiz_results(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get results for completed quiz"""
    try:
        user_id = current_user.get("user_id")
        quiz_service = QuizService(db)
        
        results = quiz_service.get_quiz_results(session_id, user_id)
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz session not found"
            )
        
        return QuizResultsResponse(**results)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz results: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history/all", response_model=QuizHistoryResponse, tags=["Quiz"])
async def get_quiz_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's quiz history"""
    try:
        user_id = current_user.get("user_id")
        quiz_service = QuizService(db)
        
        history = quiz_service.get_user_quiz_history(user_id, limit)
        stats = quiz_service.get_user_quiz_statistics(user_id)
        
        quiz_items = [
            QuizHistoryItem(**item) for item in history
        ]
        
        return QuizHistoryResponse(
            total_quizzes=stats["total_quizzes"],
            total_questions_attempted=stats["total_questions_attempted"],
            average_score=stats["average_score"],
            quizzes=quiz_items
        )
    
    except Exception as e:
        logger.error(f"Error getting quiz history: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

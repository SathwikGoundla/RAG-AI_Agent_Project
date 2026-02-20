"""
Quiz Generation & Practice Interface
Generate quizzes from your documents for learning and practice
"""

import streamlit as st
import requests
from typing import Optional, Dict, List
import time
from datetime import datetime

# ============================================
# Configuration
# ============================================

BACKEND_URL = st.secrets.get("backend_url", "http://localhost:8000")
API_V1_STR = "/api/v1"

# ============================================
# API Functions
# ============================================

def api_request(
    method: str,
    endpoint: str,
    json_data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    use_token: bool = True
) -> Optional[requests.Response]:
    """Make API request with automatic token injection."""
    headers = {}
    
    if use_token and st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        response = requests.request(
            method=method,
            url=url,
            json=json_data,
            params=params,
            headers=headers,
            timeout=60
        )
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Is the server running?")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timeout. Please try again.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def generate_quiz(
    num_questions: int = 5,
    difficulty: str = "medium",
    language: str = "english",
    topic: Optional[str] = None,
    question_types: Optional[List[str]] = None
) -> Optional[Dict]:
    """Generate a quiz from uploaded documents."""
    payload = {
        "num_questions": num_questions,
        "difficulty": difficulty,
        "language": language,
    }
    if topic:
        payload["topic"] = topic
    if question_types:
        payload["question_types"] = question_types
    
    response = api_request(
        "POST",
        f"{API_V1_STR}/quiz/generate",
        json_data=payload
    )
    
    if response and response.status_code == 200:
        return response.json()
    elif response:
        st.error(f"Error: {response.json().get('detail', 'Failed to generate quiz')}")
        return None
    return None


def submit_quiz_answer(
    session_id: str,
    question_id: str,
    user_answer: str,
    time_taken: int = 0
) -> Optional[Dict]:
    """Submit answer to a quiz question."""
    response = api_request(
        "POST",
        f"{API_V1_STR}/quiz/{session_id}/answer",
        json_data={
            "session_id": session_id,
            "question_id": question_id,
            "user_answer": user_answer,
            "time_taken_seconds": time_taken
        }
    )
    
    if response and response.status_code == 200:
        return response.json()
    elif response:
        st.error(f"Error: {response.json().get('detail', 'Failed to submit answer')}")
        return None
    return None


def get_quiz_results(session_id: str) -> Optional[Dict]:
    """Get results for a completed quiz."""
    response = api_request(
        "GET",
        f"{API_V1_STR}/quiz/{session_id}/results"
    )
    
    if response and response.status_code == 200:
        return response.json()
    elif response:
        st.error(f"Error: {response.json().get('detail', 'Failed to get results')}")
        return None
    return None


def get_quiz_history() -> Optional[Dict]:
    """Get user's quiz history."""
    response = api_request(
        "GET",
        f"{API_V1_STR}/quiz/history/all"
    )
    
    if response and response.status_code == 200:
        return response.json()
    elif response:
        st.error(f"Error: {response.json().get('detail', 'Failed to get history')}")
        return None
    return None


# ============================================
# UI Components
# ============================================

def display_question(question: Dict, question_num: int, session_state_prefix: str = ""):
    """Display a single quiz question."""
    st.markdown(f"### Question {question_num}: {question.get('difficulty', 'medium').upper()} Level")
    
    st.markdown(question.get('question_text', ''))
    
    question_type = question.get('question_type', 'multiple_choice')
    question_id = question.get('id', '')
    key_prefix = f"{session_state_prefix}_{question_id}"
    
    if question_type == 'multiple_choice':
        options = question.get('options', [])
        st.markdown("**Select one option:**")
        
        selected = st.radio(
            "Options",
            options=options,
            key=f"mcq_{key_prefix}",
            label_visibility="collapsed"
        )
        return selected
    
    elif question_type == 'short_answer':
        st.markdown("**Type your answer:**")
        answer = st.text_area(
            "Answer",
            key=f"short_{key_prefix}",
            label_visibility="collapsed",
            height=100
        )
        return answer
    
    elif question_type == 'true_false':
        st.markdown("**Select True or False:**")
        answer = st.radio(
            "Answer",
            options=["True", "False"],
            key=f"tf_{key_prefix}",
            label_visibility="collapsed"
        )
        return answer
    
    return None


def show_quiz_statistics(correct: int, total: int, duration_sec: Optional[int] = None):
    """Display quiz statistics."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Questions", total)
    
    with col2:
        st.metric("Correct", correct)
    
    with col3:
        percentage = (correct / total * 100) if total > 0 else 0
        st.metric("Score", f"{percentage:.1f}%")
    
    with col4:
        if duration_sec:
            minutes = duration_sec // 60
            seconds = duration_sec % 60
            st.metric("Time", f"{minutes}m {seconds}s")
        else:
            st.metric("Time", "N/A")


# ============================================
# Main Page
# ============================================

def main():
    """Main quiz page."""
    st.set_page_config(page_title="Quiz", layout="wide")
    
    st.header("📝 Quiz & Practice")
    st.markdown("Generate interactive quizzes based on your uploaded documents to test your knowledge.")
    
    # Initialize session state
    if "quiz_session_id" not in st.session_state:
        st.session_state.quiz_session_id = None
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = None
    if "current_question_idx" not in st.session_state:
        st.session_state.current_question_idx = 0
    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "question_times" not in st.session_state:
        st.session_state.question_times = {}
    if "quiz_results" not in st.session_state:
        st.session_state.quiz_results = None
    if "quiz_start_time" not in st.session_state:
        st.session_state.quiz_start_time = None
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Take Quiz", "📊 Results", "📈 History"])
    
    # ============================================
    # TAB 1: TAKE QUIZ
    # ============================================
    with tab1:
        if not st.session_state.quiz_started:
            # Quiz Configuration
            st.subheader("Quiz Configuration")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                num_questions = st.slider(
                    "Number of Questions",
                    min_value=1,
                    max_value=50,
                    value=10,
                    step=1
                )
            
            with col2:
                difficulty = st.selectbox(
                    "Difficulty Level",
                    ["easy", "medium", "hard"],
                    index=1
                )
            
            with col3:
                language = st.selectbox(
                    "Language",
                    ["english", "telugu"],
                    index=0
                )
            
            with col4:
                topic = st.text_input(
                    "Optional Topic Filter",
                    placeholder="e.g., 'Machine Learning'"
                )
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Question Types:**")
                include_mcq = st.checkbox("Multiple Choice", value=True)
                include_short = st.checkbox("Short Answer", value=True)
                include_tf = st.checkbox("True/False", value=True)
            
            with col2:
                st.markdown("**Summary:**")
                st.markdown(f"- Questions: **{num_questions}**")
                st.markdown(f"- Difficulty: **{difficulty.title()}**")
                st.markdown(f"- Language: **{language.title()}**")
                if topic:
                    st.markdown(f"- Topic: **{topic}**")
            
            st.divider()
            
            if st.button("🚀 Generate & Start Quiz", type="primary", use_container_width=True):
                with st.spinner("Generating quiz..."):
                    question_types = []
                    if include_mcq:
                        question_types.append("multiple_choice")
                    if include_short:
                        question_types.append("short_answer")
                    if include_tf:
                        question_types.append("true_false")
                    
                    quiz_response = generate_quiz(
                        num_questions=num_questions,
                        difficulty=difficulty,
                        language=language,
                        topic=topic if topic else None,
                        question_types=question_types if question_types else None
                    )
                
                if quiz_response:
                    st.session_state.quiz_session_id = quiz_response.get("session_id")
                    st.session_state.quiz_data = quiz_response
                    st.session_state.quiz_started = True
                    st.session_state.quiz_start_time = time.time()
                    st.session_state.current_question_idx = 0
                    st.rerun()
        
        else:
            # Display Quiz
            if st.session_state.quiz_data and st.session_state.quiz_session_id:
                quiz = st.session_state.quiz_data
                questions = quiz.get('questions', [])
                
                if not questions:
                    st.error("No questions available in this quiz.")
                else:
                    # Progress bar
                    progress = (st.session_state.current_question_idx) / len(questions)
                    st.progress(progress, f"Question {st.session_state.current_question_idx + 1} of {len(questions)}")
                    
                    st.divider()
                    
                    # Display current question
                    current_q_idx = st.session_state.current_question_idx
                    current_question = questions[current_q_idx]
                    
                    # Get user's answer if exists
                    q_id = current_question.get('id')
                    user_answer = st.session_state.quiz_answers.get(q_id, "")
                    
                    # Show question start time for this question
                    if q_id not in st.session_state.question_times:
                        st.session_state.question_times[q_id] = time.time()
                    
                    # Display question
                    with st.container():
                        user_answer = display_question(
                            current_question,
                            current_q_idx + 1,
                            session_state_prefix="quiz"
                        )
                        
                        if user_answer is not None:
                            st.session_state.quiz_answers[q_id] = user_answer
                    
                    st.divider()
                    
                    # Navigation buttons
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col1:
                        if st.session_state.current_question_idx > 0:
                            if st.button("⬅️ Previous", use_container_width=True):
                                st.session_state.current_question_idx -= 1
                                st.rerun()
                    
                    with col2:
                        if st.session_state.current_question_idx < len(questions) - 1:
                            if st.button("Next ➡️", use_container_width=True, type="secondary"):
                                st.session_state.current_question_idx += 1
                                st.rerun()
                        else:
                            if st.button("✅ Submit Quiz", use_container_width=True, type="primary"):
                                # Submit all answers
                                with st.spinner("Submitting quiz..."):
                                    all_submitted = True
                                    for q in questions:
                                        q_id = q.get('id')
                                        answer = st.session_state.quiz_answers.get(q_id, "")
                                        
                                        if not answer:
                                            st.warning(f"Question {q.get('question_number', '?')} not answered!")
                                            all_submitted = False
                                            continue
                                        
                                        time_taken = int(time.time() - st.session_state.question_times.get(q_id, time.time()))
                                        
                                        result = submit_quiz_answer(
                                            st.session_state.quiz_session_id,
                                            q_id,
                                            answer,
                                            time_taken
                                        )
                                    
                                    if all_submitted:
                                        # Get results
                                        results = get_quiz_results(st.session_state.quiz_session_id)
                                        if results:
                                            st.session_state.quiz_results = results
                                            st.session_state.quiz_started = False
                                            st.success("✅ Quiz submitted successfully!")
                                            st.rerun()
                    
                    with col3:
                        if st.button("🔄 Cancel", use_container_width=True, type="secondary"):
                            st.session_state.quiz_started = False
                            st.session_state.quiz_session_id = None
                            st.session_state.quiz_data = None
                            st.session_state.quiz_answers = {}
                            st.session_state.question_times = {}
                            st.rerun()
    
    # ============================================
    # TAB 2: RESULTS
    # ============================================
    with tab2:
        st.subheader("Latest Quiz Results")
        
        if st.session_state.quiz_results:
            results = st.session_state.quiz_results
            
            # Display statistics
            show_quiz_statistics(
                results.get('correct_count', 0),
                results.get('num_questions', 0),
                results.get('duration_seconds')
            )
            
            st.divider()
            
            # Score visualization
            score = results.get('score', 0)
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Performance:**")
                if score >= 80:
                    st.success(f"Excellent! Score: {score:.1f}%")
                elif score >= 60:
                    st.info(f"Good! Score: {score:.1f}%")
                elif score >= 40:
                    st.warning(f"Needs Improvement. Score: {score:.1f}%")
                else:
                    st.error(f"Review Needed. Score: {score:.1f}%")
            
            with col2:
                st.markdown("**Quiz Info:**")
                st.markdown(f"- Difficulty: **{results.get('difficulty', 'N/A').title()}**")
                st.markdown(f"- Language: **{results.get('language', 'N/A').title()}**")
                st.markdown(f"- Status: **{results.get('status', 'N/A').title()}**")
            
            st.divider()
            
            # Clear results button
            if st.button("🔄 Take Another Quiz", type="secondary", use_container_width=True):
                st.session_state.quiz_results = None
                st.rerun()
        else:
            st.info("📭 No quiz results yet. Take a quiz to see your results here!")
    
    # ============================================
    # TAB 3: HISTORY
    # ============================================
    with tab3:
        st.subheader("Quiz History & Statistics")
        
        with st.spinner("Loading history..."):
            history = get_quiz_history()
        
        if history and history.get('quizzes'):
            # Overall statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Quizzes", history.get('total_quizzes', 0))
            
            with col2:
                st.metric("Questions Attempted", history.get('total_questions_attempted', 0))
            
            with col3:
                st.metric("Average Score", f"{history.get('average_score', 0):.1f}%")
            
            with col4:
                if history.get('total_questions_attempted', 0) > 0:
                    accuracy = (history.get('total_questions_attempted', 0) / max(1, history.get('total_questions_attempted', 1))) * 100
                    st.metric("Accuracy", f"{accuracy:.1f}%")
            
            st.divider()
            
            # Quiz list
            st.markdown("**Previous Quizzes:**")
            
            for quiz in history.get('quizzes', []):
                score = quiz.get('score', 0)
                score_color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Score", f"{score:.1f}%", label_visibility="collapsed")
                
                with col2:
                    st.metric("Questions", quiz.get('num_questions', 0), label_visibility="collapsed")
                
                with col3:
                    st.metric("Correct", quiz.get('correct_count', 0), label_visibility="collapsed")
                
                with col4:
                    st.metric("Difficulty", quiz.get('difficulty', 'N/A').title(), label_visibility="collapsed")
                
                with col5:
                    created = quiz.get('created_at', 'N/A')
                    st.markdown(f"📅 {created[:10]}")
                
                st.divider()
        else:
            st.info("📭 No quiz history yet. Take a quiz to get started!")

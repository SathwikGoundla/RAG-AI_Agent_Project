"""
Context Manager for RAG Pipeline
Manages conversation history, context windows, and session state
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class Message:
    """Represents a single message in conversation"""
    
    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }


class ContextManager:
    """
    Manages conversation context and context windows.
    
    Features:
    - Session creation and tracking
    - Message history storage
    - Context window management
    - Token counting
    - Conversation summarization
    """
    
    def __init__(self, max_context_tokens: int = 4000, max_messages: int = 20):
        """
        Initialize context manager
        
        Args:
            max_context_tokens: Maximum tokens to keep in context window
            max_messages: Maximum messages to keep in history
        """
        self.max_context_tokens = max_context_tokens
        self.max_messages = max_messages
        self.conversations: Dict[str, List[Message]] = {}
        self.sessions: Dict[str, Dict] = {}
        logger.info(f"ContextManager initialized (max_tokens={max_context_tokens}, max_messages={max_messages})")
    
    def create_session(self, user_id: int) -> str:
        """
        Create a new conversation session
        
        Args:
            user_id: ID of user
            
        Returns:
            Session ID
        """
        import uuid
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "messages_count": 0
        }
        
        self.conversations[session_id] = []
        logger.info(f"Created session {session_id} for user {user_id}")
        
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add message to conversation history
        
        Args:
            session_id: Session ID
            role: "user" or "assistant"
            content: Message content
        """
        if session_id not in self.conversations:
            logger.warning(f"Session {session_id} not found, creating new one")
            self.conversations[session_id] = []
            self.sessions[session_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "messages_count": 0
            }
        
        message = Message(role, content)
        self.conversations[session_id].append(message)
        
        if session_id in self.sessions:
            self.sessions[session_id]["messages_count"] += 1
        
        logger.debug(f"Added {role} message to session {session_id}")
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of messages as dictionaries
        """
        if session_id not in self.conversations:
            logger.warning(f"Session {session_id} not found")
            return []
        
        messages = self.conversations[session_id]
        return [msg.to_dict() for msg in messages[-self.max_messages:]]
    
    def get_context_window(self, session_id: str, max_tokens: Optional[int] = None) -> str:
        """
        Get context window for current session (recent messages)
        
        Args:
            session_id: Session ID
            max_tokens: Maximum tokens to include (uses default if None)
            
        Returns:
            Formatted context string
        """
        if session_id not in self.conversations:
            return ""
        
        max_tokens = max_tokens or self.max_context_tokens
        messages = self.conversations[session_id]
        
        # Build context from recent messages, respecting token limit
        context_parts = []
        token_count = 0
        
        # Work backwards through messages
        for message in reversed(messages):
            # Estimate tokens (rough: ~4 chars per token)
            msg_tokens = len(message.content) // 4 + 10
            
            if token_count + msg_tokens > max_tokens:
                break
            
            context_parts.insert(0, f"{message.role}: {message.content}")
            token_count += msg_tokens
        
        logger.debug(f"Context window for {session_id}: {token_count} tokens, {len(context_parts)} messages")
        return "\n".join(context_parts)
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Uses rough approximation: 1 token ≈ 4 characters
        
        Args:
            text: Text to count
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get session metadata
        
        Args:
            session_id: Session ID
            
        Returns:
            Session info or None if not found
        """
        if session_id not in self.sessions:
            return None
        
        return {
            **self.sessions[session_id],
            "message_count": len(self.conversations.get(session_id, []))
        }
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear all messages in a session
        
        Args:
            session_id: Session ID
        """
        if session_id in self.conversations:
            self.conversations[session_id] = []
            logger.info(f"Cleared session {session_id}")
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete entire session
        
        Args:
            session_id: Session ID
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
        if session_id in self.sessions:
            del self.sessions[session_id]
        logger.info(f"Deleted session {session_id}")
    
    def summarize_conversation(self, session_id: str) -> str:
        """
        Create a summary of the conversation
        
        Args:
            session_id: Session ID
            
        Returns:
            Conversation summary
        """
        if session_id not in self.conversations:
            return ""
        
        messages = self.conversations[session_id]
        
        if not messages:
            return "Empty conversation"
        
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        summary = f"""
Conversation Summary:
- Total messages: {len(messages)}
- User messages: {len(user_messages)}
- Assistant responses: {len(assistant_messages)}
- Duration: From {messages[0].timestamp} to {messages[-1].timestamp}

Key topics:
"""
        
        # Add first few user messages as indicators of topics
        for i, msg in enumerate(user_messages[:3]):
            summary += f"\n{i+1}. {msg.content[:100]}..."
        
        return summary


# Global context manager instance
_context_manager = ContextManager()


def get_context_manager() -> ContextManager:
    """Get global context manager instance"""
    return _context_manager

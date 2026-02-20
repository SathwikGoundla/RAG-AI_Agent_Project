#!/usr/bin/env python3
"""
Citation Implementation Verification Script
Verifies that all components are working correctly
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_imports():
    """Verify all required modules can be imported"""
    print("🔍 Verifying imports...")
    
    try:
        # Backend utilities
        from backend.utils.citation_formatter import Citation, CitationFormatter, ConfidenceScoreCalculator
        print("  ✅ citation_formatter.py")
        
        # Frontend components
        from frontend.components.citation_display import (
            display_citation_badge, 
            get_score_color,
            display_single_citation,
            display_citations_section
        )
        print("  ✅ citation_display.py")
        
        # Backend models
        from backend.models import CitationInfo, ExplainableQueryResponse, ExplainableChatResponse
        print("  ✅ models.py (CitationInfo, Explainable*Response)")
        
        # Backend RAG components
        from backend.rag_engine.retriever import RetrieverService
        from backend.rag_engine.router import QueryResponse, ChatResponse
        print("  ✅ router.py (QueryResponse, ChatResponse)")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


def verify_citation_formatter():
    """Verify citation formatting works"""
    print("\n🧪 Testing citation formatter...")
    
    try:
        from backend.utils.citation_formatter import Citation, CitationFormatter, ConfidenceScoreCalculator
        
        # Create sample citation
        citation = Citation(
            document_name="test.pdf",
            chunk_index=0,
            page_number=1,
            confidence_score=0.92,
            similarity_score=0.85,
            excerpt="Sample text excerpt",
            chunk_id="chunk_0"
        )
        
        # Test conversion to dict
        citation_dict = citation.to_dict()
        assert citation_dict["document"] == "test.pdf"
        assert citation_dict["confidence"] == 0.92
        print("  ✅ Citation dataclass to_dict()")
        
        # Test formatting
        inline = CitationFormatter.format_inline_citation("test.pdf", page_number=1)
        assert "[test.pdf" in inline and "p.1" in inline
        print("  ✅ CitationFormatter.format_inline_citation()")
        
        # Test confidence calculation
        calc = ConfidenceScoreCalculator()
        label = calc.get_confidence_label(0.92)
        emoji = calc.get_confidence_emoji(0.92)
        assert label in ["Very High", "High", "Medium", "Low", "Very Low"]
        assert emoji in ["🟢", "🟡", "🟠", "🔴", "⚫"]
        print(f"  ✅ ConfidenceScoreCalculator (label={label}, emoji={emoji})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Formatter test failed: {e}")
        return False


def verify_models():
    """Verify Pydantic models are defined"""
    print("\n📋 Verifying models...")
    
    try:
        from backend.models import CitationInfo, ExplainableQueryResponse, ExplainableChatResponse
        
        # Test CitationInfo
        citation_info = CitationInfo(
            document="test.pdf",
            chunk_index=0,
            page=1,
            confidence=0.92,
            similarity=0.85,
            excerpt="Text",
            chunk_id="chunk_0"
        )
        print("  ✅ CitationInfo model")
        
        # Test ExplainableQueryResponse
        query_response = ExplainableQueryResponse(
            answer="Test answer",
            citations=[],
            answer_confidence=0.85,
            language="english",
            model_used="gpt-3.5-turbo",
            tokens_used={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            context_count=0
        )
        print("  ✅ ExplainableQueryResponse model")
        
        # Test ExplainableChatResponse
        chat_response = ExplainableChatResponse(
            message="Test message",
            citations=[],
            message_confidence=0.90,
            session_id="session_123",
            language="english"
        )
        print("  ✅ ExplainableChatResponse model")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Model test failed: {e}")
        return False


def verify_file_structure():
    """Verify required files exist"""
    print("\n📁 Verifying file structure...")
    
    files_to_check = [
        "backend/utils/citation_formatter.py",
        "frontend/components/citation_display.py",
        "backend/rag_engine/router.py",
        "backend/models.py",
        "frontend/pages/chat.py"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            # Get file size
            size = os.path.getsize(full_path)
            print(f"  ✅ {file_path} ({size} bytes)")
        else:
            print(f"  ❌ {file_path} NOT FOUND")
            all_exist = False
    
    return all_exist


def verify_router_citations():
    """Verify router builds citations properly"""
    print("\n🔌 Verifying router citations...")
    
    try:
        with open("backend/rag_engine/router.py", "r") as f:
            router_content = f.read()
        
        # Check for citation building
        checks = [
            ("similarity_score" in router_content, "Returns similarity_score"),
            ("citations.append" in router_content, "Builds citations list"),
            ("chunk_index" in router_content, "Includes chunk_index"),
            ("confidence" in router_content, "Includes confidence"),
        ]
        
        all_passed = True
        for check, desc in checks:
            if check:
                print(f"  ✅ {desc}")
            else:
                print(f"  ❌ {desc}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ Router verification failed: {e}")
        return False


def verify_chat_page_integration():
    """Verify chat.py integrates citation display"""
    print("\n🎨 Verifying chat.py integration...")
    
    try:
        with open("frontend/pages/chat.py", "r") as f:
            chat_content = f.read()
        
        checks = [
            ("display_message" in chat_content, "display_message() function"),
            ("confidence" in chat_content, "Displays confidence metrics"),
            ("similarity" in chat_content, "Displays similarity scores"),
            ("emoji" in chat_content or "🟢" in chat_content, "Uses emoji badges"),
            ("display_search_results" in chat_content, "display_search_results() function"),
        ]
        
        all_passed = True
        for check, desc in checks:
            if check:
                print(f"  ✅ {desc}")
            else:
                print(f"  ❌ {desc}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ Chat.py verification failed: {e}")
        return False


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("🚀 Citation Implementation Verification")
    print("=" * 60)
    
    # Change to project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    results = []
    
    # Run verifications
    results.append(("File Structure", verify_file_structure()))
    results.append(("Model Definitions", verify_models()))
    results.append(("Router Citations", verify_router_citations()))
    results.append(("Chat Integration", verify_chat_page_integration()))
    
    # Import tests (only if other tests pass)
    if results[0][1]:  # If file structure OK
        results.append(("Imports", verify_imports()))
        results.append(("Citation Formatter", verify_citation_formatter()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Verification Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:.<40} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Total: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

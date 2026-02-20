"""
Citation Formatting Utilities
Formats citations and confidence scores for explainable AI
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Citation:
    """Represents a citation with confidence and metadata"""
    document_name: str
    chunk_index: int
    page_number: Optional[int]
    confidence_score: float  # 0-1 scale
    similarity_score: float  # 0-1 scale
    excerpt: str
    chunk_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert citation to dictionary"""
        return {
            "document": self.document_name,
            "chunk_index": self.chunk_index,
            "page": self.page_number,
            "confidence": round(self.confidence_score, 3),
            "similarity": round(self.similarity_score, 3),
            "excerpt": self.excerpt,
            "chunk_id": self.chunk_id
        }


class CitationFormatter:
    """Formats citations for display and export"""
    
    @staticmethod
    def format_inline_citation(
        document_name: str,
        page_number: Optional[int] = None,
        chunk_index: Optional[int] = None
    ) -> str:
        """
        Format inline citation (for inline in text)
        Example: [Document.pdf, p.2]
        
        Args:
            document_name: Name of source document
            page_number: Page number if available
            chunk_index: Chunk index if available
            
        Returns:
            Formatted inline citation
        """
        parts = [document_name]
        
        if page_number:
            parts.append(f"p.{page_number}")
        elif chunk_index is not None:
            parts.append(f"chunk:{chunk_index}")
        
        return "[" + ", ".join(parts) + "]"
    
    @staticmethod
    def format_full_citation(
        document_name: str,
        page_number: Optional[int] = None,
        chunk_index: Optional[int] = None,
        confidence_score: Optional[float] = None,
        similarity_score: Optional[float] = None
    ) -> str:
        """
        Format full citation with confidence
        Example: Document.pdf (Page 2, Chunk 5) - Confidence: 0.95, Similarity: 0.89
        
        Args:
            document_name: Name of source document
            page_number: Page number if available
            chunk_index: Chunk index if available
            confidence_score: LLM confidence score (0-1)
            similarity_score: Vector similarity score (0-1)
            
        Returns:
            Formatted full citation
        """
        citation = document_name
        
        # Add location info
        location_parts = []
        if page_number:
            location_parts.append(f"Page {page_number}")
        if chunk_index is not None:
            location_parts.append(f"Chunk {chunk_index}")
        
        if location_parts:
            citation += f" ({', '.join(location_parts)})"
        
        # Add confidence scores
        scores = []
        if confidence_score is not None:
            scores.append(f"Confidence: {confidence_score:.1%}")
        if similarity_score is not None:
            scores.append(f"Similarity: {similarity_score:.1%}")
        
        if scores:
            citation += f" — {', '.join(scores)}"
        
        return citation
    
    @staticmethod
    def format_citation_block(
        citations: List[Citation],
        include_excerpts: bool = True
    ) -> str:
        """
        Format a block of citations for display
        
        Args:
            citations: List of Citation objects
            include_excerpts: Whether to include text excerpts
            
        Returns:
            Formatted citation block
        """
        if not citations:
            return "No citations available"
        
        lines = []
        lines.append("**Sources:**")
        
        for i, citation in enumerate(citations, 1):
            # Citation number and document
            line = f"{i}. {citation.document_name}"
            
            # Location
            location_parts = []
            if citation.page_number:
                location_parts.append(f"p.{citation.page_number}")
            if citation.chunk_index is not None:
                location_parts.append(f"chunk {citation.chunk_index}")
            
            if location_parts:
                line += f" ({', '.join(location_parts)})"
            
            # Scores
            scores = []
            if citation.confidence_score > 0:
                scores.append(f"Conf: {citation.confidence_score:.1%}")
            if citation.similarity_score > 0:
                scores.append(f"Sim: {citation.similarity_score:.1%}")
            
            if scores:
                line += f" [{', '.join(scores)}]"
            
            lines.append(line)
            
            # Excerpt
            if include_excerpts and citation.excerpt:
                excerpt = citation.excerpt[:150]
                if len(citation.excerpt) > 150:
                    excerpt += "..."
                lines.append(f"   > {excerpt}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_harvard_style(
        document_name: str,
        page_number: Optional[int] = None,
        year: Optional[int] = None
    ) -> str:
        """
        Format citation in Harvard style
        Example: (Smith 2023, p. 42)
        
        Args:
            document_name: Name of source document
            page_number: Page number if available
            year: Year if available
            
        Returns:
            Harvard-style citation
        """
        citation_parts = []
        
        # Extract author/title (first word of filename)
        doc_parts = document_name.split(".")
        author = doc_parts[0]
        
        if year:
            citation_parts.append(f"{author} {year}")
        else:
            citation_parts.append(author)
        
        if page_number:
            citation_parts.append(f"p. {page_number}")
        
        return "(" + ", ".join(citation_parts) + ")"
    
    @staticmethod
    def format_footnote(
        citation_index: int,
        document_name: str,
        page_number: Optional[int] = None,
        excerpt: Optional[str] = None
    ) -> str:
        """
        Format as footnote
        
        Args:
            citation_index: Citation number
            document_name: Name of source document
            page_number: Page number if available
            excerpt: Text excerpt
            
        Returns:
            Footnote format
        """
        note = f"[{citation_index}] {document_name}"
        
        if page_number:
            note += f", page {page_number}"
        
        if excerpt:
            note += f": \"{excerpt[:100]}\""
        
        return note
    
    @staticmethod
    def format_mla_style(
        document_name: str,
        page_number: Optional[int] = None
    ) -> str:
        """
        Format citation in MLA style
        Example: Smith 42
        
        Args:
            document_name: Name of source document
            page_number: Page number if available
            
        Returns:
            MLA-style citation
        """
        doc_parts = document_name.split(".")
        author = doc_parts[0]
        
        if page_number:
            return f"{author} {page_number}"
        else:
            return author


class ConfidenceScoreCalculator:
    """Calculates and interprets confidence scores"""
    
    @staticmethod
    def calculate_overall_confidence(
        similarity_score: float,
        relevance_score: Optional[float] = None,
        llm_confidence: Optional[float] = None
    ) -> float:
        """
        Calculate overall confidence score combining multiple factors
        
        Args:
            similarity_score: Vector similarity (0-1)
            relevance_score: Manual relevance score (0-1), optional
            llm_confidence: LLM confidence (0-1), optional
            
        Returns:
            Overall confidence score (0-1)
        """
        scores = [similarity_score]
        
        if relevance_score is not None and 0 <= relevance_score <= 1:
            scores.append(relevance_score)
        
        if llm_confidence is not None and 0 <= llm_confidence <= 1:
            scores.append(llm_confidence)
        
        # Average the scores
        overall = sum(scores) / len(scores) if scores else 0
        return min(1.0, max(0.0, overall))  # Clamp between 0-1
    
    @staticmethod
    def get_confidence_label(confidence: float) -> str:
        """
        Get human-readable confidence label
        
        Args:
            confidence: Confidence score (0-1)
            
        Returns:
            Confidence label
        """
        if confidence >= 0.9:
            return "Very High"
        elif confidence >= 0.75:
            return "High"
        elif confidence >= 0.6:
            return "Medium"
        elif confidence >= 0.4:
            return "Low"
        else:
            return "Very Low"
    
    @staticmethod
    def get_confidence_emoji(confidence: float) -> str:
        """
        Get emoji representing confidence level
        
        Args:
            confidence: Confidence score (0-1)
            
        Returns:
            Confidence emoji
        """
        if confidence >= 0.9:
            return "🟢"  # Very High - Green
        elif confidence >= 0.75:
            return "🟡"  # High - Yellow-Green
        elif confidence >= 0.6:
            return "🟠"  # Medium - Orange
        elif confidence >= 0.4:
            return "🔴"  # Low - Red
        else:
            return "⚫"  # Very Low - Black


def format_answer_with_citations(
    answer: str,
    citations: List[Citation],
    include_confidence: bool = True,
    style: str = "inline"  # "inline", "footnote", "harvard"
) -> Tuple[str, str]:
    """
    Format answer text with inline citations
    
    Args:
        answer: Main answer text
        citations: List of Citation objects
        include_confidence: Whether to include confidence scores
        style: Citation style ("inline", "footnote", "harvard")
        
    Returns:
        Tuple of (formatted_answer, citations_block)
    """
    formatter = CitationFormatter()
    
    # Create citations block
    if style == "footnote":
        citations_text = "\n".join([
            formatter.format_footnote(
                i,
                c.document_name,
                c.page_number,
                c.excerpt
            )
            for i, c in enumerate(citations, 1)
        ])
    elif style == "harvard":
        citations_text = formatter.format_citation_block(citations, include_confidence)
    else:  # inline
        citations_text = formatter.format_citation_block(citations, include_confidence)
    
    return answer, citations_text

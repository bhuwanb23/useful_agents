"""
Learned Question model - stores Q&A patterns for reuse
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class QuestionType(str, Enum):
    """Types of questions we encounter"""
    PERSONAL_INFO = "personal_info"
    WORK_AUTH = "work_authorization"
    SALARY = "salary"
    YEARS_EXPERIENCE = "years_experience"
    SKILL_EXPERIENCE = "skill_experience"
    AVAILABILITY = "availability"
    MOTIVATION = "motivation"
    BEHAVIORAL = "behavioral"
    YES_NO = "yes_no"
    DROPDOWN = "dropdown"
    CUSTOM = "custom"


class AnswerStrategy(str, Enum):
    """How to answer this question"""
    AUTO = "auto"                  # Direct from profile
    CALCULATED = "calculated"      # Calculate from data
    AI_REASONING = "ai_reasoning"  # AI extracts from resume
    AI_GENERATE = "ai_generate"    # AI generates custom answer
    MANUAL = "manual"              # User provides answer
    LEARNED = "learned"            # Use previously learned answer


class LearnedQuestion(BaseModel):
    """
    A question we've encountered and know how to answer
    """
    
    # Question identification
    question_id: str = Field(default_factory=lambda: f"q_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    question_text: str
    normalized_question: str  # Simplified version for matching
    question_type: QuestionType
    
    # Answer details
    answer_strategy: AnswerStrategy
    answer_value: Optional[str] = None
    answer_source: Optional[str] = None  # e.g., "user_profile.personal_info.email"
    
    # For AI-generated answers
    ai_prompt_template: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_reasoning: Optional[str] = None
    
    # For calculated answers
    calculation_formula: Optional[str] = None
    
    # Metadata
    first_encountered: datetime = Field(default_factory=datetime.now)
    last_encountered: datetime = Field(default_factory=datetime.now)
    encountered_count: int = 1
    
    # Reusability
    always_same_answer: bool = True  # False if answer varies per job/company
    requires_customization: bool = False
    user_confirmed: bool = False  # Has user verified this answer?
    
    # Matching patterns
    similar_questions: List[str] = []  # Other phrasings of same question
    keywords: List[str] = []  # Keywords for matching
    
    # Success tracking
    successfully_submitted: int = 0
    failed_submissions: int = 0
    
    def update_encounter(self):
        """Update encounter statistics"""
        self.encountered_count += 1
        self.last_encountered = datetime.now()
    
    def mark_successful(self):
        """Mark this answer as successful"""
        self.successfully_submitted += 1
    
    def mark_failed(self):
        """Mark this answer as failed"""
        self.failed_submissions += 1
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.successfully_submitted + self.failed_submissions
        if total == 0:
            return 0.0
        return self.successfully_submitted / total
    
    @property
    def is_reliable(self) -> bool:
        """Is this answer reliable enough to auto-use?"""
        return (
            self.encountered_count >= 3 and
            self.success_rate >= 0.8 and
            self.user_confirmed
        )


class QuestionDatabase(BaseModel):
    """
    Database of all learned questions
    """
    
    questions: Dict[str, LearnedQuestion] = {}
    
    # Statistics
    total_questions: int = 0
    auto_answered: int = 0
    ai_answered: int = 0
    manually_answered: int = 0
    
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def add_question(self, question: LearnedQuestion):
        """Add or update a question"""
        self.questions[question.question_id] = question
        self.total_questions = len(self.questions)
        self.last_updated = datetime.now()
    
    def find_similar_question(self, question_text: str) -> Optional[LearnedQuestion]:
        """
        Find a similar question we've seen before
        """
        normalized = question_text.lower().strip()
        
        # First try exact match on normalized
        for q in self.questions.values():
            if q.normalized_question == normalized:
                return q
        
        # Then try keyword matching
        words = set(normalized.split())
        best_match = None
        best_score = 0
        
        for q in self.questions.values():
            # Check similar questions list
            if normalized in q.similar_questions:
                return q
            
            # Calculate word overlap
            q_words = set(q.normalized_question.split())
            overlap = len(words & q_words)
            score = overlap / len(words) if words else 0
            
            if score > best_score and score > 0.7:  # 70% overlap
                best_score = score
                best_match = q
        
        return best_match
    
    def get_by_type(self, question_type: QuestionType) -> List[LearnedQuestion]:
        """Get all questions of a specific type"""
        return [
            q for q in self.questions.values()
            if q.question_type == question_type
        ]
    
    def get_automation_stats(self) -> Dict:
        """Get automation statistics"""
        if self.total_questions == 0:
            return {"automation_rate": 0.0}
        
        return {
            "total_questions": self.total_questions,
            "auto_answered": self.auto_answered,
            "ai_answered": self.ai_answered,
            "manually_answered": self.manually_answered,
            "automation_rate": (self.auto_answered + self.ai_answered) / self.total_questions
        }
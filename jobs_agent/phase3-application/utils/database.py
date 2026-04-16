"""
Database operations for applications and learned questions
"""

import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json

from models.application import Application, ApplicationEvent, ApplicationStatus
from models.learned_question import LearnedQuestion, QuestionDatabase


class Database:
    """
    Handles all database operations
    """
    
    def __init__(self, db_path: str = "data/applications.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        
        cursor = self.conn.cursor()
        
        # Applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                application_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                job_url TEXT NOT NULL,
                match_score REAL,
                grade TEXT,
                
                application_method TEXT,
                application_url TEXT,
                
                status TEXT DEFAULT 'prepared',
                applied_date TIMESTAMP,
                last_updated TIMESTAMP,
                
                cover_letter_text TEXT,
                cover_letter_path TEXT,
                resume_used TEXT,
                
                submission_time_seconds REAL,
                submission_screenshot_path TEXT,
                
                confirmation_email_received BOOLEAN DEFAULT 0,
                confirmation_code TEXT,
                interview_date TIMESTAMP,
                
                user_notes TEXT,
                error_log TEXT,
                
                preparation_time_seconds REAL,
                review_time_seconds REAL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Screening questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screening_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT NOT NULL,
                question_text TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                answer_strategy TEXT,
                confidence REAL DEFAULT 1.0,
                was_edited BOOLEAN DEFAULT 0,
                FOREIGN KEY (application_id) REFERENCES applications(application_id)
            )
        """)
        
        # Application events (audit log)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS application_events (
                event_id TEXT PRIMARY KEY,
                application_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (application_id) REFERENCES applications(application_id)
            )
        """)
        
        # Learned questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_questions (
                question_id TEXT PRIMARY KEY,
                question_text TEXT NOT NULL,
                normalized_question TEXT NOT NULL,
                question_type TEXT,
                
                answer_strategy TEXT,
                answer_value TEXT,
                answer_source TEXT,
                
                ai_prompt_template TEXT,
                ai_confidence REAL,
                ai_reasoning TEXT,
                
                calculation_formula TEXT,
                
                first_encountered TIMESTAMP,
                last_encountered TIMESTAMP,
                encountered_count INTEGER DEFAULT 1,
                
                always_same_answer BOOLEAN DEFAULT 1,
                requires_customization BOOLEAN DEFAULT 0,
                user_confirmed BOOLEAN DEFAULT 0,
                
                similar_questions TEXT,
                keywords TEXT,
                
                successfully_submitted INTEGER DEFAULT 0,
                failed_submissions INTEGER DEFAULT 0
            )
        """)
        
        # Statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                applications_prepared INTEGER DEFAULT 0,
                applications_submitted INTEGER DEFAULT 0,
                applications_reviewed INTEGER DEFAULT 0,
                applications_skipped INTEGER DEFAULT 0,
                errors_encountered INTEGER DEFAULT 0,
                avg_submission_time_seconds REAL,
                platforms_used TEXT
            )
        """)
        
        # Rate limiting table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                platform TEXT,
                date DATE,
                applications_count INTEGER DEFAULT 0,
                last_application_time TIMESTAMP,
                PRIMARY KEY (platform, date)
            )
        """)
        
        self.conn.commit()
    
    # ===== APPLICATION OPERATIONS =====
    
    def save_application(self, app: Application):
        """Save or update an application"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO applications VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            app.application_id,
            app.job_id,
            app.company,
            app.title,
            str(app.job_url),
            app.match_score,
            app.grade,
            app.application_method.value,
            str(app.application_url) if app.application_url else None,
            app.status.value,
            app.applied_date.isoformat() if app.applied_date else None,
            app.last_updated.isoformat(),
            app.cover_letter_text,
            app.cover_letter_path,
            app.resume_used,
            app.submission_time_seconds,
            app.submission_screenshot_path,
            app.confirmation_email_received,
            app.confirmation_code,
            app.interview_date.isoformat() if app.interview_date else None,
            app.user_notes,
            app.error_log,
            app.preparation_time_seconds,
            app.review_time_seconds,
            datetime.now().isoformat()
        ))
        
        # Save screening questions
        for sq in app.screening_questions:
            cursor.execute("""
                INSERT INTO screening_questions 
                (application_id, question_text, answer_text, answer_strategy, confidence, was_edited)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                app.application_id,
                sq.question_text,
                sq.answer_text,
                sq.answer_strategy,
                sq.confidence,
                sq.was_edited
            ))
        
        self.conn.commit()
    
    def get_application(self, application_id: str) -> Optional[Application]:
        """Get application by ID"""
        
        cursor = self.conn.cursor()
        row = cursor.execute(
            "SELECT * FROM applications WHERE application_id = ?",
            (application_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return self._row_to_application(row)
    
    def get_applications_by_status(self, status: ApplicationStatus) -> List[Application]:
        """Get all applications with a specific status"""
        
        cursor = self.conn.cursor()
        rows = cursor.execute(
            "SELECT * FROM applications WHERE status = ? ORDER BY last_updated DESC",
            (status.value,)
        ).fetchall()
        
        return [self._row_to_application(row) for row in rows]
    
    def get_recent_applications(self, limit: int = 50) -> List[Application]:
        """Get recent applications"""
        
        cursor = self.conn.cursor()
        rows = cursor.execute(
            "SELECT * FROM applications ORDER BY last_updated DESC LIMIT ?",
            (limit,)
        ).fetchall()
        
        return [self._row_to_application(row) for row in rows]
    
    def _row_to_application(self, row) -> Application:
        """Convert DB row to Application object"""
        
        # This is simplified - you'd need to handle all fields properly
        return Application(
            application_id=row['application_id'],
            job_id=row['job_id'],
            company=row['company'],
            title=row['title'],
            job_url=row['job_url'],
            match_score=row['match_score'],
            grade=row['grade'],
            application_method=row['application_method'],
            status=row['status']
        )
    
    # ===== LEARNED QUESTIONS OPERATIONS =====
    
    def save_learned_question(self, question: LearnedQuestion):
        """Save or update a learned question"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO learned_questions VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            question.question_id,
            question.question_text,
            question.normalized_question,
            question.question_type.value,
            question.answer_strategy.value,
            question.answer_value,
            question.answer_source,
            question.ai_prompt_template,
            question.ai_confidence,
            question.ai_reasoning,
            question.calculation_formula,
            question.first_encountered.isoformat(),
            question.last_encountered.isoformat(),
            question.encountered_count,
            question.always_same_answer,
            question.requires_customization,
            question.user_confirmed,
            json.dumps(question.similar_questions),
            json.dumps(question.keywords),
            question.successfully_submitted,
            question.failed_submissions
        ))
        
        self.conn.commit()
    
    def get_learned_question(self, question_id: str) -> Optional[LearnedQuestion]:
        """Get learned question by ID"""
        
        cursor = self.conn.cursor()
        row = cursor.execute(
            "SELECT * FROM learned_questions WHERE question_id = ?",
            (question_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return self._row_to_learned_question(row)
    
    def search_similar_questions(self, question_text: str) -> List[LearnedQuestion]:
        """Search for similar questions"""
        
        normalized = question_text.lower().strip()
        
        cursor = self.conn.cursor()
        rows = cursor.execute("""
            SELECT * FROM learned_questions 
            WHERE normalized_question LIKE ? 
            OR question_text LIKE ?
            ORDER BY encountered_count DESC
            LIMIT 10
        """, (f"%{normalized}%", f"%{normalized}%")).fetchall()
        
        return [self._row_to_learned_question(row) for row in rows]
    
    def _row_to_learned_question(self, row) -> LearnedQuestion:
        """Convert DB row to LearnedQuestion object"""
        
        # This is simplified
        return LearnedQuestion(
            question_id=row['question_id'],
            question_text=row['question_text'],
            normalized_question=row['normalized_question'],
            question_type=row['question_type'],
            answer_strategy=row['answer_strategy'],
            answer_value=row['answer_value']
        )
    
    # ===== STATISTICS =====
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get application statistics"""
        
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total applications
        stats['total_applications'] = cursor.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()[0]
        
        # By status
        for status in ApplicationStatus:
            count = cursor.execute(
                "SELECT COUNT(*) FROM applications WHERE status = ?",
                (status.value,)
            ).fetchone()[0]
            stats[f'status_{status.value}'] = count
        
        # Response rate
        submitted = stats.get('status_submitted', 0) + stats.get('status_confirmed', 0)
        responded = stats.get('status_interview', 0) + stats.get('status_offer', 0) + stats.get('status_rejected', 0)
        stats['response_rate'] = (responded / submitted * 100) if submitted > 0 else 0
        
        # Average scores
        avg_score = cursor.execute(
            "SELECT AVG(match_score) FROM applications"
        ).fetchone()[0]
        stats['avg_match_score'] = avg_score or 0
        
        return stats
    
    def close(self):
        """Close database connection"""
        self.conn.close()
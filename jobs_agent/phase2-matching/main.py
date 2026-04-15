# phase2-matching/main.py
import sys
import os
from pathlib import Path

# Add parent directory to path to import from phase1
sys.path.insert(0, str(Path(__file__).parent.parent / 'phase1-scraping'))

import sqlite3
from typing import List, Dict, Any
import json
from datetime import datetime
from tqdm import tqdm
import argparse

# Phase 1 imports (optional - only needed if using phase1 settings)
try:
    from config.settings import settings as phase1_settings
except ImportError:
    # Settings not available, will use environment variables directly
    phase1_settings = None

# Phase 2 imports
from config.scoring_config import SCORING_CONFIG
from models.scored_jobs import ScoredJob, ScoreBreakdown, MatchExplanation
from scorers.hybrid_scorer import HybridScorer
from utils.embedding_cache import EmbeddingCache
from utils.explainer import MatchExplainer

class JobMatchingSystem:
    """
    Main system for matching and scoring jobs
    """
    
    def __init__(
        self, 
        resume_analysis_path: str,
        preferences_path: str,
        jobs_db_path: str,
        use_ai: bool = True
    ):
        print("=" * 70)
        print(" " * 20 + "🎯 JOB MATCHING SYSTEM 🎯")
        print("=" * 70)
        
        # Load resume analysis from Phase 1
        print("\n📋 Loading resume analysis...")
        with open(resume_analysis_path, 'r') as f:
            self.resume_analysis = json.load(f)
        print(f"   ✓ Resume analyzed: {len(self.resume_analysis.get('skills', []))} skills identified")
        
        # Load preferences
        print("\n⚙️  Loading preferences...")
        with open(preferences_path, 'r') as f:
            self.preferences = json.load(f)
        print(f"   ✓ Preferences loaded")
        
        # Connect to jobs database
        print("\n💾 Connecting to jobs database...")
        self.db_path = jobs_db_path
        self.conn = sqlite3.connect(jobs_db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        job_count = self.conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        print(f"   ✓ Found {job_count} jobs in database")
        
        # Initialize embedding cache
        print("\n🧠 Initializing AI components...")
        self.embedding_cache = EmbeddingCache(
            cache_file="data/embeddings_cache.pkl",
            model_name=SCORING_CONFIG['embedding_model']
        )
        
        # Initialize scorer
        self.scorer = HybridScorer(
            resume_analysis=self.resume_analysis,
            preferences=self.preferences,
            api_key=os.getenv('GOOGLE_API_KEY'),
            embedding_cache=self.embedding_cache,
            use_ai=use_ai
        )
        
        # Initialize explainer
        self.explainer = MatchExplainer()
        
        # Create resume text for semantic matching
        self.resume_text = self._create_resume_text()
        
        print("   ✓ System ready!")
    
    def _create_resume_text(self) -> str:
        """Create text representation of resume"""
        parts = []
        
        if self.resume_analysis.get('job_titles'):
            parts.append("Job Titles: " + ", ".join(self.resume_analysis['job_titles']))
        
        if self.resume_analysis.get('skills'):
            parts.append("Skills: " + ", ".join(self.resume_analysis['skills']))
        
        if self.resume_analysis.get('industries'):
            parts.append("Industries: " + ", ".join(self.resume_analysis['industries']))
        
        return "\n".join(parts)
    
    def match_all_jobs(self, limit: int = None) -> List[ScoredJob]:
        """
        Match and score all jobs from database
        """
        print("\n" + "=" * 70)
        print("🔍 MATCHING JOBS")
        print("=" * 70)
        
        # Fetch jobs from database
        query = "SELECT * FROM jobs"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query)
        jobs = [dict(row) for row in cursor.fetchall()]
        
        print(f"\n📊 Processing {len(jobs)} jobs...")
        
        scored_jobs = []
        
        # Process jobs with progress bar
        for job in tqdm(jobs, desc="Scoring jobs"):
            try:
                scored_job = self._score_single_job(job)
                
                # Only keep jobs above minimum threshold
                if scored_job.total_score >= SCORING_CONFIG['minimum_score_to_save']:
                    scored_jobs.append(scored_job)
            
            except Exception as e:
                print(f"\n⚠️  Error scoring job {job.get('job_id')}: {e}")
                continue
        
        # Sort by score (highest first)
        scored_jobs.sort(key=lambda x: x.total_score, reverse=True)
        
        print(f"\n✅ Scored {len(scored_jobs)} jobs (filtered from {len(jobs)})")
        
        # Add AI enrichment for top jobs
        if SCORING_CONFIG['use_ai_enrichment']:
            self._enrich_top_jobs(scored_jobs[:SCORING_CONFIG['top_n_for_ai_analysis']])
        
        # Save embedding cache
        self.embedding_cache.save()
        
        return scored_jobs
    
    def _score_single_job(self, job: Dict[str, Any]) -> ScoredJob:
        """
        Score a single job
        """
        # Get scores
        breakdown, ai_explanation, missing_skills = self.scorer.score_with_explanation(
            job=job,
            resume_text=self.resume_text
        )
        
        # Calculate total
        total_score = self.scorer.calculate_total(breakdown)
        
        # Get grade
        grade = self.explainer.score_to_grade(total_score)
        
        # Create explanation
        explanation = self.explainer.create_explanation(
            breakdown=breakdown,
            total_score=total_score,
            ai_summary=ai_explanation,
            missing_skills=missing_skills
        )
        
        # Create ScoredJob
        scored_job = ScoredJob(
            job_id=job['job_id'],
            title=job['title'],
            company=job['company'],
            location=job.get('location'),
            is_remote=bool(job.get('is_remote', False)),
            job_url=job['job_url'],
            description=job.get('description', ''),
            salary_min=job.get('salary_min'),
            salary_max=job.get('salary_max'),
            posted_date=job.get('posted_date'),
            source=job.get('source', 'unknown'),
            total_score=round(total_score, 2),
            grade=grade,
            breakdown=breakdown,
            explanation=explanation
        )
        
        return scored_job
    
    def _enrich_top_jobs(self, top_jobs: List[ScoredJob]):
        """
        Add detailed AI analysis for top jobs
        """
        if not top_jobs:
            return
        
        print(f"\n🤖 Enriching top {len(top_jobs)} jobs with AI insights...")
        
        for job in tqdm(top_jobs, desc="AI enrichment"):
            try:
                # Regenerate with more detailed AI analysis
                if not job.explanation.ai_summary:
                    job_dict = {
                        'job_id': job.job_id,
                        'title': job.title,
                        'company': job.company,
                        'description': job.description
                    }
                    
                    ai_explanation = self.scorer.ai_scorer.generate_explanation(
                        job_dict, 
                        job.total_score
                    )
                    
                    job.explanation.ai_summary = ai_explanation
            
            except Exception as e:
                print(f"\n⚠️  Error enriching job {job.job_id}: {e}")
    
    def save_results(self, scored_jobs: List[ScoredJob], output_file: str):
        """
        Save scored jobs to JSON
        """
        print(f"\n💾 Saving results to {output_file}...")
        
        results = []
        for job in scored_jobs:
            results.append(job.model_dump(mode='json'))
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"   ✓ Saved {len(results)} scored jobs")
    
    def save_to_database(self, scored_jobs: List[ScoredJob]):
        """
        Save scored jobs to new table in database
        """
        print("\n💾 Saving to database...")
        
        # Create scored_jobs table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scored_jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                total_score REAL,
                grade TEXT,
                skills_score REAL,
                experience_score REAL,
                title_score REAL,
                semantic_score REAL,
                salary_score REAL,
                location_score REAL,
                culture_score REAL,
                growth_score REAL,
                recommendation TEXT,
                strengths TEXT,
                concerns TEXT,
                missing_skills TEXT,
                ai_summary TEXT,
                scored_at TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
        """)
        
        # Insert scored jobs
        for job in scored_jobs:
            self.conn.execute("""
                INSERT OR REPLACE INTO scored_jobs VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                job.job_id,
                job.title,
                job.company,
                job.total_score,
                job.grade,
                job.breakdown.skills_match,
                job.breakdown.experience_match,
                job.breakdown.title_match,
                job.breakdown.semantic_similarity,
                job.breakdown.salary_match,
                job.breakdown.location_match,
                job.breakdown.culture_fit,
                job.breakdown.growth_potential,
                job.explanation.recommendation,
                json.dumps(job.explanation.strengths),
                json.dumps(job.explanation.concerns),
                json.dumps(job.explanation.missing_skills),
                job.explanation.ai_summary,
                job.scored_at.isoformat()
            ))
        
        self.conn.commit()
        print(f"   ✓ Saved {len(scored_jobs)} jobs to database")
    
    def print_summary(self, scored_jobs: List[ScoredJob]):
        """
        Print summary statistics
        """
        print("\n" + "=" * 70)
        print("📊 MATCHING SUMMARY")
        print("=" * 70)
        
        total = len(scored_jobs)
        
        if total == 0:
            print("No jobs matched criteria.")
            return
        
        # Grade distribution
        from collections import Counter
        grade_dist = Counter(job.grade for job in scored_jobs)
        
        print(f"\n📈 Score Distribution:")
        print(f"   Total Jobs Scored: {total}")
        print(f"   Average Score: {sum(j.total_score for j in scored_jobs) / total:.1f}")
        print(f"   Highest Score: {max(j.total_score for j in scored_jobs):.1f}")
        print(f"\n   Grade Breakdown:")
        for grade in ['A+', 'A', 'B', 'C', 'D', 'F']:
            count = grade_dist.get(grade, 0)
            pct = (count / total * 100) if total > 0 else 0
            print(f"      {grade}: {count:3d} jobs ({pct:5.1f}%)")
        
        # Top recommendations
        print(f"\n🌟 Top 10 Matches:")
        for i, job in enumerate(scored_jobs[:10], 1):
            print(f"\n   {i}. [{job.grade}] {job.title} at {job.company}")
            print(f"      Score: {job.total_score:.1f}/100")
            print(f"      {job.explanation.recommendation}")
            if job.explanation.strengths:
                print(f"      💪 {job.explanation.strengths[0]}")
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(description='Job Matching System')
    parser.add_argument('--resume', default='../phase1-scraping/data/resume_analysis.json',
                       help='Path to resume analysis JSON')
    parser.add_argument('--preferences', default='data/preferences.json',
                       help='Path to preferences JSON')
    parser.add_argument('--jobs-db', default='../phase1-scraping/data/jobs.db',
                       help='Path to jobs database')
    parser.add_argument('--output', default='data/scored_jobs.json',
                       help='Output file for scored jobs')
    parser.add_argument('--limit', type=int, help='Limit number of jobs to process')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI scoring')
    
    args = parser.parse_args()
    
    # Create matching system
    matcher = JobMatchingSystem(
        resume_analysis_path=args.resume,
        preferences_path=args.preferences,
        jobs_db_path=args.jobs_db,
        use_ai=not args.no_ai
    )
    
    try:
        # Match all jobs
        scored_jobs = matcher.match_all_jobs(limit=args.limit)
        
        # Save results
        matcher.save_results(scored_jobs, args.output)
        matcher.save_to_database(scored_jobs)
        
        # Print summary
        matcher.print_summary(scored_jobs)
        
    finally:
        matcher.close()
    
    print("\n✅ Matching complete!")


if __name__ == "__main__":
    main()
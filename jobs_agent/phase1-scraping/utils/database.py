# utils/database.py
from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from models.job import Job
from typing import List
from datetime import datetime

Base = declarative_base()

class JobDB(Base):
    __tablename__ = 'jobs'
    
    job_id = Column(String, primary_key=True)
    source = Column(String)
    title = Column(String)
    company = Column(String)
    location = Column(String, nullable=True)
    is_remote = Column(Boolean, default=False)
    description = Column(Text)
    job_type = Column(String, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    job_url = Column(String)
    posted_date = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.now)
    match_score = Column(Float, nullable=True)

class Database:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def save_jobs(self, jobs: List[Job]):
        """Save jobs to database"""
        for job in jobs:
            existing = self.session.query(JobDB).filter_by(job_id=job.job_id).first()
            if existing:
                continue  # Skip duplicates
            
            db_job = JobDB(
                job_id=job.job_id,
                source=job.source,
                title=job.title,
                company=job.company,
                location=job.location,
                is_remote=job.is_remote,
                description=job.description,
                job_type=job.job_type.value if job.job_type else None,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                job_url=str(job.job_url),
                posted_date=job.posted_date,
                scraped_at=job.scraped_at,
                match_score=job.match_score
            )
            self.session.add(db_job)
        
        self.session.commit()
        print(f"✓ Saved {len(jobs)} jobs to database")
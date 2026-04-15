# models/__init__.py
from .job import Job, JobType
from .resume import ResumeAnalysis
from .preferences import JobPreferences

__all__ = ['Job', 'JobType', 'ResumeAnalysis', 'JobPreferences']
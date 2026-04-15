# phase2-matching/quick_start.py
"""
Quick start script - runs everything
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("🚀 Quick Start: Job Matching System\n")
    
    # Check if preferences exist
    prefs_file = Path('data/preferences.json')
    if not prefs_file.exists():
        print("📋 Step 1: Create preferences")
        subprocess.run([sys.executable, 'create_preferences.py'])
    else:
        print("✓ Preferences file exists")
    
    # Check if resume analysis exists
    resume_analysis = Path('../phase1-scraping/data/resume_analysis.json')
    if not resume_analysis.exists():
        print("\n⚠️  Resume analysis not found!")
        print("   Please run Phase 1 first to analyze your resume.")
        return
    
    print("\n✓ Resume analysis found")
    
    # Check if jobs database exists
    jobs_db = Path('../phase1-scraping/data/jobs.db')
    if not jobs_db.exists():
        print("\n⚠️  Jobs database not found!")
        print("   Please run Phase 1 first to scrape jobs.")
        return
    
    print("✓ Jobs database found")
    
    # Run matching
    print("\n🎯 Step 2: Running job matching...")
    subprocess.run([sys.executable, 'main.py'])
    
    print("\n✅ Complete! Check data/scored_jobs.json for results.")


if __name__ == "__main__":
    main()
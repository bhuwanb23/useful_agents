import sys
sys.path.insert(0, '.')

# Quick integration test
from main import JobMatchingSystem

print("\n" + "="*70)
print("Testing Phase 2 with Transformed Resume Data")
print("="*70)

try:
    system = JobMatchingSystem(
        resume_analysis_path='../phase1-scraping/data/resume_analysis.json',
        preferences_path='data/preferences.json',
        jobs_db_path='../phase1-scraping/data/jobs.db',
        use_ai=False
    )
    
    print("\n✅ SUCCESS! Phase 2 initialized with transformed resume data!")
    print(f"   - Loaded {len(system.resume_analysis['skills'])} skills")
    print(f"   - Found {system.conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]} jobs in database")
    print(f"   - System ready for matching!")
    
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

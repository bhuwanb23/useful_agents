import sys
from pathlib import Path

# Set up paths
phase2_dir = Path(__file__).parent
sys.path.insert(0, str(phase2_dir))

import json

print("\n" + "="*70)
print("PHASE 1 + PHASE 2 INTEGRATION TEST")
print("="*70)

# Test 1: Load transformed resume
print("\n[Test 1] Loading transformed resume analysis...")
try:
    with open('../phase1-scraping/data/resume_analysis.json', 'r') as f:
        resume = json.load(f)
    print(f"  ✓ Loaded successfully")
    print(f"  - Skills: {len(resume['skills'])} (type: {type(resume['skills']).__name__})")
    print(f"  - Job titles: {len(resume['job_titles'])}")
    print(f"  - Experience: {resume['experience_years']} years")
    print(f"  - Seniority: {resume['seniority']}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 2: Load preferences
print("\n[Test 2] Loading preferences...")
try:
    with open('data/preferences.json', 'r') as f:
        prefs = json.load(f)
    print(f"  ✓ Loaded successfully")
    print(f"  - Remote only: {prefs['remote_only']}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 3: Check jobs database
print("\n[Test 3] Checking jobs database...")
try:
    import sqlite3
    conn = sqlite3.connect('../phase1-scraping/data/jobs.db')
    count = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    print(f"  ✓ Database accessible")
    print(f"  - Total jobs: {count}")
    conn.close()
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✅ ALL CHECKS PASSED! Data is ready for Phase 2 matching")
print("="*70)

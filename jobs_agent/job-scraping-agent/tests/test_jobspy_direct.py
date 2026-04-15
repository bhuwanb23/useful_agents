#!/usr/bin/env python3
"""
Test JobSpy scraper directly (not pytest)
"""
import warnings
warnings.filterwarnings('ignore')

from jobspy import scrape_jobs

print("=" * 70)
print("Testing JobSpy Scraper Directly")
print("=" * 70)

# Test 1: Just Indeed
print("\n[Test 1] Scraping with Indeed only...")
try:
    jobs = scrape_jobs(
        site_name=['indeed'],
        search_term='Software Developer',
        results_wanted=5,
        country_indeed='USA'
    )
    print(f"✅ SUCCESS! Found {len(jobs)} jobs from Indeed")
    if len(jobs) > 0:
        print("\nSample jobs:")
        print(jobs[['title', 'company', 'site', 'location']].head(3))
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 2: Indeed + LinkedIn
print("\n[Test 2] Scraping with Indeed + LinkedIn...")
try:
    jobs = scrape_jobs(
        site_name=['indeed', 'linkedin'],
        search_term='Software Developer',
        results_wanted=5,
        country_indeed='USA'
    )
    print(f"✅ SUCCESS! Found {len(jobs)} jobs")
    if len(jobs) > 0:
        print(f"\nJobs by site:")
        print(jobs['site'].value_counts())
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 3: All supported sites
print("\n[Test 3] Scraping with all supported sites (indeed, linkedin, zip_recruiter)...")
try:
    jobs = scrape_jobs(
        site_name=['indeed', 'linkedin', 'zip_recruiter'],
        search_term='Software Developer',
        results_wanted=10,
        country_indeed='USA'
    )
    print(f"✅ SUCCESS! Found {len(jobs)} jobs")
    if len(jobs) > 0:
        print(f"\nJobs by site:")
        print(jobs['site'].value_counts())
        print(f"\nTop 5 jobs:")
        print(jobs[['title', 'company', 'site', 'location']].head(5))
except Exception as e:
    print(f"❌ FAILED: {e}")

print("\n" + "=" * 70)
print("Test Complete!")
print("=" * 70)

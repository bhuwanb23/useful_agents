# phase2-matching/create_preferences.py
"""
Helper script to create preferences.json
Run this once to set your job search preferences
"""

import json
from pathlib import Path

def create_preferences():
    """
    Interactive script to create preferences
    """
    print("=" * 70)
    print(" " * 15 + "🎯 JOB SEARCH PREFERENCES SETUP 🎯")
    print("=" * 70)
    
    preferences = {}
    
    # Remote preference
    print("\n📍 Location Preferences:")
    remote_only = input("   Remote only? (y/n): ").lower() == 'y'
    preferences['remote_only'] = remote_only
    
    if not remote_only:
        locations = input("   Preferred locations (comma-separated): ").split(',')
        preferences['locations'] = [loc.strip() for loc in locations if loc.strip()]
    else:
        preferences['locations'] = []
    
    # Salary
    print("\n💰 Salary Preferences:")
    min_salary = input("   Minimum salary (or press Enter to skip): ")
    if min_salary:
        preferences['min_salary'] = float(min_salary)
    else:
        preferences['min_salary'] = None
    
    # Job types
    print("\n💼 Job Type:")
    print("   1. Full-time")
    print("   2. Part-time")
    print("   3. Contract")
    print("   4. All")
    job_type_choice = input("   Choose (1-4): ")
    
    job_type_map = {
        '1': ['full-time'],
        '2': ['part-time'],
        '3': ['contract'],
        '4': ['full-time', 'part-time', 'contract']
    }
    preferences['job_types'] = job_type_map.get(job_type_choice, ['full-time'])
    
    # Exclusions
    print("\n🚫 Exclusions:")
    excluded_companies = input("   Companies to exclude (comma-separated, or press Enter): ")
    if excluded_companies:
        preferences['excluded_companies'] = [c.strip() for c in excluded_companies.split(',')]
    else:
        preferences['excluded_companies'] = []
    
    excluded_keywords = input("   Keywords to exclude (comma-separated, or press Enter): ")
    if excluded_keywords:
        preferences['excluded_keywords'] = [k.strip() for k in excluded_keywords.split(',')]
    else:
        preferences['excluded_keywords'] = []
    
    # Save
    output_path = Path('data/preferences.json')
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(preferences, f, indent=2)
    
    print(f"\n✅ Preferences saved to {output_path}")
    print("\nYour preferences:")
    print(json.dumps(preferences, indent=2))


if __name__ == "__main__":
    create_preferences()
# main.py
import asyncio
from agents.ai_analyzer import AIAnalyzer
from agents.orchestrator import JobScrapingOrchestrator
from models.preferences import JobPreferences
from utils.database import Database
import json

async def main():
    """
    Main application flow
    """
    
    print("=" * 70)
    print(" " * 15 + "🤖 AI JOB SCRAPING AGENT 🤖")
    print("=" * 70)
    
    # Step 1: Setup
    print("\n📋 Step 1: Loading configuration...")
    
    resume_path = "data/resume.md"
    
    preferences = JobPreferences(
        remote_only=True,
        locations=["United States"],
        countries=["USA"],
        job_types=["full-time"],
        min_salary=80000,
        results_per_source=30,
        excluded_keywords=["unpaid", "volunteer", "intern"]
    )
    
    career_urls = [
        "https://boards.greenhouse.io/openai",
        "https://jobs.lever.co/anthropic",
        # Add more company career pages
    ]
    
    # Step 2: AI Analysis
    print("\n🧠 Step 2: Analyzing resume with AI...")
    analyzer = AIAnalyzer()
    resume_analysis = analyzer.analyze_resume(resume_path)
    
    print(f"   ✓ Identified {len(resume_analysis.job_titles)} target job titles")
    print(f"   ✓ Extracted {len(resume_analysis.skills)} skills")
    print(f"   ✓ Seniority level: {resume_analysis.seniority}")
    
    # Step 3: Generate search queries
    print("\n🔎 Step 3: Generating search queries...")
    search_queries = analyzer.generate_search_queries(resume_analysis, preferences)
    print(f"   ✓ Generated {len(search_queries)} optimized queries")
    print(f"   Top 5 queries:")
    for query in search_queries[:5]:
        print(f"      - {query}")
    
    # Step 4: Scrape jobs
    print("\n🕷️  Step 4: Scraping jobs from all sources...")
    orchestrator = JobScrapingOrchestrator()
    
    jobs = await orchestrator.scrape_all_sources(
        search_queries=search_queries,
        resume_analysis=resume_analysis,
        preferences=preferences,
        career_urls=career_urls
    )
    
    # Step 5: Save results
    print("\n💾 Step 5: Saving results...")
    db = Database()
    db.save_jobs(jobs)
    
    # Export to JSON
    with open("data/scraped_jobs.json", "w") as f:
        json.dump([job.model_dump(mode='json') for job in jobs], f, indent=2, default=str)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SCRAPING SUMMARY")
    print("=" * 70)
    print(f"Total jobs found: {len(jobs)}")
    print(f"Remote jobs: {sum(1 for j in jobs if j.is_remote)}")
    print(f"Jobs with salary: {sum(1 for j in jobs if j.salary_min)}")
    
    # Top companies
    from collections import Counter
    companies = Counter(j.company for j in jobs)
    print(f"\nTop 10 companies:")
    for company, count in companies.most_common(10):
        print(f"   {company}: {count} jobs")
    
    print("\n✅ Scraping complete! Check data/scraped_jobs.json")

if __name__ == "__main__":
    asyncio.run(main())
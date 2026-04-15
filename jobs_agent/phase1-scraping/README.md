# 🤖 AI-Powered Job Scraping Agent

An intelligent job search automation tool that uses AI to analyze your resume, scrape jobs from multiple sources, and match you with the best opportunities.

## ✨ Features

- 🧠 **AI Resume Analysis** - Uses Google Gemini to extract skills, experience, and generate optimized search queries
- 🕷️ **Multi-Source Scraping** - Aggregates jobs from Indeed, LinkedIn, Glassdoor, ZipRecruiter via JobSpy and Apify
- 🏢 **Career Page Scraping** - Direct scraping from company career pages (Greenhouse, Lever, Workday)
- 🎯 **Smart Matching** - Scores jobs based on resume-job fit
- 🗂️ **Deduplication** - Removes duplicate listings across sources
- 💾 **Database Storage** - Saves all jobs to SQLite with full search capability
- 📊 **Analytics** - Track scraping statistics and job market insights

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google AI API Key (FREE from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/job-scraping-agent.git
cd job-scraping-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
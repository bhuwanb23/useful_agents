# JobSpy Scraper - Known Issues & Solutions

## Current Status

**JobSpy v1.1.13** has significant limitations due to anti-bot protection from job sites.

---

## Issues Found

### 1. **Glassdoor - KeyError: 'GLASSDOOR'** ❌
```
KeyError: 'GLASSDOOR'
```
**Cause:** Glassdoor enum not supported in JobSpy v1.1.13

**Solution:** Removed from SUPPORTED_SITES

---

### 2. **Google Jobs - KeyError: 'GOOGLE'** ❌
```
KeyError: 'GOOGLE'
```
**Cause:** Google Jobs enum not supported in JobSpy v1.1.13

**Solution:** Removed from SUPPORTED_SITES

---

### 3. **All Sites - HTTP 403 Blocked** ⚠️
```
IndeedException: bad response with status code: 403
ZipRecruiterException: bad response status code: 403
LinkedInException: bad response status code: 403
```
**Cause:** Job sites have anti-bot protection that blocks automated scraping

**Impact:** JobSpy cannot scrape jobs without proxies

---

## Current Configuration

```python
# Only these sites are configured (but all get 403 blocked)
SUPPORTED_SITES = ["indeed", "linkedin", "zip_recruiter"]
```

---

## Recommended Solutions

### **Option 1: Use Apify (RECOMMENDED)** ✅

Apify is already integrated and working perfectly!

**Advantages:**
- ✅ Has official partnerships with job sites
- ✅ Handles anti-bot protection automatically  
- ✅ Includes residential proxies
- ✅ More reliable data extraction
- ✅ Free tier: $5 credit/month

**Already Implemented:**
- Apify Indeed scraper (working)
- Proper error handling
- Data type validation

**Usage:**
```python
# Apify works great!
orchestrator = JobScrapingOrchestrator()
jobs = await orchestrator.scrape_all_sources(...)
```

---

### **Option 2: Add Proxy Support to JobSpy**

If you want to use JobSpy, you need proxies:

```python
jobs = scrape_jobs(
    site_name=["indeed", "linkedin"],
    search_term="Software Developer",
    results_wanted=20,
    country_indeed='USA',
    proxies=[
        "208.195.175.46:65095",
        "208.195.175.45:65095",
        "localhost"
    ]
)
```

**Where to get proxies:**
- **Free:** Limited, often blocked
- **Paid:** BrightData, Oxylabs, Smartproxy ($50-300/month)
- **Residential:** More expensive but less likely to be blocked

---

### **Option 3: Upgrade JobSpy Version**

Check if newer version has fixes:

```bash
pip install --upgrade python-jobspy
```

**Current version:** 1.1.13  
**Latest version:** Check on PyPI

---

## Architecture Recommendation

### **Best Practice: Multi-Source Strategy**

```
Primary Source: Apify (reliable, working)
    ↓ (fallback if Apify quota exceeded)
Secondary Source: Career Page APIs (Greenhouse, Lever)
    ↓ (additional jobs)
Tertiary Source: JobSpy (if proxies available)
```

### **Current Implementation:**

The job-scraping-agent already uses this strategy:

1. **Phase 1:** JobSpy (will fail without proxies - expected)
2. **Phase 2:** Apify (✅ working, primary source)
3. **Phase 3:** Career Pages (✅ working via HTTP APIs)

**Result:** You get jobs from Apify + Career Pages even if JobSpy fails!

---

## Error Messages Explained

### Good (Expected):
```
⚠️  JobSpy blocked for 'Software Developer' (anti-bot protection). Use Apify instead.
```
This is normal - the system continues to Apify which works.

### Bad (Shouldn't happen):
```
✗ JobSpy error for 'query': GLASSDOOR
✗ JobSpy error for 'query': GOOGLE
```
These are fixed - removed unsupported sites.

---

## Testing JobSpy

To test if JobSpy works (requires proxies):

```python
from jobspy import scrape_jobs

# Test with just Indeed
try:
    jobs = scrape_jobs(
        site_name=['indeed'],
        search_term='Software Developer',
        results_wanted=5,
        country_indeed='USA'
    )
    print(f"✓ Found {len(jobs)} jobs")
except Exception as e:
    print(f"✗ JobSpy blocked: {e}")
    print("→ Use Apify instead")
```

---

## Conclusion

**JobSpy Status:** ❌ Blocked without proxies  
**Apify Status:** ✅ Working perfectly  
**Career Pages:** ✅ Working via HTTP APIs  

**Recommendation:** Rely on Apify as primary source, Career Pages as secondary. JobSpy is optional bonus if you have proxies.

The system is designed to handle JobSpy failures gracefully and will still find jobs through other sources!

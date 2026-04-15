# phase2-matching/config/prompts.py

CULTURE_FIT_PROMPT = """
Analyze the cultural fit between this candidate and job.

Candidate Profile:
- Seniority: {seniority}
- Industries: {industries}
- Current Role: {current_role}

Job Description:
{job_description}

Company: {company}

Rate 0-5 how well the candidate would fit the company culture based on:
1. Company size/stage (startup vs enterprise)
2. Work style indicators (fast-paced, collaborative, etc.)
3. Tech stack modernity
4. Team structure hints

Return ONLY a number 0-5 (decimals ok).
"""

GROWTH_POTENTIAL_PROMPT = """
Analyze growth potential of this job for the candidate.

Candidate:
- Current Skills: {skills}
- Experience Level: {seniority}
- Career Goals: {job_titles}

Job Description:
{job_description}

Rate 0-5 the growth potential based on:
1. New skills they would learn
2. Increase in responsibility
3. Career advancement opportunity
4. Exposure to new technologies/domains

Return ONLY a number 0-5 (decimals ok).
"""

MATCH_EXPLANATION_PROMPT = """
Generate a brief explanation of why this job matches the candidate.

Resume Summary:
{resume_summary}

Job:
- Title: {title}
- Company: {company}
- Description: {description}

Match Score: {score}/100

In 2-3 sentences, explain:
1. Why this is a good fit (focus on specific skills/experience)
2. One potential growth opportunity

Be conversational and encouraging.
"""

MISSING_SKILLS_ANALYSIS_PROMPT = """
Identify key skills the candidate is missing for this role.

Candidate Skills: {candidate_skills}

Job Requirements:
{job_description}

List up to 5 most important missing skills.
Return as JSON array: ["skill1", "skill2", ...]
"""
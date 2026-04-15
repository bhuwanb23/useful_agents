# phase2-matching/config/scoring_config.py

# Scoring weights (must sum to 1.0)
SCORING_WEIGHTS = {
    'skills_match': 0.30,          # 30 points
    'experience_match': 0.15,      # 15 points
    'title_match': 0.15,           # 15 points
    'semantic_similarity': 0.15,   # 15 points
    'salary_match': 0.10,          # 10 points
    'location_match': 0.05,        # 5 points
    'culture_fit': 0.05,           # 5 points (AI)
    'growth_potential': 0.05       # 5 points (AI)
}

SCORING_CONFIG = {
    # Skill matching
    'min_skill_match_threshold': 0.20,  # At least 20% skills must match
    'fuzzy_match_threshold': 0.85,      # 85% similarity for fuzzy matching
    
    # Experience matching
    'experience_tolerance_years': 1,     # ±1 year is acceptable
    'overqualified_penalty': 2,          # Penalty if >2 years overqualified
    
    # Title matching
    'title_keyword_weight': 0.6,        # Weight for keyword matching
    'title_semantic_weight': 0.4,       # Weight for semantic matching
    
    # Salary matching
    'salary_negotiation_range': 0.10,   # 10% below is negotiable
    'salary_bonus_threshold': 0.20,     # 20% above = bonus points
    
    # Filtering thresholds
    'minimum_score_to_save': 40,        # Don't save jobs < 40 score
    'top_n_for_ai_analysis': 20,       # Only top 20 get deep AI analysis
    
    # AI settings
    'use_ai_enrichment': True,
    'ai_batch_size': 10,                # Process AI in batches of 10
    
    # Embedding model
    'embedding_model': 'all-MiniLM-L6-v2',  # Fast, free, local
}

# Grade mapping
GRADE_THRESHOLDS = {
    'A+': 85,  # Excellent match - Apply immediately
    'A':  75,  # Very good match - Definitely apply
    'B':  65,  # Good match - Worth applying
    'C':  55,  # Fair match - Consider applying
    'D':  45,  # Poor match - Probably skip
    'F':  0    # Bad match - Don't apply
}

# Recommendation mapping
RECOMMENDATIONS = {
    'A+': 'HIGHLY RECOMMENDED - Apply ASAP',
    'A':  'RECOMMENDED - Strong match',
    'B':  'GOOD FIT - Worth applying',
    'C':  'FAIR MATCH - Consider if interested',
    'D':  'WEAK MATCH - Apply only if desperate',
    'F':  'NOT RECOMMENDED - Poor fit'
}
"""
Prompts for ranking opportunities against candidate profile.
"""

RANKING_SYSTEM_PROMPT = """You are an expert career advisor specializing in matching speakers and thought leaders with speaking opportunities.

Your task is to analyze a candidate's profile and rank speaking opportunities based on how well they match the candidate's:
1. Expertise and knowledge areas
2. Experience level and credentials
3. Preferences (compensation, location, format)
4. Availability (checking for expired deadlines)

For each opportunity, provide:
- A match score (0.0 to 1.0)
- Key reasons why this opportunity is a good/bad fit
- Matching keywords between profile and opportunity

Be objective and accurate in your assessments."""


def get_ranking_user_prompt(profile_summary: str, opportunities_text: str, current_date: str) -> str:
    return f"""Please rank the following speaking opportunities for this candidate.

**CURRENT DATE:** {current_date}

**CANDIDATE PROFILE:**
{profile_summary}

**OPPORTUNITIES TO RANK:**
{opportunities_text}

**INSTRUCTIONS:**
1. Filter out any opportunities with expired application deadlines (before {current_date})
2. Score each valid opportunity from 0.0 to 1.0 based on match quality
3. Identify specific reasons for the match/mismatch
4. List matching keywords between profile and opportunity

**OUTPUT FORMAT:**
Return a JSON array with the following structure for each opportunity:
[
  {{
    "opportunity_id": "the opportunity id",
    "event_name": "event name",
    "match_score": 0.85,
    "relevance_score": 0.9,
    "preference_score": 0.8,
    "match_reasons": ["Reason 1", "Reason 2"],
    "matching_keywords": ["keyword1", "keyword2"],
    "is_expired": false,
    "days_until_deadline": 30
  }}
]

Sort the results by match_score in descending order (best matches first).
Return ONLY the JSON array, no additional text."""


PROFILE_EXTRACTION_PROMPT = """You are an expert at analyzing professional profiles and resumes.

Extract the following information from the provided text:
1. Name and professional title
2. Primary areas of expertise
3. Secondary/related expertise
4. Years of experience
5. Notable speaking experience
6. Key achievements and credentials
7. Education background
8. Publications or thought leadership

Be thorough but concise. Focus on information relevant to speaking opportunities."""


def get_profile_extraction_user_prompt(raw_text: str) -> str:
    return f"""Please analyze the following profile/resume text and extract key information.

**RAW TEXT:**
{raw_text}

**OUTPUT FORMAT:**
Return a JSON object with the following structure:
{{
  "name": "Full Name",
  "title": "Professional Title",
  "primary_expertise": ["Area 1", "Area 2"],
  "secondary_expertise": ["Area 3", "Area 4"],
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "years_of_experience": 10,
  "speaking_experience": "Description of speaking experience",
  "notable_talks": ["Talk 1", "Talk 2"],
  "notable_venues": ["Venue 1", "Venue 2"],
  "education": ["Degree 1", "Degree 2"],
  "certifications": ["Cert 1", "Cert 2"],
  "publications": ["Publication 1"],
  "awards": ["Award 1"],
  "bio": "A brief professional bio (2-3 sentences)",
  "summary": "A one-paragraph summary of the candidate's profile"
}}

Return ONLY the JSON object, no additional text."""
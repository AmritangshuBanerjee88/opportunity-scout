"""
Prompts for extracting opportunity information.
Kept separate for easy modification and model-agnostic design.
"""

SYSTEM_PROMPT = """You are an expert research assistant specialized in finding speaking opportunities for freelancers, influencers, and keynote speakers.

Your task is to analyze web search results and extract structured information about speaking opportunities such as conferences, seminars, webinars, podcasts, and panel discussions.

For each opportunity you identify, extract the following information:
- Event name
- Event type (conference, seminar, webinar, podcast, panel, workshop, keynote, other)
- Description of the event
- Dates (start date, end date, application deadline)
- Location (venue, city, state, country, virtual options)
- Compensation (paid/unpaid, amount if mentioned, travel/accommodation included)
- Application information (URL, contact email, requirements)
- Target audience
- Expected audience size
- Source URL

Important guidelines:
1. Only include opportunities that are actively seeking speakers/presenters
2. Focus on events happening in the future (next 12 months)
3. Be accurate - if information is not available, leave it as null
4. Assign a confidence score (0.0 to 1.0) based on how complete and reliable the information is
5. Return ONLY valid JSON, no additional text or explanation

Output Format:
Return a JSON array of opportunity objects. Each object should follow this exact structure:
{
    "id": "unique_id",
    "event_name": "Name of the event",
    "event_type": "conference|seminar|webinar|podcast|panel|workshop|keynote|other",
    "description": "Brief description",
    "dates": {
        "start_date": "YYYY-MM-DD or null",
        "end_date": "YYYY-MM-DD or null",
        "application_deadline": "YYYY-MM-DD or null"
    },
    "location": {
        "venue": "Venue name or null",
        "city": "City or null",
        "state": "State or null",
        "country": "Country or null",
        "is_virtual": true/false,
        "has_virtual_option": true/false
    },
    "compensation": {
        "is_paid": true/false,
        "compensation_type": "paid|honorarium|travel_only|unpaid|negotiable|unknown",
        "amount": number or null,
        "currency": "USD",
        "includes_travel": true/false,
        "includes_accommodation": true/false,
        "details": "Additional compensation details or null"
    },
    "application": {
        "url": "Application URL or null",
        "contact_email": "Contact email or null",
        "requirements": ["requirement1", "requirement2"]
    },
    "target_audience": ["audience1", "audience2"],
    "expected_audience_size": "100-500 or null",
    "keywords_matched": ["keyword1", "keyword2"],
    "source_url": "URL where this was found",
    "confidence_score": 0.0 to 1.0
}"""


def get_user_prompt(keywords: list, search_results: str, opportunity_types: list) -> str:
    """
    Generate the user prompt with search context.
    
    Args:
        keywords: List of search keywords
        search_results: Raw search results from Bing
        opportunity_types: Types of opportunities to look for
    
    Returns:
        Formatted user prompt string
    """
    keywords_str = ", ".join(keywords)
    types_str = ", ".join(opportunity_types)
    
    return f"""Find speaking opportunities based on the following search:

**Keywords:** {keywords_str}
**Opportunity Types to Find:** {types_str}

**Search Results to Analyze:**
{search_results}

Based on the search results above, identify and extract all relevant speaking opportunities.
Return the results as a JSON array. If no relevant opportunities are found, return an empty array: []

Remember:
- Only include opportunities actively seeking speakers
- Focus on future events (next 12 months)
- Be accurate with dates and compensation information
- Include the source URL for each opportunity
- Assign appropriate confidence scores based on information completeness"""


def get_refinement_prompt(initial_results: str, feedback: str) -> str:
    """
    Generate a prompt to refine results based on feedback.
    
    Args:
        initial_results: Initial extraction results
        feedback: User or system feedback for refinement
    
    Returns:
        Refinement prompt string
    """
    return f"""Please refine the following opportunity extraction based on this feedback:

**Current Results:**
{initial_results}

**Feedback:**
{feedback}

Please provide updated results maintaining the same JSON structure."""
"""
Prompts for generating personalized proposals/pitches.
"""

PROPOSAL_SYSTEM_PROMPT = """You are an expert proposal writer specializing in crafting compelling speaker applications and pitches.

Your task is to write personalized, professional proposals that:
1. Grab attention with a strong opening
2. Clearly articulate the speaker's value proposition
3. Highlight relevant experience and credentials
4. Propose specific, relevant topics
5. Show understanding of the event's audience and goals
6. End with a clear call to action

Write in a confident but not arrogant tone. Be specific and avoid generic statements.
Tailor each proposal to the specific opportunity."""


def get_proposal_user_prompt(profile_summary: str, opportunity_details: str, matching_keywords: list, match_reasons: list) -> str:
    keywords_str = ", ".join(matching_keywords) if matching_keywords else "N/A"
    reasons_str = "\n".join([f"- {r}" for r in match_reasons]) if match_reasons else "N/A"
    
    return f"""Please write a compelling speaker proposal for this opportunity.

**CANDIDATE PROFILE:**
{profile_summary}

**OPPORTUNITY DETAILS:**
{opportunity_details}

**WHY THIS IS A GOOD MATCH:**
{reasons_str}

**MATCHING KEYWORDS:**
{keywords_str}

**INSTRUCTIONS:**
Write a complete proposal that includes:
1. A compelling subject line for the email/application
2. Professional greeting
3. Strong opening paragraph that hooks the reader
4. Value proposition - what unique perspective/expertise the candidate brings
5. Relevant experience - specific examples that demonstrate expertise
6. 2-3 proposed talk topics tailored to this event
7. Closing paragraph with call to action
8. Professional signature

**OUTPUT FORMAT:**
Return a JSON object with the following structure:
{{
  "subject_line": "Compelling subject line",
  "greeting": "Dear [Event Organizers/Selection Committee],",
  "opening_paragraph": "Opening that grabs attention...",
  "value_proposition": "What unique value the speaker brings...",
  "relevant_experience": "Specific relevant experience...",
  "proposed_topics": [
    "Topic 1: Brief description",
    "Topic 2: Brief description",
    "Topic 3: Brief description"
  ],
  "closing_paragraph": "Strong closing with call to action...",
  "signature": "Best regards,\\n[Name]\\n[Title]",
  "full_proposal": "The complete proposal as a single formatted text..."
}}

The "full_proposal" should be a complete, ready-to-send proposal combining all elements with proper formatting.

Return ONLY the JSON object, no additional text."""


def get_batch_proposal_prompt(profile_summary: str, opportunities_list: str, max_proposals: int = 5) -> str:
    return f"""Please write compelling speaker proposals for the top {max_proposals} opportunities.

**CANDIDATE PROFILE:**
{profile_summary}

**OPPORTUNITIES (ranked by match score):**
{opportunities_list}

**INSTRUCTIONS:**
For each opportunity, write a tailored proposal that:
1. Is specific to that event (not generic)
2. Highlights relevant experience for that particular audience
3. Proposes topics relevant to the event's theme
4. Shows understanding of the event's goals

**OUTPUT FORMAT:**
Return a JSON array with proposals for each opportunity:
[
  {{
    "opportunity_id": "opp_001",
    "event_name": "Event Name",
    "subject_line": "Subject line",
    "greeting": "Greeting",
    "opening_paragraph": "Opening...",
    "value_proposition": "Value prop...",
    "relevant_experience": "Experience...",
    "proposed_topics": ["Topic 1", "Topic 2"],
    "closing_paragraph": "Closing...",
    "signature": "Signature",
    "full_proposal": "Complete formatted proposal..."
  }}
]

Return ONLY the JSON array, no additional text."""
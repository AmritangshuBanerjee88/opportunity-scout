"""
Service for parsing candidate profiles from various formats.
Supports PDF, DOCX, and plain text.
"""

import os
import json
import logging
import uuid
from typing import Optional, Dict, Any
from openai import AzureOpenAI
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProfileParserService:
    """
    Service for parsing and extracting structured profile information.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the profile parser service."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if not endpoint or not api_key:
            raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set")
        
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=self.config['azure_openai']['api_version']
        )
        
        self.chat_deployment = self.config['models']['chat']['deployment_name']
        logger.info(f"ProfileParserService initialized with model: {self.chat_deployment}")
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            import io
            try:
                from pypdf import PdfReader
            except ImportError:
                from PyPDF2 import PdfReader
            
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n".join(text_parts)
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, docx_content: bytes) -> str:
        """Extract text from DOCX bytes."""
        try:
            import io
            from docx import Document
            
            docx_file = io.BytesIO(docx_content)
            doc = Document(docx_file)
            
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            return "\n".join(text_parts)
        
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return ""
    
    def parse_profile_with_ai(self, raw_text: str) -> Dict[str, Any]:
        """Use AI to extract structured profile from raw text."""
        
        system_prompt = """You are an expert at analyzing professional profiles and resumes.
Extract key information and return it as a JSON object."""
        
        user_prompt = f"""Please analyze the following profile/resume text and extract key information.

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

        try:
            response = self.client.chat.completions.create(
                model=self.chat_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON from response
            try:
                # Try direct parsing
                return json.loads(result_text)
            except json.JSONDecodeError:
                # Try to find JSON in response
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    return json.loads(result_text[start_idx:end_idx])
                return {}
        
        except Exception as e:
            logger.error(f"Error parsing profile with AI: {e}")
            return {}
    
    def create_profile_summary(self, profile_data: Dict[str, Any], preferences_text: str = "") -> str:
        """Create a text summary of the profile for ranking."""
        
        parts = []
        
        if profile_data.get("name"):
            parts.append(f"Name: {profile_data['name']}")
        
        if profile_data.get("title"):
            parts.append(f"Title: {profile_data['title']}")
        
        if profile_data.get("primary_expertise"):
            parts.append(f"Primary Expertise: {', '.join(profile_data['primary_expertise'])}")
        
        if profile_data.get("secondary_expertise"):
            parts.append(f"Secondary Expertise: {', '.join(profile_data['secondary_expertise'])}")
        
        if profile_data.get("years_of_experience"):
            parts.append(f"Years of Experience: {profile_data['years_of_experience']}")
        
        if profile_data.get("speaking_experience"):
            parts.append(f"Speaking Experience: {profile_data['speaking_experience']}")
        
        if profile_data.get("notable_venues"):
            parts.append(f"Notable Venues: {', '.join(profile_data['notable_venues'])}")
        
        if profile_data.get("education"):
            parts.append(f"Education: {', '.join(profile_data['education'])}")
        
        if profile_data.get("publications"):
            parts.append(f"Publications: {', '.join(profile_data['publications'])}")
        
        if profile_data.get("awards"):
            parts.append(f"Awards: {', '.join(profile_data['awards'])}")
        
        if profile_data.get("bio"):
            parts.append(f"Bio: {profile_data['bio']}")
        
        if preferences_text:
            parts.append(f"Preferences: {preferences_text}")
        
        return "\n".join(parts)
    
    def parse_profile(
        self,
        profile_text: Optional[str] = None,
        resume_content: Optional[bytes] = None,
        resume_filename: Optional[str] = None,
        preferences_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse profile from various inputs.
        
        Returns:
            Dictionary with profile_data, profile_summary, and raw_text
        """
        raw_text_parts = []
        
        # Extract text from resume file
        if resume_content and resume_filename:
            if resume_filename.lower().endswith('.pdf'):
                extracted = self.extract_text_from_pdf(resume_content)
                if extracted:
                    raw_text_parts.append(extracted)
            elif resume_filename.lower().endswith('.docx'):
                extracted = self.extract_text_from_docx(resume_content)
                if extracted:
                    raw_text_parts.append(extracted)
            elif resume_filename.lower().endswith('.txt'):
                raw_text_parts.append(resume_content.decode('utf-8'))
        
        # Add profile text
        if profile_text:
            raw_text_parts.append(profile_text)
        
        # Combine all text
        raw_text = "\n\n".join(raw_text_parts)
        
        if not raw_text.strip():
            return {
                "profile_id": str(uuid.uuid4()),
                "profile_data": {},
                "profile_summary": preferences_text or "No profile provided",
                "raw_text": preferences_text or ""
            }
        
        # Parse with AI
        profile_data = self.parse_profile_with_ai(raw_text)
        
        # Create summary
        profile_summary = self.create_profile_summary(profile_data, preferences_text)
        
        return {
            "profile_id": str(uuid.uuid4()),
            "profile_data": profile_data,
            "profile_summary": profile_summary,
            "raw_text": raw_text
        }
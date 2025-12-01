"""
Opportunity Scout & Proposal Architect - Combined Streamlit Frontend

A web application for:
1. Finding speaking opportunities (Part A)
2. Ranking opportunities and generating proposals (Part B)

Password protected for authorized access only.
"""

import streamlit as st
import json
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import requests

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Opportunity Scout & Proposal Architect",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM STYLING
# =============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .match-score-high {
        color: #28a745;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .match-score-medium {
        color: #ffc107;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .match-score-low {
        color: #dc3545;
        font-weight: bold;
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# API CLIENTS
# =============================================================================

class OpportunityScoutClient:
    """Client for Backend A - Opportunity Scout."""
    
    def __init__(self, endpoint_url: str, api_key: str):
        self.endpoint_url = endpoint_url.rstrip('/')
        self.api_key = api_key
        if not self.endpoint_url.endswith('/score'):
            self.scoring_url = f"{self.endpoint_url}/score"
        else:
            self.scoring_url = self.endpoint_url
    
    def search(self, keywords: List[str], opportunity_types: List[str], 
               max_results: int = 20) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "azureml-model-deployment": "default"
        }
        payload = {
            "keywords": keywords,
            "opportunity_types": opportunity_types,
            "max_results": max_results
        }
        response = requests.post(self.scoring_url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, str):
            result = json.loads(result)
        return result


class ProposalArchitectClient:
    """Client for Backend B - Proposal Architect."""
    
    def __init__(self, endpoint_url: str, api_key: str):
        self.endpoint_url = endpoint_url.rstrip('/')
        self.api_key = api_key
        if not self.endpoint_url.endswith('/score'):
            self.scoring_url = f"{self.endpoint_url}/score"
        else:
            self.scoring_url = self.endpoint_url
    
    def _make_request(self, payload: Dict) -> Dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "azureml-model-deployment": "default"
        }
        response = requests.post(self.scoring_url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, str):
            result = json.loads(result)
        return result
    
    def upload(self, opportunities_json: str, profile_text: str = None,
               resume_base64: str = None, resume_filename: str = None,
               preferences_text: str = None) -> Dict:
        payload = {
            "action": "upload",
            "opportunities_json": opportunities_json,
            "profile_text": profile_text,
            "resume_base64": resume_base64,
            "resume_filename": resume_filename,
            "preferences_text": preferences_text
        }
        return self._make_request(payload)
    
    def rank(self, session_id: str) -> Dict:
        payload = {
            "action": "rank",
            "session_id": session_id
        }
        return self._make_request(payload)
    
    def generate_proposal(self, session_id: str, opportunity_id: str) -> Dict:
        payload = {
            "action": "generate_proposal",
            "session_id": session_id,
            "opportunity_id": opportunity_id
        }
        return self._make_request(payload)
    
    def generate_all_proposals(self, session_id: str, max_proposals: int = 5) -> Dict:
        payload = {
            "action": "generate_all_proposals",
            "session_id": session_id,
            "max_proposals": max_proposals
        }
        return self._make_request(payload)


# =============================================================================
# PASSWORD PROTECTION
# =============================================================================

def check_password():
    """Returns True if the user has entered the correct password."""
    
    def password_entered():
        if st.session_state["password"] == st.secrets.get("APP_PASSWORD", ""):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("""
        <div style="text-align: center; padding: 50px;">
            <h1>🎯 Opportunity Scout & Proposal Architect</h1>
            <p style="color: #666;">AI-Powered Speaking Opportunity Finder & Proposal Generator</p>
            <br>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input(
                "🔐 Enter Access Code", 
                type="password", 
                on_change=password_entered, 
                key="password",
                placeholder="Enter your access code..."
            )
            st.markdown("""
            <p style="text-align: center; color: #888; font-size: 0.9rem;">
                Don't have an access code? Contact the administrator.
            </p>
            """, unsafe_allow_html=True)
        return False
    
    elif not st.session_state["password_correct"]:
        st.markdown("""
        <div style="text-align: center; padding: 50px;">
            <h1>🎯 Opportunity Scout & Proposal Architect</h1>
            <p style="color: #666;">AI-Powered Speaking Opportunity Finder & Proposal Generator</p>
            <br>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input(
                "🔐 Enter Access Code", 
                type="password", 
                on_change=password_entered, 
                key="password",
                placeholder="Enter your access code..."
            )
            st.error("❌ Incorrect access code. Please try again.")
        return False
    
    else:
        return True


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_opportunity_scout_client() -> Optional[OpportunityScoutClient]:
    """Get Opportunity Scout client."""
    endpoint = st.secrets.get("AZURE_ML_ENDPOINT_A", "")
    api_key = st.secrets.get("AZURE_ML_KEY_A", "")
    if endpoint and api_key:
        return OpportunityScoutClient(endpoint, api_key)
    return None


def get_proposal_architect_client() -> Optional[ProposalArchitectClient]:
    """Get Proposal Architect client."""
    endpoint = st.secrets.get("AZURE_ML_ENDPOINT_B", "")
    api_key = st.secrets.get("AZURE_ML_KEY_B", "")
    if endpoint and api_key:
        return ProposalArchitectClient(endpoint, api_key)
    return None


def format_date(date_str: str) -> str:
    """Format date string for display."""
    if not date_str:
        return "TBD"
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y")
    except:
        return date_str


def get_match_score_class(score: float) -> str:
    """Get CSS class based on match score."""
    if score >= 0.8:
        return "match-score-high"
    elif score >= 0.5:
        return "match-score-medium"
    else:
        return "match-score-low"


# =============================================================================
# TAB 1: OPPORTUNITY SCOUT
# =============================================================================

def render_opportunity_scout_tab():
    """Render the Opportunity Scout tab."""
    
    st.header("🔍 Find Speaking Opportunities")
    st.markdown("Search the web for conferences, webinars, podcasts, and more!")
    
    # Sidebar options for this tab
    with st.sidebar:
        st.subheader("🎯 Search Filters")
        
        opp_types = {
            "conference": st.checkbox("📢 Conferences", value=True, key="scout_conf"),
            "seminar": st.checkbox("🎓 Seminars", value=True, key="scout_sem"),
            "webinar": st.checkbox("💻 Webinars", value=True, key="scout_web"),
            "podcast": st.checkbox("🎙️ Podcasts", value=False, key="scout_pod"),
            "panel": st.checkbox("👥 Panel Discussions", value=False, key="scout_pan"),
            "workshop": st.checkbox("🛠️ Workshops", value=False, key="scout_work")
        }
        selected_types = [k for k, v in opp_types.items() if v]
        
        max_results = st.slider("📊 Max Results", 5, 50, 20, key="scout_max")
    
    # Main content
    keywords_input = st.text_area(
        "Enter your keywords (one per line or comma-separated)",
        placeholder="AI Ethics\nWomen in Data Science\nMachine Learning",
        height=100,
        key="scout_keywords"
    )
    
    keywords = []
    if keywords_input:
        for line in keywords_input.split('\n'):
            for kw in line.split(','):
                kw = kw.strip()
                if kw:
                    keywords.append(kw)
    
    if keywords:
        st.markdown("**Keywords:** " + ", ".join([f"`{kw}`" for kw in keywords]))
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_clicked = st.button(
            "🔍 Search for Opportunities",
            type="primary",
            use_container_width=True,
            disabled=len(keywords) == 0 or len(selected_types) == 0,
            key="scout_search_btn"
        )
    
    if len(keywords) == 0:
        st.warning("⚠️ Please enter at least one keyword.")
    if len(selected_types) == 0:
        st.warning("⚠️ Please select at least one opportunity type.")
    
    # Process search
    if search_clicked and keywords and selected_types:
        client = get_opportunity_scout_client()
        if not client:
            st.error("❌ Opportunity Scout API not configured.")
            return
        
        with st.spinner("🔍 Searching... This may take 1-2 minutes."):
            try:
                response = client.search(keywords, selected_types, max_results)
                st.session_state["scout_response"] = response
                st.success(f"✅ Found {len(response.get('opportunities', []))} opportunities!")
            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")
                return
    
    # Display results
    if "scout_response" in st.session_state:
        response = st.session_state["scout_response"]
        opportunities = response.get("opportunities", [])
        
        if opportunities:
            st.divider()
            st.subheader(f"📋 Results ({len(opportunities)} opportunities)")
            
            # Download button
            json_data = json.dumps(response, indent=2)
            st.download_button(
                label="📥 Download Results as JSON",
                data=json_data,
                file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key="scout_download"
            )
            
            st.info("💡 **Tip:** Download the JSON and upload it to the **Proposal Architect** tab to rank and generate proposals!")
            
            st.divider()
            
            # Display each opportunity
            for i, opp in enumerate(opportunities, 1):
                with st.expander(f"{i}. {opp.get('event_name', 'Unknown Event')}", expanded=(i <= 3)):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Type:** {opp.get('event_type', 'N/A')}")
                        
                        dates = opp.get("dates", {})
                        if dates.get("start_date"):
                            st.markdown(f"**Date:** {format_date(dates['start_date'])}")
                        if dates.get("application_deadline"):
                            st.markdown(f"**Deadline:** {format_date(dates['application_deadline'])}")
                    
                    with col2:
                        location = opp.get("location", {})
                        loc_parts = []
                        if location.get("city"):
                            loc_parts.append(location["city"])
                        if location.get("country"):
                            loc_parts.append(location["country"])
                        if loc_parts:
                            st.markdown(f"**Location:** {', '.join(loc_parts)}")
                        elif location.get("is_virtual"):
                            st.markdown("**Location:** Virtual")
                        
                        comp = opp.get("compensation", {})
                        if comp.get("is_paid"):
                            amount = comp.get("amount")
                            if amount:
                                st.markdown(f"**Compensation:** ${amount:,.0f}")
                            else:
                                st.markdown("**Compensation:** Paid")
                        else:
                            st.markdown("**Compensation:** Unpaid/Unknown")
                    
                    if opp.get("description"):
                        st.markdown(f"**Description:** {opp['description'][:300]}...")
                    
                    app_info = opp.get("application", {})
                    if app_info.get("url"):
                        st.link_button("🔗 Apply Now", app_info["url"])


# =============================================================================
# TAB 2: PROPOSAL ARCHITECT
# =============================================================================

def render_proposal_architect_tab():
    """Render the Proposal Architect tab."""
    
    st.header("📝 Proposal Architect")
    st.markdown("Upload your profile and opportunities to get ranked matches and personalized proposals!")
    
    # Step 1: Upload Data
    st.subheader("Step 1: Upload Your Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📄 Opportunities JSON**")
        uploaded_json = st.file_uploader(
            "Upload the JSON from Opportunity Scout",
            type=["json"],
            key="arch_json"
        )
        
        if uploaded_json:
            try:
                json_content = uploaded_json.read().decode('utf-8')
                json_data = json.loads(json_content)
                opp_count = len(json_data.get("opportunities", []))
                st.success(f"✅ Loaded {opp_count} opportunities")
                st.session_state["arch_opportunities_json"] = json_content
            except Exception as e:
                st.error(f"❌ Invalid JSON: {e}")
    
    with col2:
        st.markdown("**📎 Your Resume/CV (Optional)**")
        uploaded_resume = st.file_uploader(
            "Upload PDF, DOCX, or TXT",
            type=["pdf", "docx", "txt"],
            key="arch_resume"
        )
        
        if uploaded_resume:
            st.success(f"✅ Uploaded: {uploaded_resume.name}")
            resume_bytes = uploaded_resume.read()
            st.session_state["arch_resume_base64"] = base64.b64encode(resume_bytes).decode('utf-8')
            st.session_state["arch_resume_filename"] = uploaded_resume.name
    
    st.markdown("**✍️ Your Profile/Bio**")
    profile_text = st.text_area(
        "Describe yourself, your expertise, and speaking experience",
        placeholder="""Example:
Dr. Jane Smith - AI Researcher and Keynote Speaker

10+ years of experience in machine learning and AI ethics.
Previously spoke at TEDx, NeurIPS, and World Economic Forum.
Author of "AI for Good" bestselling book.
PhD in Computer Science from MIT.

Expertise: AI Ethics, Machine Learning, Data Science, Women in Tech""",
        height=200,
        key="arch_profile"
    )
    
    st.markdown("**🎯 Your Preferences**")
    preferences_text = st.text_area(
        "What are you looking for in opportunities?",
        placeholder="""Example:
- Prefer paid speaking opportunities ($2000+ honorarium)
- Willing to travel internationally
- Interested in both in-person and virtual events
- Available from March 2025 onwards
- Prefer conferences and webinars over podcasts""",
        height=120,
        key="arch_preferences"
    )
    
    # Upload button
    can_upload = "arch_opportunities_json" in st.session_state and (profile_text or "arch_resume_base64" in st.session_state)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        upload_clicked = st.button(
            "📤 Upload & Process",
            type="primary",
            use_container_width=True,
            disabled=not can_upload,
            key="arch_upload_btn"
        )
    
    if not can_upload:
        st.info("💡 Please upload opportunities JSON and provide your profile (text or resume).")
    
    # Process upload
    if upload_clicked:
        client = get_proposal_architect_client()
        if not client:
            st.error("❌ Proposal Architect API not configured.")
            return
        
        with st.spinner("📤 Uploading and processing your data..."):
            try:
                result = client.upload(
                    opportunities_json=st.session_state.get("arch_opportunities_json", "{}"),
                    profile_text=profile_text,
                    resume_base64=st.session_state.get("arch_resume_base64"),
                    resume_filename=st.session_state.get("arch_resume_filename"),
                    preferences_text=preferences_text
                )
                
                if result.get("success"):
                    st.session_state["arch_session_id"] = result["session_id"]
                    st.session_state["arch_profile_summary"] = result.get("profile_summary", "")
                    st.success(f"✅ Upload successful! Session ID: {result['session_id'][:8]}...")
                else:
                    st.error(f"❌ Upload failed: {result.get('error')}")
                    return
            except Exception as e:
                st.error(f"❌ Upload failed: {str(e)}")
                return
    
    # Step 2: Rank Opportunities
    if "arch_session_id" in st.session_state:
        st.divider()
        st.subheader("Step 2: Rank Opportunities")
        
        if st.session_state.get("arch_profile_summary"):
            with st.expander("📋 Your Profile Summary", expanded=False):
                st.text(st.session_state["arch_profile_summary"])
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            rank_clicked = st.button(
                "📊 Rank Opportunities",
                type="primary",
                use_container_width=True,
                key="arch_rank_btn"
            )
        
        if rank_clicked:
            client = get_proposal_architect_client()
            with st.spinner("📊 Ranking opportunities based on your profile..."):
                try:
                    result = client.rank(st.session_state["arch_session_id"])
                    
                    if result.get("success"):
                        st.session_state["arch_rankings"] = result
                        st.success(f"✅ Ranked {result.get('valid_opportunities', 0)} opportunities!")
                    else:
                        st.error(f"❌ Ranking failed: {result.get('error')}")
                except Exception as e:
                    st.error(f"❌ Ranking failed: {str(e)}")
    
    # Display Rankings
    if "arch_rankings" in st.session_state:
        rankings = st.session_state["arch_rankings"]
        ranked_opps = rankings.get("ranked_opportunities", [])
        
        if ranked_opps:
            st.divider()
            st.subheader(f"Step 3: Review Rankings ({len(ranked_opps)} matches)")
            
            st.markdown(f"""
            - **Total Opportunities:** {rankings.get('total_opportunities', 0)}
            - **Valid (Not Expired):** {rankings.get('valid_opportunities', 0)}
            - **Expired:** {rankings.get('expired_opportunities', 0)}
            """)
            
            for i, opp in enumerate(ranked_opps, 1):
                score = opp.get("match_score", 0)
                score_class = get_match_score_class(score)
                
                with st.expander(f"#{i} - {opp.get('event_name', 'Unknown')} ({score:.0%} match)", expanded=(i <= 3)):
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        st.markdown(f"**Match Score:** <span class='{score_class}'>{score:.0%}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Type:** {opp.get('event_type', 'N/A')}")
                        st.markdown(f"**Paid:** {'Yes 💰' if opp.get('is_paid') else 'No'}")
                    
                    with col2:
                        if opp.get("start_date"):
                            st.markdown(f"**Date:** {format_date(opp['start_date'])}")
                        if opp.get("location"):
                            st.markdown(f"**Location:** {opp['location']}")
                        elif opp.get("is_virtual"):
                            st.markdown("**Location:** Virtual 🌐")
                    
                    with col3:
                        if opp.get("application_deadline"):
                            st.markdown(f"**Deadline:** {format_date(opp['application_deadline'])}")
                        if opp.get("days_until_deadline"):
                            st.markdown(f"**Days Left:** {opp['days_until_deadline']}")
                    
                    # Match reasons
                    reasons = opp.get("match_reasons", [])
                    if reasons:
                        st.markdown("**Why it's a good match:**")
                        for reason in reasons[:3]:
                            st.markdown(f"- {reason}")
                    
                    # Keywords
                    keywords = opp.get("matching_keywords", [])
                    if keywords:
                        st.markdown(f"**Matching Keywords:** {', '.join(keywords[:5])}")
                    
                    # Generate proposal button
                    if st.button(f"📝 Generate Proposal", key=f"gen_prop_{opp.get('opportunity_id', i)}"):
                        client = get_proposal_architect_client()
                        with st.spinner("📝 Generating personalized proposal..."):
                            try:
                                prop_result = client.generate_proposal(
                                    st.session_state["arch_session_id"],
                                    opp.get("opportunity_id")
                                )
                                
                                if prop_result.get("success"):
                                    proposal = prop_result.get("proposal", {})
                                    st.session_state[f"proposal_{opp.get('opportunity_id')}"] = proposal
                                    st.success("✅ Proposal generated!")
                                else:
                                    st.error(f"❌ Failed: {prop_result.get('error')}")
                            except Exception as e:
                                st.error(f"❌ Failed: {str(e)}")
                    
                    # Display generated proposal
                    prop_key = f"proposal_{opp.get('opportunity_id')}"
                    if prop_key in st.session_state:
                        proposal = st.session_state[prop_key]
                        st.divider()
                        st.markdown("### 📧 Generated Proposal")
                        st.markdown(f"**Subject:** {proposal.get('subject_line', 'N/A')}")
                        st.text_area(
                            "Full Proposal",
                            value=proposal.get("full_proposal", ""),
                            height=300,
                            key=f"prop_text_{opp.get('opportunity_id')}"
                        )
                        
                        st.download_button(
                            "📥 Download Proposal",
                            data=proposal.get("full_proposal", ""),
                            file_name=f"proposal_{opp.get('event_name', 'unknown')[:20]}.txt",
                            mime="text/plain",
                            key=f"download_prop_{opp.get('opportunity_id')}"
                        )
            
            # Generate all proposals
            st.divider()
            st.subheader("Step 4: Generate All Proposals")
            
            num_proposals = st.slider("Number of proposals to generate", 1, min(10, len(ranked_opps)), 5, key="num_props")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📝 Generate All Proposals", type="primary", use_container_width=True, key="gen_all_btn"):
                    client = get_proposal_architect_client()
                    with st.spinner(f"📝 Generating {num_proposals} proposals... This may take a few minutes."):
                        try:
                            result = client.generate_all_proposals(
                                st.session_state["arch_session_id"],
                                num_proposals
                            )
                            
                            if result.get("success"):
                                st.session_state["arch_all_proposals"] = result
                                st.success(f"✅ Generated {result.get('total_generated', 0)} proposals!")
                            else:
                                st.error(f"❌ Failed: {result.get('error')}")
                        except Exception as e:
                            st.error(f"❌ Failed: {str(e)}")
            
            # Display all proposals
            if "arch_all_proposals" in st.session_state:
                all_props = st.session_state["arch_all_proposals"]
                proposals = all_props.get("proposals", [])
                download_text = all_props.get("download_text", "")
                
                if proposals:
                    st.divider()
                    st.markdown(f"### 📧 All Generated Proposals ({len(proposals)})")
                    
                    if download_text:
                        st.download_button(
                            "📥 Download All Proposals",
                            data=download_text,
                            file_name=f"all_proposals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            key="download_all_props"
                        )
                    
                    for prop in proposals:
                        with st.expander(f"📧 {prop.get('event_name', 'Unknown')}"):
                            st.markdown(f"**Subject:** {prop.get('subject_line', 'N/A')}")
                            st.text_area(
                                "Proposal",
                                value=prop.get("full_proposal", ""),
                                height=200,
                                key=f"all_prop_{prop.get('id', '')}"
                            )


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    # Check password first
    if not check_password():
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎯 Navigation")
        
        if st.button("🚪 Logout"):
            st.session_state["password_correct"] = False
            st.rerun()
        
        st.divider()
        
        st.markdown("""
        ### How to Use
        
        **Step 1: Find Opportunities**
        Use the **Opportunity Scout** tab to search for speaking opportunities.
        
        **Step 2: Download JSON**
        Download the results as JSON.
        
        **Step 3: Generate Proposals**
        Upload the JSON to **Proposal Architect** along with your profile to get ranked matches and personalized proposals.
        """)
    
    # Main content with tabs
    st.markdown('<p class="main-header">🎯 Opportunity Scout & Proposal Architect</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Speaking Opportunity Finder & Proposal Generator</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔍 Opportunity Scout", "📝 Proposal Architect"])
    
    with tab1:
        render_opportunity_scout_tab()
    
    with tab2:
        render_proposal_architect_tab()
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.9rem;">
        <p>Opportunity Scout & Proposal Architect | Powered by Azure AI</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
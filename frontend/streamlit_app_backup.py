"""
Opportunity Scout - Streamlit Frontend

A web application for finding speaking opportunities for freelancers,
influencers, and keynote speakers.

Password protected for authorized access only.
"""

import streamlit as st
import json
from datetime import datetime
from typing import List, Dict, Any
import os

from utils.api_client import OpportunityScoutClient, SearchRequest, Opportunity

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Opportunity Scout",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# PASSWORD PROTECTION
# =============================================================================

def check_password():
    """Returns `True` if the user has entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets.get("APP_PASSWORD", ""):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    # First run, show input for password
    if "password_correct" not in st.session_state:
        st.markdown("""
        <div style="text-align: center; padding: 50px;">
            <h1>🔍 Opportunity Scout</h1>
            <p style="color: #666;">AI-Powered Speaking Opportunity Finder</p>
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
    
    # Password was entered incorrectly
    elif not st.session_state["password_correct"]:
        st.markdown("""
        <div style="text-align: center; padding: 50px;">
            <h1>🔍 Opportunity Scout</h1>
            <p style="color: #666;">AI-Powered Speaking Opportunity Finder</p>
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
    
    # Password is correct
    else:
        return True


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
    .opportunity-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1E88E5;
    }
    .paid-badge {
        background-color: #4CAF50;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .unpaid-badge {
        background-color: #FF9800;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .virtual-badge {
        background-color: #2196F3;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .confidence-high {
        color: #4CAF50;
    }
    .confidence-medium {
        color: #FF9800;
    }
    .confidence-low {
        color: #f44336;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_api_client() -> OpportunityScoutClient:
    """Get or create API client from session state."""
    endpoint_url = st.secrets.get("AZURE_ML_ENDPOINT_A", os.getenv("AZURE_ML_ENDPOINT_A", ""))
    api_key = st.secrets.get("AZURE_ML_KEY_A", os.getenv("AZURE_ML_KEY_A", ""))
    
    if not endpoint_url or not api_key:
        return None
    
    return OpportunityScoutClient(endpoint_url, api_key)


def format_date(date_str: str) -> str:
    """Format date string for display."""
    if not date_str:
        return "TBD"
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y")
    except:
        return date_str


def get_confidence_class(score: float) -> str:
    """Get CSS class based on confidence score."""
    if score >= 0.8:
        return "confidence-high"
    elif score >= 0.5:
        return "confidence-medium"
    else:
        return "confidence-low"


def render_opportunity_card(opp: Opportunity, index: int):
    """Render a single opportunity card."""
    
    with st.container():
        # Header with event name and badges
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {index}. {opp.event_name}")
        
        with col2:
            badges = []
            if opp.is_paid:
                badges.append("💰 Paid")
            else:
                badges.append("🎯 Unpaid")
            if opp.is_virtual:
                badges.append("🌐 Virtual")
            st.markdown(" | ".join(badges))
        
        # Details in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📅 Dates**")
            if opp.start_date:
                st.write(f"Start: {format_date(opp.start_date)}")
            if opp.end_date:
                st.write(f"End: {format_date(opp.end_date)}")
            if opp.application_deadline:
                st.write(f"⏰ Deadline: {format_date(opp.application_deadline)}")
        
        with col2:
            st.markdown("**📍 Location**")
            location_parts = []
            if opp.city:
                location_parts.append(opp.city)
            if opp.country:
                location_parts.append(opp.country)
            if location_parts:
                st.write(", ".join(location_parts))
            elif opp.is_virtual:
                st.write("Virtual Event")
            else:
                st.write("Location TBD")
        
        with col3:
            st.markdown("**💵 Compensation**")
            if opp.is_paid and opp.compensation_amount:
                st.write(f"${opp.compensation_amount:,.0f}")
            elif opp.is_paid:
                st.write("Paid (amount TBD)")
            elif opp.compensation_details:
                st.write(opp.compensation_details)
            else:
                st.write("Not specified")
        
        # Description
        if opp.description:
            with st.expander("📝 Description"):
                st.write(opp.description)
        
        # Event type and confidence
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**Type:** {opp.event_type.replace('_', ' ').title()}")
        
        with col2:
            confidence_pct = int(opp.confidence_score * 100)
            confidence_class = get_confidence_class(opp.confidence_score)
            st.markdown(f"**Confidence:** <span class='{confidence_class}'>{confidence_pct}%</span>", 
                       unsafe_allow_html=True)
        
        with col3:
            if opp.keywords_matched:
                st.markdown(f"**Keywords:** {', '.join(opp.keywords_matched[:3])}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if opp.application_url:
                st.link_button("🔗 Apply Now", opp.application_url, use_container_width=True)
        
        with col2:
            if opp.source_url:
                st.link_button("🌐 View Source", opp.source_url, use_container_width=True)
        
        st.divider()


def convert_to_json(opportunities: List[Dict], metadata: Dict) -> str:
    """Convert opportunities to downloadable JSON."""
    export_data = {
        "search_metadata": metadata,
        "opportunities": opportunities,
        "exported_at": datetime.now().isoformat()
    }
    return json.dumps(export_data, indent=2)


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    # Check password first
    if not check_password():
        return
    
    # Header
    st.markdown('<p class="main-header">🔍 Opportunity Scout</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Speaking Opportunity Finder</p>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Logout button
        if st.button("🚪 Logout"):
            st.session_state["password_correct"] = False
            st.rerun()
        
        st.divider()
        
        # Search parameters
        st.header("🎯 Search Parameters")
        
        # Opportunity types
        st.subheader("Opportunity Types")
        opp_types = {
            "conference": st.checkbox("📢 Conferences", value=True),
            "seminar": st.checkbox("🎓 Seminars", value=True),
            "webinar": st.checkbox("💻 Webinars", value=True),
            "podcast": st.checkbox("🎙️ Podcasts", value=False),
            "panel": st.checkbox("👥 Panel Discussions", value=False),
            "workshop": st.checkbox("🛠️ Workshops", value=False)
        }
        selected_types = [k for k, v in opp_types.items() if v]
        
        st.divider()
        
        # Location preference
        location_pref = st.selectbox(
            "🌍 Location Preference",
            options=["global", "virtual", "north_america", "europe", "asia"],
            format_func=lambda x: {
                "global": "🌍 Global (All locations)",
                "virtual": "💻 Virtual Only",
                "north_america": "🇺🇸 North America",
                "europe": "🇪🇺 Europe",
                "asia": "🌏 Asia"
            }.get(x, x)
        )
        
        # Time frame
        time_frame = st.slider(
            "📅 Time Frame (months)",
            min_value=1,
            max_value=12,
            value=6,
            help="Search for events happening within this time frame"
        )
        
        # Max results
        max_results = st.slider(
            "📊 Maximum Results",
            min_value=5,
            max_value=50,
            value=20,
            help="Maximum number of opportunities to find"
        )
    
    # Main content area
    st.header("🔎 Search for Opportunities")
    
    # Keyword input
    keywords_input = st.text_area(
        "Enter your keywords (one per line or comma-separated)",
        placeholder="AI Ethics\nWomen in Data Science\nMachine Learning",
        height=100,
        help="Enter topics you want to speak about. Each keyword will be searched."
    )
    
    # Parse keywords
    if keywords_input:
        # Handle both comma-separated and newline-separated
        keywords = []
        for line in keywords_input.split('\n'):
            for kw in line.split(','):
                kw = kw.strip()
                if kw:
                    keywords.append(kw)
    else:
        keywords = []
    
    # Display parsed keywords
    if keywords:
        st.markdown("**Keywords to search:**")
        st.write(", ".join([f"`{kw}`" for kw in keywords]))
    
    # Search button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_clicked = st.button(
            "🔍 Search for Opportunities",
            type="primary",
            use_container_width=True,
            disabled=len(keywords) == 0 or len(selected_types) == 0
        )
    
    # Validation messages
    if len(keywords) == 0:
        st.warning("⚠️ Please enter at least one keyword to search.")
    if len(selected_types) == 0:
        st.warning("⚠️ Please select at least one opportunity type.")
    
    # Process search
    if search_clicked and keywords and selected_types:
        # Get API client
        client = get_api_client()
        
        if not client:
            st.error("❌ API credentials not configured. Please contact administrator.")
            return
        
        # Create search request
        request = SearchRequest(
            keywords=keywords,
            opportunity_types=selected_types,
            location_preference=location_pref,
            time_frame_months=time_frame,
            max_results=max_results
        )
        
        # Show progress
        with st.spinner("🔍 Searching for opportunities... This may take 1-2 minutes."):
            try:
                # Make API call
                response = client.search(request)
                
                # Store in session state
                st.session_state["search_response"] = response
                st.session_state["search_keywords"] = keywords
                
                st.success(f"✅ Found {len(response.get('opportunities', []))} opportunities!")
                
            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")
                return
    
    # Display results
    if "search_response" in st.session_state:
        response = st.session_state["search_response"]
        opportunities_data = response.get("opportunities", [])
        metadata = response.get("search_metadata", {})
        
        st.divider()
        st.header(f"📋 Results ({len(opportunities_data)} opportunities)")
        
        # Download button
        if opportunities_data:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                json_data = convert_to_json(opportunities_data, metadata)
                st.download_button(
                    label="📥 Download Results as JSON",
                    data=json_data,
                    file_name=f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        st.divider()
        
        # Filter and sort options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_paid = st.selectbox(
                "💰 Compensation",
                options=["all", "paid", "unpaid"],
                format_func=lambda x: {"all": "All", "paid": "Paid Only", "unpaid": "Unpaid Only"}[x]
            )
        
        with col2:
            filter_virtual = st.selectbox(
                "📍 Format",
                options=["all", "virtual", "in_person"],
                format_func=lambda x: {"all": "All", "virtual": "Virtual Only", "in_person": "In-Person Only"}[x]
            )
        
        with col3:
            sort_by = st.selectbox(
                "📊 Sort By",
                options=["confidence", "date", "name"],
                format_func=lambda x: {"confidence": "Confidence Score", "date": "Event Date", "name": "Event Name"}[x]
            )
        
        # Parse opportunities
        opportunities = [Opportunity.from_api_response(o) for o in opportunities_data]
        
        # Apply filters
        if filter_paid == "paid":
            opportunities = [o for o in opportunities if o.is_paid]
        elif filter_paid == "unpaid":
            opportunities = [o for o in opportunities if not o.is_paid]
        
        if filter_virtual == "virtual":
            opportunities = [o for o in opportunities if o.is_virtual]
        elif filter_virtual == "in_person":
            opportunities = [o for o in opportunities if not o.is_virtual]
        
        # Apply sorting
        if sort_by == "confidence":
            opportunities.sort(key=lambda x: x.confidence_score, reverse=True)
        elif sort_by == "date":
            opportunities.sort(key=lambda x: x.start_date or "9999")
        elif sort_by == "name":
            opportunities.sort(key=lambda x: x.event_name.lower())
        
        # Display opportunities
        if opportunities:
            for i, opp in enumerate(opportunities, 1):
                render_opportunity_card(opp, i)
        else:
            st.info("No opportunities match the current filters.")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.9rem;">
        <p>Opportunity Scout - AI-Powered Speaking Opportunity Finder</p>
        <p>💡 Tip: Download results as JSON to use with Proposal Architect</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

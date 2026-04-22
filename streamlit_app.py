import streamlit as st
import pandas as pd
import numpy as np
import os
import time
from dotenv import load_dotenv
from groq import Groq

# Import our core logic
from src.phase1.retrieval.recommend import get_recommendations

# --- Configuration & Styling ---
st.set_page_config(
    page_title="Culinary AI | Personal Concierge",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a premium feel
st.markdown("""
    <style>
    .main {
        background-color: #FAFBFC;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        background-color: #DC2626;
        color: white;
        border: none;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #B91C1C;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.25);
        transform: translateY(-2px);
    }
    .restaurant-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .rating-badge {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.2rem 0.6rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .cuisine-tag {
        background-color: #F3F4F6;
        color: #4B5563;
        padding: 0.1rem 0.5rem;
        border-radius: 6px;
        font-size: 0.8rem;
        margin-right: 0.3rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Initialization ---
load_dotenv()

# Handle API Key from secrets or env
api_key = os.getenv("GROQ_API_KEY")
if not api_key and "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]

if not api_key:
    st.error("Missing GROQ_API_KEY. Please set it in your environment variables or Streamlit secrets.")
    st.stop()

client = Groq(api_key=api_key)

# Constants (mirrored from app.py)
LOCALITIES = ["Sarjapur Road", "BTM", "Whitefield", "Koramangala 5th Block", "Indiranagar", "Malleshwaram", "Brigade Road", "Marathahalli", "JP Nagar", "Basavanagudi", "Rajajinagar", "Vasanth Nagar", "Kalyan Nagar", "Old Airport Road", "HSR", "Cunningham Road", "Residency Road", "New BEL Road", "Koramangala 1st Block", "Koramangala 7th Block", "Banashankari", "Electronic City", "Koramangala 4th Block", "Lavelle Road", "MG Road", "Church Street", "Richmond Road", "Bellandur", "St. Marks Road", "ITPL Main Road, Whitefield", "Jayanagar", "Seshadripuram", "Bannerghatta Road", "Race Course Road", "Nagawara", "Koramangala 6th Block", "Ulsoor", "Hennur", "Kammanahalli", "City Market", "Brookefield", "Varthur Main Road, Whitefield", "Frazer Town", "Sadashiv Nagar", "Basaveshwara Nagar", "Thippasandra", "Koramangala 3rd Block", "Banaswadi", "Koramangala", "Koramangala 8th Block", "Sahakara Nagar", "Domlur", "Infantry Road", "Shanti Nagar", "Sankey Road", "Vijay Nagar", "Jeevan Bhima Nagar", "Majestic", "HBR Layout", "Yeshwantpur", "Koramangala 2nd Block", "Commercial Street", "Hosur Road", "Shivajinagar", "Kumaraswamy Layout", "Old Madras Road", "Sanjay Nagar", "RT Nagar", "Kaggadasapura", "Ejipura", "CV Raman Nagar", "Wilson Garden", "Rajarajeshwari Nagar", "Hebbal", "Bommanahalli", "Langford Town", "Magadi Road", "Rammurthy Nagar", "Yelahanka", "Jalahalli", "KR Puram", "South Bangalore", "East Bangalore", "Kanakapura Road", "Mysore Road", "Kengeri", "Uttarahalli", "Central Bangalore", "North Bangalore", "West Bangalore", "Nagarbhavi", "Peenya"]
CUISINES = ['Italian', 'Japanese', 'Mexican', 'Indian', 'Mediterranean', 'Chinese', 'North Indian', 'South Indian', 'Thai', 'Continental', 'Fast Food', 'Cafe']

# --- Sidebar Inputs ---
with st.sidebar:
    st.title("🎨 Preferences")
    st.markdown("Tailor your culinary journey.")
    
    area = st.selectbox("Location", [""] + sorted(LOCALITIES), help="Where are you looking to dine?")
    cuisine = st.selectbox("Cuisine", CUISINES)
    budget = st.select_slider("Budget (for two)", options=[500, 1000, 2000, 4000], value=1000, format_func=lambda x: f"₹{x}")
    min_rating = st.slider("Minimum Rating", 0.0, 5.0, 4.0, 0.1)
    notes = st.text_area("Additional Notes", placeholder="e.g. quiet for a date, outdoor seating, great cocktails...")
    
    search_button = st.button("Find My Match")

# --- Main Content ---
st.title("🍽️ Culinary AI")
st.markdown("#### The Epicurean Canvas: *Refine your gastronomic journey.*")

if search_button:
    if not area:
        st.warning("Please select a location to start.")
    else:
        with st.spinner("Curating your personalized recommendations..."):
            try:
                # Call recommendation logic
                results = get_recommendations(
                    area=area,
                    budget_inr=budget,
                    cuisine=cuisine,
                    min_rating=min_rating,
                    notes=notes,
                    top_n=5
                )
                
                if not results:
                    st.info("No perfect matches found for these exact criteria. Try broadening your search!")
                else:
                    st.success(f"Found {len(results)} matches for you!")
                    
                    for r in results:
                        with st.container():
                            st.markdown(f"""
                            <div class="restaurant-card">
                                <div style="display: flex; justify-content: space-between; align-items: start;">
                                    <h3 style="margin: 0; color: #111827;">{r['name']}</h3>
                                    <span class="rating-badge">⭐ {r['rating']}</span>
                                </div>
                                <div style="margin-top: 0.5rem;">
                                    {" ".join([f'<span class="cuisine-tag">{c}</span>' for c in r['cuisines']])}
                                </div>
                                <p style="margin-top: 1rem; color: #4B5563; font-style: italic; line-height: 1.5;">
                                    "{r['reason']}"
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

else:
    # Landing state
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.image("https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?q=80&w=800&auto=format&fit=crop", caption="Premium Dining Experiences")
    with col2:
        st.markdown("""
        ### Welcome to the Future of Dining
        Select your preferences in the sidebar to begin.
        
        Our AI doesn't just filter; it understands. Using advanced LLM reasoning, we analyze thousands of reviews to match you with the perfect table.
        
        **Try selecting:**
        - **Area**: Indiranagar
        - **Cuisine**: Italian
        - **Notes**: "Quiet for a date night"
        """)

st.markdown("---")
st.caption("© 2024 The Culinary Editorial. All rights reserved.")

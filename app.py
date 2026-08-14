import streamlit as st
import requests
import re
from agents import run_trip_planner
from fpdf import FPDF

st.set_page_config(page_title="TravelAgent AI", page_icon="✈️", layout="wide")

# ─── Custom CSS ──────────────────────────────────────────
st.markdown("""
<style>
    .main-title { font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #1E3A8A, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { font-size: 1.1rem; color: #6B7280; margin-bottom: 2rem; }
    .stButton>button { background: linear-gradient(90deg, #1E3A8A, #3B82F6); color: white; border: none; border-radius: 10px; padding: 0.8rem 2rem; font-size: 1.1rem; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(30,58,138,0.3); }
    .card { background: #F8FAFC; border-radius: 16px; padding: 1.5rem; border: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)

# ─── Helper: Clean text for PDF (Unicode → ASCII) ───────
def clean_for_pdf(text):
    replacements = {
        '—': '--',
        '–': '-',
        ''': "'",
        ''': "'",
        '"': '"',
        '"': '"',
        '…': '...',
        '•': '-',
        '→': '->',
        '←': '<-',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        '°': ' deg',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    text = text.replace('#', '').replace('**', '').replace('*', '').replace('---', '').replace('>', '')
    text = text.encode('latin-1', 'ignore').decode('latin-1')
    return text

# ─── Helper: Get Destination Image from Wikipedia ────────
@st.cache_data(show_spinner=False)
def get_destination_info(destination):
    try:
        query = destination.split(',')[0].strip().replace(' ', '_')
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        r = requests.get(url, timeout=5)
        data = r.json()
        img = data.get('thumbnail', {}).get('source')
        desc = data.get('extract', '')
        return img, desc
    except:
        return None, ''

# ─── Helper: Create PDF ──────────────────────────────────
def create_pdf(destination, duration, budget, currency, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 15, f"Travel Plan: {destination}", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"{duration} Days | Budget: {budget} {currency}", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "", 11)
    clean = clean_for_pdf(content)
    pdf.multi_cell(0, 7, clean)
    return bytes(pdf.output(dest="S"))

# ─── Header ──────────────────────────────────────────────
st.markdown('<div class="main-title">TravelAgent AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multi-Agent Smart Tourism Planning -- Research, Plan & Budget in Seconds</div>', unsafe_allow_html=True)

# ─── Layout: Form + Image Preview ────────────────────────
left, right = st.columns([1, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Trip Details")
    
    destination = st.text_input("Where to?", "Tokyo, Japan", placeholder="e.g. Santorini, Greece")
    
    c1, c2 = st.columns(2)
    with c1:
        duration = st.number_input("Days", 1, 14, 3)
    with c2:
        budget = st.number_input("Budget", 100, 50000, 2000)
    
    currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY", "AED", "CAD"])
    preferences = st.text_area("Travel Style & Preferences", 
        "local food, photography spots, walking tours, avoid tourist traps",
        placeholder="What do you love? Any must-haves or deal-breakers?")
    
    plan_btn = st.button("Generate My Trip", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    img_url, wiki_desc = get_destination_info(destination)
    if img_url:
        st.image(img_url, use_container_width=True)
        if wiki_desc:
            st.caption(wiki_desc[:250] + "...")
    else:
        st.info("Enter a destination to see a live preview from Wikipedia")

# ─── Results Section ─────────────────────────────────────
if plan_btn:
    if not destination.strip():
        st.error("Please enter a destination!")
    else:
        progress = st.empty()
        progress.info("Research Agent scanning... Planning Agent building itinerary... Budget Agent crunching numbers...")
        
        try:
            result = run_trip_planner(destination, duration, budget, currency, preferences)
            progress.empty()
            
            st.balloons()
            st.success("Your trip is ready!")
            
            tab1, tab2, tab3 = st.tabs(["Full Itinerary", "Budget Focus", "Export"])
            
            with tab1:
                st.markdown(result)
            
            with tab2:
                st.markdown("### Budget Breakdown")
                if "Budget" in result:
                    parts = result.split("Budget")
                    st.markdown(parts[-1])
                else:
                    st.markdown(result)
            
            with tab3:
                st.markdown("### Download Your Itinerary")
                pdf_bytes = create_pdf(destination, duration, budget, currency, result)
                st.download_button(
                    "Download PDF",
                    pdf_bytes,
                    f"Trip_{destination.replace(' ', '_').replace(',', '')}.pdf",
                    "application/pdf"
                )
                st.markdown("---")
                st.markdown("**Raw Markdown (copy to Notion/Obsidian):**")
                st.code(result, language="markdown")
                
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")
            st.info("Tip: Try a more specific destination like 'Paris, France' instead of just 'Paris'")

# ─── Footer ──────────────────────────────────────────────
st.markdown("---")
footer_html = "<div style='text-align:center; color:#9CA3AF; font-size:0.85rem;'>Built with Python + Groq LLM + Streamlit | <a href='https://github.com/khodor2341/travel-agent' target='_blank'>View on GitHub</a></div>"
st.markdown(footer_html, unsafe_allow_html=True)
destination = st.text_input(
    "Where to?", 
    "Tokyo, Japan", 
    placeholder="One city: 'Paris'  OR  Multi-city: 'Paris, Rome, Dubai'"
)
st.caption("For multi-city trips, separate cities with commas")
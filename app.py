import streamlit as st
import requests
import re
from agents import run_trip_planner
from fpdf import FPDF

st.set_page_config(page_title="TravelAgent AI", page_icon="✈️", layout="wide")

# ─── SIDEBAR: White-Label Settings ───────────────────────
with st.sidebar:
    st.markdown("### 🎨 Brand Settings")
    st.caption("Customize for your company")
    
    company_name = st.text_input("Company Name", "TravelAgent AI")
    logo_url = st.text_input("Logo URL (optional)", "", placeholder="https://your-logo.png")
    brand_color = st.color_picker("Brand Color", "#1E3A8A")
    contact_info = st.text_input("Contact / Website", "contact@travelagent.ai")
    
    st.markdown("---")
    st.markdown("**Powered by AI**")
    st.caption("Built by Khodor | [GitHub](https://github.com/khodor2341/travel-agent)")

# ─── Dynamic CSS with Brand Color ────────────────────────
st.markdown(f"""
<style>
    .main-title {{ font-size: 3rem; font-weight: 800; color: {brand_color}; }}
    .subtitle {{ font-size: 1.1rem; color: #6B7280; margin-bottom: 2rem; }}
    .stButton>button {{ background-color: {brand_color}; color: white; border: none; border-radius: 10px; padding: 0.8rem 2rem; font-size: 1.1rem; font-weight: 600; }}
    .stButton>button:hover {{ opacity: 0.9; transform: translateY(-2px); }}
    .card {{ background: #F8FAFC; border-radius: 16px; padding: 1.5rem; border: 1px solid #E2E8F0; }}
    .brand-header {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }}
</style>
""", unsafe_allow_html=True)

# ─── Helper: Clean text for PDF ──────────────────────────
def clean_for_pdf(text):
    replacements = {'—': '--', '–': '-', ''': "'", ''': "'", '"': '"', '"': '"', '…': '...', '•': '-', '→': '->', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '°': ' deg'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    emoji_pattern = re.compile("["u"\U0001F600-\U0001F64F"u"\U0001F300-\U0001F5FF"u"\U0001F680-\U0001F6FF"u"\U0001F1E0-\U0001F1FF"u"\U00002702-\U000027B0"u"\U000024C2-\U0001F251""]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    text = text.replace('#', '').replace('**', '').replace('*', '').replace('---', '').replace('>', '')
    return text.encode('latin-1', 'ignore').decode('latin-1')

# ─── Helper: Create BRANDED PDF ──────────────────────────
def create_pdf(destination, duration, budget, currency, content, company, contact, color):
    pdf = FPDF()
    pdf.add_page()
    
    # Header with brand color
    pdf.set_fill_color(int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
    pdf.rect(0, 0, 210, 25, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, company, ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, contact, ln=True, align="C")
    pdf.ln(5)
    
    # Title
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, f"Travel Plan: {destination}", ln=True, align="C")
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"{duration} Days | Budget: {budget} {currency}", ln=True, align="C")
    pdf.ln(5)
    
    # Content
    pdf.set_font("Arial", "", 10)
    clean = clean_for_pdf(content)
    pdf.multi_cell(0, 6, clean)
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, f"Prepared by {company} | Powered by TravelAgent AI", align="C")
    
    return bytes(pdf.output(dest="S"))

# ─── Helper: Wikipedia Image ─────────────────────────────
@st.cache_data(show_spinner=False)
def get_destination_info(destination):
    try:
        query = destination.split(',')[0].strip().replace(' ', '_')
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        r = requests.get(url, timeout=5)
        data = r.json()
        return data.get('thumbnail', {}).get('source'), data.get('extract', '')
    except:
        return None, ''

# ─── HEADER ──────────────────────────────────────────────
if logo_url:
    st.markdown(f'<div class="brand-header"><img src="{logo_url}" width="60"><div class="main-title">{company_name}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="main-title">{company_name}</div>', unsafe_allow_html=True)

st.markdown('<div class="subtitle">Smart Tourism Planning — Research, Plan & Budget in Seconds</div>', unsafe_allow_html=True)

# ─── FORM + PREVIEW ──────────────────────────────────────
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
    preferences = st.text_area("Travel Style", "local food, photography, walking tours, avoid crowds")
    
    plan_btn = st.button("Generate My Trip", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    img_url, wiki_desc = get_destination_info(destination)
    if img_url:
        st.image(img_url, use_container_width=True)
        st.caption(wiki_desc[:250] + "...")
    else:
        st.info("Enter a destination to see a preview")

# ─── RESULTS ─────────────────────────────────────────────
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
                    st.markdown(result.split("Budget")[-1])
                else:
                    st.markdown(result)
            
            with tab3:
                st.markdown("### Download Branded Itinerary")
                pdf_bytes = create_pdf(destination, duration, budget, currency, result, company_name, contact_info, brand_color)
                st.download_button(
                    "Download Branded PDF",
                    pdf_bytes,
                    f"{company_name.replace(' ', '_')}_Trip_{destination.replace(' ', '_').replace(',', '')}.pdf",
                    "application/pdf"
                )
                st.markdown("---")
                st.markdown("**Raw Markdown:**")
                st.code(result, language="markdown")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Tip: Try 'Paris, France' instead of just 'Paris'")

# ─── FOOTER ──────────────────────────────────────────────
st.markdown("---")
st.markdown(f"<div style='text-align:center; color:#9CA3AF; font-size:0.85rem;'>{company_name} | Built with TravelAgent AI</div>", unsafe_allow_html=True)
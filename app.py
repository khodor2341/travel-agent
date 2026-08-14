import streamlit as st
import requests
import re
from agents import run_trip_planner
from fpdf import FPDF
from database import save_trip, get_all_trips, get_trip, delete_trip
from visuals import get_unsplash_photos, parse_budget_data, render_budget_chart

st.set_page_config(page_title="TravelAgent AI", page_icon="✈️", layout="wide")

# ─── SIDEBAR: Brand Settings + Trip History ──────────────
with st.sidebar:
    st.markdown("### 🎨 Brand Settings")
    company_name = st.text_input("Company Name", "TravelAgent AI")
    logo_url = st.text_input("Logo URL", "", placeholder="https://your-logo.png")
    brand_color = st.color_picker("Brand Color", "#1E3A8A")
    contact_info = st.text_input("Contact / Website", "contact@travelagent.ai")
    
    st.markdown("---")
    st.markdown("### 📚 Trip History")
    
    trips = get_all_trips()
    if trips:
        for trip in trips:
            tid, dest, dur, bud, cur, created = trip
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"🌍 {dest} ({dur}d) — {created}", key=f"load_{tid}"):
                    full = get_trip(tid)
                    if full:
                        st.session_state['trip_result'] = full[6]
                        st.session_state['trip_meta'] = {
                            "destination": full[1], "duration": full[2],
                            "budget": full[3], "currency": full[4]
                        }
                        st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{tid}"):
                    delete_trip(tid)
                    st.rerun()
    else:
        st.caption("No saved trips yet.")
    
    st.markdown("---")
    st.caption("Built by Khodor | [GitHub](https://github.com/khodor2341/travel-agent)")

# ─── Dynamic CSS ─────────────────────────────────────────
st.markdown(f"""
<style>
    .main-title {{ font-size: 3rem; font-weight: 800; color: {brand_color}; }}
    .subtitle {{ font-size: 1.1rem; color: #6B7280; margin-bottom: 2rem; }}
    .stButton>button {{ background-color: {brand_color}; color: white; border-radius: 10px; padding: 0.8rem 2rem; font-weight: 600; }}
    .stButton>button:hover {{ opacity: 0.9; transform: translateY(-2px); }}
    .card {{ background: #F8FAFC; border-radius: 16px; padding: 1.5rem; border: 1px solid #E2E8F0; }}
    .map-link {{ color: #2563EB; text-decoration: none; font-size: 0.85rem; }}
    .map-link:hover {{ text-decoration: underline; }}
</style>
""", unsafe_allow_html=True)

# ─── Helpers ─────────────────────────────────────────────
def clean_for_pdf(text):
    reps = {'—': '--', '–': '-', ''': "'", ''': "'", '"': '"', '"': '"', '…': '...', '•': '-', '→': '->', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '°': ' deg'}
    for old, new in reps.items(): text = text.replace(old, new)
    emoji = re.compile("["u"\U0001F600-\U0001F64F"u"\U0001F300-\U0001F5FF"u"\U0001F680-\U0001F6FF"u"\U0001F1E0-\U0001F1FF"u"\U00002702-\U000027B0"u"\U000024C2-\U0001F251""]+", flags=re.UNICODE)
    text = emoji.sub('', text).replace('#', '').replace('**', '').replace('*', '').replace('---', '').replace('>', '')
    return text.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf(destination, duration, budget, currency, content, company, contact, color, client_name=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, company, ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, contact, ln=True, align="C")
    if client_name:
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 6, f"Prepared for: {client_name}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, f"Travel Plan: {destination}", ln=True, align="C")
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"{duration} Days | Budget: {budget} {currency}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, clean_for_pdf(content))
    pdf.set_y(-30)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, f"Prepared by {company} | Powered by TravelAgent AI", align="C")
    return bytes(pdf.output(dest="S"))

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

def add_map_links(text, destination):
    lines = text.split('\n')
    result = []
    for line in lines:
        match = re.match(r'^(\s*[\d\-:\.]+\s*)(.+?)(\s*\(.+?\))?$', line)
        if match and len(match.group(2).strip()) > 3:
            place = match.group(2).strip()
            skip = ['lunch', 'dinner', 'breakfast', 'hotel', 'transport', 'flight', 'check-in', 'check-out', 'buffer', 'free time', 'rest', 'travel', 'arrival', 'departure']
            if not any(s in place.lower() for s in skip):
                query = f"{place}, {destination.split(',')[0]}"
                maps_url = f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(query)}"
                line = f"{line} &nbsp;[<a href='{maps_url}' target='_blank' class='map-link'>🗺️ Map</a>]"
        result.append(line)
    return '\n'.join(result)

# ─── HEADER ──────────────────────────────────────────────
if logo_url:
    st.markdown(f'<div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;"><img src="{logo_url}" width="60"><div class="main-title">{company_name}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="main-title">{company_name}</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Smart Tourism Planning — Research, Plan & Budget in Seconds</div>', unsafe_allow_html=True)

# ─── FORM ────────────────────────────────────────────────
left, right = st.columns([1, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Trip Details")
    
    # ─── TEMPLATE BUTTONS ──────────────────────────────
    st.markdown("**Quick Templates:**")
    t1, t2, t3, t4, t5 = st.columns(5)
    
    with t1:
        if st.button("💑 Romantic", use_container_width=True):
            st.session_state['template_prefs'] = "romantic sunsets, fine dining, couples activities, boutique hotels, wine tasting, photography"
            st.session_state['template_budget_mult'] = 1.5
            st.rerun()
    with t2:
        if st.button("👨‍👩‍👧 Family", use_container_width=True):
            st.session_state['template_prefs'] = "kid-friendly attractions, theme parks, easy transport, family suites, interactive museums, parks"
            st.session_state['template_budget_mult'] = 1.2
            st.rerun()
    with t3:
        if st.button("🏔️ Adventure", use_container_width=True):
            st.session_state['template_prefs'] = "hiking, extreme sports, outdoor adventures, hostels, local street food, nature photography"
            st.session_state['template_budget_mult'] = 0.8
            st.rerun()
    with t4:
        if st.button("💎 Luxury", use_container_width=True):
            st.session_state['template_prefs'] = "5-star hotels, private tours, Michelin dining, spa wellness, luxury shopping, helicopter tours"
            st.session_state['template_budget_mult'] = 3.0
            st.rerun()
    with t5:
        if st.button("🎒 Budget", use_container_width=True):
            st.session_state['template_prefs'] = "hostels, street food, free attractions, public transport, walking tours, local markets"
            st.session_state['template_budget_mult'] = 0.5
            st.rerun()
    
    st.markdown("---")
    
    destination = st.text_input("Where to?", "Tokyo, Japan", placeholder="e.g. Santorini, Greece")
    client_name = st.text_input("Client Name (optional)", "", placeholder="e.g. Sarah Ahmed")
    client_email = st.text_input("Client Email (optional)", "", placeholder="For direct email share")
    c1, c2, c3 = st.columns(3)
    with c1:
        duration = st.number_input("Days", 1, 14, 3)
    with c2:
        start_date = st.date_input("Start Date", value=None)
    with c3:
        default_budget = int(2000 * st.session_state.get('template_budget_mult', 1.0))
        budget = st.number_input("Budget", 100, 50000, default_budget)
    
    currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY", "AED", "CAD"])
    preferences = st.text_area("Travel Style & Preferences", 
        value=st.session_state.get('template_prefs', "local food, photography spots, walking tours, avoid tourist traps"),
        placeholder="What do you love? Any must-haves or deal-breakers?")
    
    plan_btn = st.button("Generate My Trip", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    img_url, wiki_desc = get_destination_info(destination)
    if img_url:
        st.image(img_url, use_container_width=True)
        st.caption(wiki_desc[:250] + "...")
    else:
        st.info("Enter a destination to see a live preview from Wikipedia")

# ─── GENERATE ────────────────────────────────────────────
if plan_btn:
    if not destination.strip():
        st.error("Please enter a destination!")
    else:
        progress = st.empty()
        progress.info("🔍 Research Agent scanning... ⏳ Planning Agent building itinerary... 💰 Budget Agent crunching numbers...")
        try:
            start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
            result = run_trip_planner(destination, duration, budget, currency, preferences, start_date_str)
            progress.empty()
            st.balloons()
            st.success("Your trip is ready!")
            
            st.session_state['trip_result'] = result
            st.session_state['trip_meta'] = {
                "destination": destination, "duration": duration,
                "budget": budget, "currency": currency,
                "start_date": start_date.strftime("%Y-%m-%d") if start_date else None,
                "client_name": client_name,
                "client_email": client_email
            }
            
            save_trip(destination, duration, budget, currency, preferences, result)
            st.toast("Trip saved to history! ✅")
            
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")
            st.info("Tip: Try a more specific destination like 'Paris, France' instead of just 'Paris'")

# ─── EDITABLE OUTPUT ─────────────────────────────────────
if 'trip_result' in st.session_state:
    meta = st.session_state['trip_meta']
    result = st.session_state['trip_result']
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View & Edit", "💰 Budget & Charts", "🖼️ Gallery", "📥 Export"])
    
    with tab1:
        st.markdown("### ✏️ Edit Before Sending to Client")
        st.caption("You can modify any text below. Your changes will reflect in the PDF.")
        edited = st.text_area("Editable Itinerary", result, height=500)
        if edited != result:
            st.session_state['trip_result'] = edited
            st.toast("Changes saved! Regenerate PDF to see updates.")
        
        st.markdown("---")
        st.markdown("### 🗺️ Preview with Map Links")
        st.markdown(add_map_links(edited, meta['destination']), unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 💰 Budget Analysis")
        if "Budget" in result:
            budget_section = result.split("Budget")[-1]
            st.markdown(budget_section)
            
            budget_data = parse_budget_data(budget_section)
            if budget_data:
                chart = render_budget_chart(budget_data, meta['currency'])
                if chart:
                    st.pyplot(chart)
            else:
                st.info("Could not parse budget numbers for chart")
        else:
            st.markdown(result)
    
    with tab3:
        st.markdown("### 🖼️ Destination Gallery")
        with st.spinner("Loading photos..."):
            photos = get_unsplash_photos(meta['destination'])
        cols = st.columns(3)
        for i, photo in enumerate(photos):
            with cols[i % 3]:
                st.image(photo, use_container_width=True)
    
    with tab4:
        st.markdown("### 📄 Export Final Version")
        final_text = st.session_state.get('trip_result', result)
        pdf_bytes = create_pdf(meta['destination'], meta['duration'], meta['budget'], meta['currency'], final_text, company_name, contact_info, brand_color, meta.get('client_name', ''))
        st.download_button(
            "📥 Download Branded PDF",
            pdf_bytes,
            f"{company_name.replace(' ', '_')}_Trip_{meta['destination'].replace(' ', '_').replace(',', '')}.pdf",
            "application/pdf"
        )
        st.markdown("---")
        if meta.get('client_email'):
            subject = requests.utils.quote(f"Your Travel Plan: {meta['destination']}")
            body = requests.utils.quote(f"Hi {meta.get('client_name', 'there')},\n\nPlease find your personalized travel plan for {meta['destination']} attached.\n\nBest regards,\n{company_name}")
            st.markdown(f"[📧 Email to Client](mailto:{meta['client_email']}?subject={subject}&body={body})", unsafe_allow_html=True)
        else:
            st.caption("Add client email to enable one-click email share")
        st.markdown("---")
        st.markdown("**Share via WhatsApp:**")
        whatsapp_text = requests.utils.quote(clean_for_pdf(final_text)[:500] + f"...\n\nPlanned by {company_name}")
        st.markdown(f"[📤 Open WhatsApp](https://wa.me/?text={whatsapp_text})", unsafe_allow_html=True)

# ─── FOOTER ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center; color:#9CA3AF; font-size:0.85rem;'>"
    f"{company_name} | Built with TravelAgent AI | "
    f"<a href='https://github.com/khodor2341/travel-agent' target='_blank'>View on GitHub</a>"
    f"</div>",
    unsafe_allow_html=True
)
import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
import io
import speech_recognition as sr
import re

st.set_page_config(page_title="Voice-to-PDF Pipeline", layout="wide")
st.title("🎙️ Dual-Input Voice Data Intelligence Pipeline")

if 'items_list' not in st.session_state:
    st.session_state.items_list = []

# ==========================================
# ADVANCED COMPOUND NUMBER PARSER (Data Science Engine)
# ==========================================
def parse_indian_voice_text(text):
    text = text.lower().strip()
    
    # Clean out explicit currency signs to simplify matching
    text = re.sub(r'\b(rs|rupees|rupee|inr)\b', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Mapping table for compounding multiplier calculations
    multipliers = {
        'crore': 10000000, 'crores': 10000000,
        'lakh': 100000, 'lakhs': 100000,
        'thousand': 1000, 'thousands': 1000, 'k': 1000,
        'hundred': 100, 'hundreds': 100
    }
    
    # 1. Step A: Isolate the descriptive label characters from the number components
    # Finds where the first continuous numeric token sequence begins
    num_start_match = re.search(r'\d', text)
    if not num_start_match:
        return None
        
    start_idx = num_start_match.start()
    item_name = text[:start_idx].strip().capitalize()
    numeric_part = text[start_idx:].strip()
    
    if not item_name:
        item_name = "⚠️ ERROR: Incomplete Input"
        
    # 2. Step B: Compounding accumulation loops
    # Tokenize the numerical phrase segment (e.g., ["4", "lakh", "50", "thousand", "5", "hundred", "55"])
    tokens = numeric_part.split()
    
    total_price = 0.0
    current_number = None
    
    for token in tokens:
        # Check if the token is a direct numeric digit or a decimal float value
        if token.replace('.', '', 1).isdigit():
            if current_number is not None:
                # If we hit two numbers in a row (e.g., "... hundred 55"), accumulate the previous one
                total_price += current_number
            current_number = float(token)
        # Check if the token matches a scalar word unit
        elif token in multipliers:
            factor = multipliers[token]
            if current_number is not None:
                total_price += current_number * factor
                current_number = None
            else:
                # Edge case handling if user says just "lakh" without a leading number unit prefix
                total_price += 1.0 * factor
                
    # Add any final remaining trailing numbers (like the "55" at the very end of your string)
    if current_number is not None:
        total_price += current_number
        
    if total_price > 0:
        return {"Item Name": item_name, "Price (Rs)": total_price}
        
    return None

# ==========================================
# MULTI-INPUT AUDIO PROCESSING SIDEBAR
# ==========================================
st.sidebar.header("1. Choose Your Input Method")
input_mode = st.sidebar.radio(
    "Select Input Type:", 
    ["Live Microphone Recording", "Upload Audio File (.wav)", "Simulate Dictation Text"]
)

transcribed_text = ""

if input_mode == "Live Microphone Recording":
    audio_source_file = st.sidebar.audio_input("Record your statement here:")
    if audio_source_file is not None:
        try:
            audio_bytes = audio_source_file.read()
            if len(audio_bytes) > 100:
                recognizer = sr.Recognizer()
                with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
                    audio_data = recognizer.record(source)
                transcribed_text = recognizer.recognize_google(audio_data)
        except Exception:
            pass

elif input_mode == "Upload Audio File (.wav)":
    audio_source_file = st.sidebar.file_uploader("Upload a voice note (.wav file)", type=["wav"])
    if audio_source_file is not None:
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_source_file) as source:
                audio_data = recognizer.record(source)
            transcribed_text = recognizer.recognize_google(audio_data)
        except Exception:
            st.sidebar.error("Error parsing audio file format structure.")

else:
    transcribed_text = st.sidebar.text_input("Type dictation simulation text:", placeholder="Laptop 4 lakh 50 thousand")

# Process Captured/Simulated strings
if transcribed_text:
    st.sidebar.info(f"Captured Text Stream: \"{transcribed_text}\"")
    if st.sidebar.button("🤖 Run Audio Intelligence Engine"):
        parsed_record = parse_indian_voice_text(transcribed_text)
        if parsed_record:
            st.session_state.items_list.append(parsed_record)
            st.success(f"Added: {parsed_record['Item Name']}")
            st.rerun()
        else:
            st.sidebar.error("Could not isolate parameters from input text string.")

# ==========================================
# DATA SCIENCE CLEANSING GRID & REPORTLAB
# ==========================================
st.header("2. Data Cleansing & Validation Board")
st.write("Review system observations. Select a row checkbox on the left, press Delete to clear corrupt rows then click Apply Grid Adjustments & Recalculate")

if st.session_state.items_list:
    data_df = pd.DataFrame(st.session_state.items_list)
    edited_df = st.data_editor(data_df, num_rows="dynamic", use_container_width=True, key="grid_v7")
    
    if st.button("💾 Apply Grid Adjustments & Recalculate"):
        st.session_state.items_list = edited_df.to_dict(orient="records")
        st.success("Internal states updated!")
        st.rerun()
        
    st.markdown("---")
    st.header("3. PDF Production & Analytics Export")
    final_df = pd.DataFrame(st.session_state.items_list)
    
    if not final_df.empty:
        total_amount = final_df["Price (Rs)"].sum()
        st.metric(label="Total Aggregated Value", value=f"Rs. {total_amount:,.2f}")
        
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(200, 800, "Itemized Inventory Report")
        c.setFont("Helvetica", 12)
        y = 750
        for idx, row in final_df.iterrows():
            c.drawString(50, y, f"{idx+1}. {row['Item Name']} ----------- Rs.{row['Price (Rs)']}")
            y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y - 20, f"Grand Cumulative Total: Rs.{total_amount}")
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(label="📥 Download Clean Report PDF", data=pdf_buffer, file_name="Items_Report.pdf", mime="application/pdf")
else:
    st.info("The table data grid is empty. Input items using the sidebar.")

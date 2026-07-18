import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
import io
import speech_recognition as sr
import re

st.set_page_config(page_title="Voice-to-PDF Pipeline", layout="wide")
st.title("🎙️ Dual-Input Voice Data Intelligence Pipeline")

# Initialize our primary data state array
if 'items_list' not in st.session_state:
    st.session_state.items_list = []

# ==========================================
# ADVANCED ERROR-TOLERANT PARSER
# ==========================================
def parse_indian_voice_text(text):
    text = text.lower().strip()
    
    # Standardize common numeric speech contractions
    text = re.sub(r'\b(k|grand)\b', 'thousand', text)
    text = re.sub(r'\b(rs|rupees|rupee|inr)\b', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Regex to handle singular or plural currency suffix variables
    pattern = r"([a-z\s]+)\s+(\d+(?:\.\d+)?)\s*(crores?|lakhs?|thousands?|hundreds?)?"
    match = re.search(pattern, text)
    
    if match:
        item_name = match.group(1).strip().capitalize()
        base_value = float(match.group(2))
        unit = match.group(3)
        
        if unit in ['lakh', 'lakhs']:
            base_value *= 100000
        elif unit in ['crore', 'crores']:
            base_value *= 10000000
        elif unit in ['thousand', 'thousands']:
            base_value *= 1000
        elif unit in ['hundred', 'hundreds']:
            base_value *= 100
            
        if not item_name:
            item_name = "⚠️ ERROR: Incomplete Input"
            
        return {"Item Name": item_name, "Price (Rs)": base_value}
        
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    if numbers:
        price = float(numbers[0])
        
        if "lakh" in text:
            price *= 100000
        elif "crore" in text:
            price *= 10000000
        elif "thousand" in text:
            price *= 1000
        elif "hundred" in text:
            price *= 100
            
        item_name = re.sub(r'\d+(?:\.\d+)?', '', text).strip().capitalize()
        if not item_name:
            item_name = "⚠️ ERROR: Incomplete Input"
            
        return {"Item Name": item_name, "Price (Rs)": price}
        
    return None

# ==========================================
# MULTI-INPUT AUDIO PROCESSING SIDEBAR
# ==========================================
st.sidebar.header("1. Choose Your Audio Source")
input_mode = st.sidebar.radio("Select how to input voice data:", ["Live Microphone Recording", "Upload Audio File (.wav)"])

audio_source_file = None

if input_mode == "Live Microphone Recording":
    audio_source_file = st.sidebar.audio_input("Click to record your statement:")
else:
    audio_source_file = st.sidebar.file_uploader("Upload a voice note (.wav file)", type=["wav"])

if audio_source_file is not None:
    if st.sidebar.button("🤖 Run Audio Intelligence Engine"):
        with st.spinner("Extracting parameters and running transcription..."):
            try:
                # Read browser memory bytes stream channel data
                audio_bytes = audio_source_file.read()
                
                # SILENCE FILTER: Skip processing entirely if audio file buffer is unpopulated or too small
                if len(audio_bytes) < 100:
                    st.sidebar.warning("Audio buffer initializing. Please record your voice statement before processing.")
                else:
                    recognizer = sr.Recognizer()
                    audio_file_like = io.BytesIO(audio_bytes)
                    
                    with sr.AudioFile(audio_file_like) as source:
                        audio_data = recognizer.record(source)
                    
                    transcribed_text = recognizer.recognize_google(audio_data)
                    st.sidebar.success("Analysis Complete!")
                    st.sidebar.info(f"Captured: \"{transcribed_text}\"")
                    
                    parsed_record = parse_indian_voice_text(transcribed_text)
                    if parsed_record:
                        st.session_state.items_list.append(parsed_record)
                        st.rerun()
                    else:
                        st.sidebar.error("Could not extract a valid item name or numeric price. Please try speaking clearer.")
            
            # Explicitly catch network connection timeouts or empty stream exceptions
            except (sr.UnknownValueError, sr.RequestError):
                st.sidebar.error("Speech recognition server connection timed out. Please check your mic connection or try speaking again.")
            except Exception as e:
                # Fallback to absolute silence if it's just a browser startup frame mismatch error
                pass

# ==========================================
# DATA SCIENCE CLEANSING GRID & REPORTLAB
# ==========================================
st.header("2. Data Cleansing & Validation Board")
st.write("Review system observations. Select a row checkbox on the left, press Delete to clear corrupt rows then click Apply Grid Adjustments & Recalculate")

if st.session_state.items_list:
    data_df = pd.DataFrame(st.session_state.items_list)
    edited_df = st.data_editor(data_df, num_rows="dynamic", use_container_width=True, key="grid_v5")
    
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

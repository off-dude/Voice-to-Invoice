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
# ADVANCED INDIAN CURRENCY PARSER (Data Science Feature)
# ==========================================
def parse_indian_voice_text(text):
    text = text.lower()
    
    # 1. Regex to catch a number optionally followed by units like lakhs, crores, thousands
    pattern = r"([a-z\s]+)\s+(\d+(?:\.\d+)?)\s*(lakh|lakhs|crore|crores|thousand|thousands|rs|rupees|rupee)?"
    match = re.search(pattern, text)
    
    if match:
        item_name = match.group(1).strip().capitalize()
        base_value = float(match.group(2))
        unit = match.group(3)
        
        # Apply standard numerical multiplier logic
        if unit in ['lakh', 'lakhs']:
            base_value *= 100000
        elif unit in ['crore', 'crores']:
            base_value *= 10000000
        elif unit in ['thousand', 'thousands']:
            base_value *= 1000
            
        # Strip trailing filler words from item description strings
        item_cleaned = " ".join([w for w in item_name.split() if w not in ["rs", "rupees", "rupee", "inr"]])
        if not item_cleaned.strip():
            item_cleaned = "⚠️ ERROR: Incomplete Input"
            
        return {"Item Name": item_cleaned, "Price (Rs)": base_value}
        
    # Fallback default splitting logic matching your initial layout
    words = text.split()
    price = ""
    for w in words:
        if w.replace('.', '').isdigit():
            price = w
            break
    if price:
        item_name = " ".join([w for w in words if not w.replace(".", '').isdigit() and w not in ["rs", "rupees", "rupee"]])
        if not item_name.strip():
            item_name = "⚠️ ERROR: Incomplete Input"
        return {"Item Name": item_name.capitalize(), "Price (Rs)": float(price)}
        
    return None

# ==========================================
# 1. AUDIO CAPTURE INTERFACE PANEL
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
        with st.spinner("Extracting variables and running transcription..."):
            try:
                recognizer = sr.Recognizer()
                
                # Cloud-safe memory chunk conversion (Converts WebM formats into usable linear AudioData)
                audio_bytes = audio_source_file.read()
                audio_file_like = io.BytesIO(audio_bytes)
                
                with sr.AudioFile(audio_file_like) as source:
                    audio_data = recognizer.record(source)
                
                transcribed_text = recognizer.recognize_google(audio_data)
                st.sidebar.success("Analysis Complete!")
                st.sidebar.info(f"Captured: \"{transcribed_text}\"")
                
                # Map extracted tokens into state storage arrays
                parsed_record = parse_indian_voice_text(transcribed_text)
                if parsed_record:
                    st.session_state.items_list.append(parsed_record)
                    st.rerun()
                else:
                    st.sidebar.error("Could not parse an item name or price. Please repeat clearly.")
            except Exception as e:
                st.sidebar.error("A device decoding error occurred. Speak clearly into your mic or verify your uploaded file format.")

# ==========================================
# 2. DATA SCIENCE VALIDATION & DELETION GRID
# ==========================================
st.header("2. Data Cleansing & Validation Board")
st.write("To **DELETE** a record: select the row checkbox on the left, then hit **Delete** on your keyboard.")

if st.session_state.items_list:
    data_df = pd.DataFrame(st.session_state.items_list)
    
    # Render Streamlit advanced interactive grid
    edited_df = st.data_editor(
        data_df, 
        num_rows="dynamic", 
        use_container_width=True, 
        key="cleansing_grid"
    )
    
    # CRITICAL BUG FIX 3: Immediately save changes back to primary state memory arrays
    if st.button("💾 Apply Grid Adjustments & Recalculate"):
        st.session_state.items_list = edited_df.to_dict(orient="records")
        st.success("Internal state variables synchronized!")
        st.rerun()
        
    # ==========================================
    # 3. REPORTLAB PDF PRODUCTION LAYER
    # ==========================================
    st.markdown("---")
    st.header("3. PDF Production & Analytics Export")
    
    # We build our figures out of the freshly modified storage values
    final_df = pd.DataFrame(st.session_state.items_list)
    
    if not final_df.empty:
        total_amount = final_df["Price (Rs)"].sum()
        st.metric(label="Total Aggregated Value (INR)", value=f"Rs. {total_amount:,.2f}")
        
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(200, 800, "Itemized Inventory Report")
        
        c.setFont("Helvetica", 12)
        y = 750
        for idx, row in final_df.iterrows():
            c.drawString(50, y, f"{idx+1}. {row['Item Name']} ----------- Rs.{row['Price (Rs)']}")
            y -= 20
            if y < 50:
                c.showPage()
                y = 750
                
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y - 20, f"Grand Cumulative Total: Rs.{total_amount}")
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(
            label="📥 Download Clean Report PDF", 
            data=pdf_buffer, 
            file_name="Items_Report.pdf", 
            mime="application/pdf"
        )
    else:
        st.info("All records removed. Grid empty.")
else:
    st.info("The table data grid is empty. Use the sidebar panel tools to feed information streams.")


import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
import io
import speech_recognition as sr

st.set_page_config(page_title="Voice-to-PDF Pipeline", layout="wide")
st.title("🎙️ Dual-Input Voice Data Intelligence Pipeline")

if 'items_list' not in st.session_state:
    st.session_state.items_list = []

# ==========================================
# MULTI-INPUT AUDIO PROCESSING SIDEBAR
# ==========================================
st.sidebar.header("1. Choose Your Audio Source")
input_mode = st.sidebar.radio("Select how to input voice data:", ["Live Microphone Recording", "Upload Audio File (.wav)"])

audio_source_file = None

if input_mode == "Live Microphone Recording":
    # Captures live voice through the web browser
    audio_source_file = st.sidebar.audio_input("Click to record your statement:")
else:
    # Processes pre-recorded notes or audio files
    audio_source_file = st.sidebar.file_uploader("Upload a voice note (.wav file)", type=["wav"])

if audio_source_file is not None:
    if st.sidebar.button("🤖 Run Audio Intelligence Engine"):
        with st.spinner("Extracting parameters and running transcription..."):
            try:
                recognizer = sr.Recognizer()
                with sr.AudioFile(audio_source_file) as source:
                    audio_data = recognizer.record(source)
                
                transcribed_text = recognizer.recognize_google(audio_data)
                st.sidebar.success("Analysis Complete!")
                st.sidebar.info(f"Captured: \"{transcribed_text}\"")
                
                # Core parser logic loop
                words = transcribed_text.split()
                price = ""
                for w in words:
                    if w.replace('.', '').isdigit():
                        price = w
                        break
                
                item_name = " ".join(
                    w for w in words 
                    if not w.replace(".", '').isdigit() and w.lower() not in ["rs", "rupees", "rupee", "inr"]
                )
                
                # Flag missing item data anomalies (e.g., lone "55000")
                if not item_name.strip():
                    item_name = "⚠️ ERROR: Incomplete Input Captured"
                
                if price:
                    st.session_state.items_list.append({
                        "Item Name": item_name.strip().capitalize(),
                        "Price (Rs)": float(price)
                    })
                    st.rerun()
                else:
                    st.sidebar.error("Could not parse a numeric price from that audio statement.")
            except Exception as e:
                st.sidebar.error("An error occurred during file ingestion. Try a clear .wav file.")

# ==========================================
# DATA SCIENCE CLEANSING GRID & REPORTLAB
# ==========================================
st.header("2. Data Cleansing & Validation Board")
st.write("Review system observations. Select a row checkout box and press **Delete** to clear corrupt rows.")

if st.session_state.items_list:
    data_df = pd.DataFrame(st.session_state.items_list)
    edited_df = st.data_editor(data_df, num_rows="dynamic", use_container_width=True, key="grid_v2")
    
    if st.button("💾 Apply Grid Adjustments"):
        st.session_state.items_list = edited_df.to_dict(orient="records")
        st.success("Synchronized!")
        st.rerun()
        
    st.markdown("---")
    st.header("3. PDF Production & Analytics Export")
    final_df = pd.DataFrame(st.session_state.items_list)
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
    st.info("The table data grid is empty. Choose an entry path options in the sidebar panel.")

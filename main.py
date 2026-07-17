import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
import io

st.set_page_config(page_title="Voice-to-PDF Pipeline", layout="wide")
st.title("🎙️ Voice-to-PDF Validation & Analytics Engine")

# ==========================================
# 1. INITIALIZE DATA SESSION STATE STORAGE
# ==========================================
# This acts as our 'items' array but survives browser refreshes
if 'extracted_items' not in st.session_state:
    st.session_state.extracted_items = []

# ==========================================
# 2. AUDIO RECORDER / SIMULATOR LAYER
# ==========================================
st.sidebar.header("1. Input Control Voice Panel")
st.sidebar.write("Simulate microphone streams or upload your transcribed strings:")

# Streamlit cannot easily stream live local pyaudio/sr.Microphone on the cloud server.
# To keep your app light and working, we accept text input strings directly or uploaded files.
simulated_voice_input = st.sidebar.text_input(
    "Type or dictate text here (e.g., 'laptop 55000 rs'):", 
    placeholder="Macbook 120000 rupees"
)

if st.sidebar.button("➕ Parse and Insert Record"):
    if simulated_voice_input:
        words = simulated_voice_input.split()
        price = ""
        
        # Your exact parsing logic from your VS Code file
        for w in words:
            if w.replace('.', '').isdigit():
                price = w
                break
                
        # Clean out currency indicators
        item_name = " ".join(
            w for w in words 
            if not w.replace(".", '').isdigit() and w.lower() not in ["rs", "rupees", "rupee", "inr"]
        )
        
        # Fallback Data Science Flagging: Catch empty names (e.g. if user just says '55000')
        if not item_name.strip():
            item_name = "⚠️ ERROR: Missing Item Name"
            
        if price:
            # Append into structured memory dictionary rows
            st.session_state.extracted_items.append({
                "Item Name": item_name.strip().capitalize(),
                "Price (INR)": float(price)
            })
            st.sidebar.success(f"Parsed: {item_name} -> ₹{price}")
        else:
            st.sidebar.error("Could not extract numerical price. Try again.")

# ==========================================
# 3. USER DATA VALIDATION LAYER (Delete/Edit Section)
# ==========================================
st.header("2. Data Cleaning & Validation Board")
st.write("Review the items below. To **DELETE** an incorrect entry (like a lone number), select the row and click the **Trash Can icon** or press **Delete** on your keyboard.")

if st.session_state.extracted_items:
    # Convert data list to Dataframe for UI editing
    df_data = pd.DataFrame(st.session_state.extracted_items)
    
    # Render Streamlit's advanced data editor matrix
    # Setting num_rows="dynamic" enables row addition and deletion tools natively on the grid
    edited_df = st.data_editor(
        df_data,
        num_rows="dynamic",
        use_container_width=True,
        key="data_validation_grid"
    )
    
    # Save button to update changes back to memory storage
    if st.button("💾 Apply Grid Adjustments & Recalculate"):
        st.session_state.extracted_items = edited_df.to_dict(orient="records")
        st.success("Changes saved successfully!")
        st.rerun()
else:
    st.info("The table is empty. Type a phrase in the sidebar to populate items.")

# ==========================================
# 4. REPORTLAB PDF EXPORT GENERATOR
# ==========================================
if st.session_state.extracted_items:
    st.markdown("---")
    st.header("3. PDF Production & Analytics Export")
    
    final_df = pd.DataFrame(st.session_state.extracted_items)
    total_amount = final_df["Price (INR)"].sum()
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(label="Total Aggregated Value", value=f"₹ {total_amount:,.2f}")
        
        # ReportLab PDF compilation routine in-memory bytes channel buffer
        # This keeps the application cloud-friendly so it doesn't try writing to protected server paths
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(200, 800, "Itemized Inventory Report")
        
        c.setFont("Helvetica", 12)
        y = 750
        for idx, row in final_df.iterrows():
            c.drawString(50, y, f"{idx+1}. {row['Item Name']} ----------- Rs.{row['Price (INR)']}")
            y -= 20
            if y < 50: # Trigger basic page safety overflow break margin
                c.showPage()
                y = 750
                
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y - 20, f"Grand Cumulative Total: Rs.{total_amount}")
        c.save()
        
        # Reset file buffer pointer back to head start index position
        pdf_buffer.seek(0)
        
        st.download_button(
            label="📥 Download Clean Report PDF",
            data=pdf_buffer,
            file_name="Items_Report.pdf",
            mime="application/pdf"
        )

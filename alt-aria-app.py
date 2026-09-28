import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import io
from docx import Document
from docx.shared import Inches

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Email A11y Generator", layout="wide", page_icon="♿")

st.title("♿ Email Accessibility (A11y) Generator")
st.caption("Generate Deque-compliant Alt Text, ARIA Labels, and export to Word/Google Docs.")

# --- SIDEBAR: API KEY CONFIGURATION ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

# --- HELPER FUNCTION: CREATE WORD DOC ---
def create_word_doc(a11y_data, original_image):
    doc = Document()
    doc.add_heading('Accessibility A11y Documentation', 0)
    
    # Create Table
    table = doc.add_table(rows=1, cols=5)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    headers = ['Section of Email', 'Block Description', 'Visual', 'Alt Text', 'ARIA Label']
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        
    img_width, img_height = original_image.size
    
    # Populate Rows
    for row_data in a11y_data:
        row_cells = table.add_row().cells
        row_cells[0].text = row_data.get("section", "—")
        row_cells[1].text = row_data.get("description", "—")
        
        # Handle Image Slicing for Word Doc
        box = row_data.get("box_2d")
        if box and len(box) == 4:
            ymin, xmin, ymax, xmax = box
            left = (xmin / 1000.0) * img_width
            top = (ymin / 1000.0) * img_height
            right = (xmax / 1000.0) * img_width
            bottom = (ymax / 1000.0) * img_height
            
            cropped_slice = original_image.crop((left, top, right, bottom))
            
            # Save slice to memory to insert into Word Doc
            img_stream = io.BytesIO()
            cropped_slice.save(img_stream, format='PNG')
            img_stream.seek(0)
            
            paragraph = row_cells[2].paragraphs[0]
            run = paragraph.add_run()
            run.add_picture(img_stream, width=Inches(1.2)) # Scale image for Word cell
        else:
            row_cells[2].text = "—"
            
        row_cells[3].text = row_data.get("alt_text", "n/a")
        row_cells[4].text = row_data.get("aria_label", "n/a")
        
    # Save document to memory
    doc_stream = io.BytesIO()
    doc.save(doc_stream)
    doc_stream.seek(0)
    return doc_stream

# --- INPUT SECTION ---
col_left, col_right = st.columns([1, 1])

with col_left:
    uploaded_file = st.file_uploader("1. Upload Email Proof (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

with col_right:
    developer_notes = st.text_area(
        "2. Custom Callouts / Build Context", 
        height=150,
        placeholder="e.g.,\n- Hero is an animated GIF\n- Module 2 is a Movable Ink block"
    )

if uploaded_file and api_key:
    image = Image.open(uploaded_file)
    img_width, img_height = image.size
    
    st.divider()
    if st.button("🚀 Generate A11y Table", type="primary"):
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro', generation_config={"response_mime_type": "application/json"})
        
        prompt = f"""
        You are an expert Accessibility (A11y) Specialist. Analyze this email proof and generate data for a strict Deque-compliant A11y table.

        DEVELOPER CALLOUTS: {developer_notes if developer_notes else "None provided."}

        RULES:
        1. Decorative Lifestyle Photos: SKIP ROW completely unless it contains incidental text or an imposed brand logo.
        2. Essential Graphics & Logos: Provide clear, descriptive Alt Text.
        3. ARIA Labels: Must literally match the exact text in the button or link.
        4. Unclickable Graphics: ARIA Label must be "n/a - not clickable".
        5. Movable Ink: Group into a single row, set Block Description to "Creative Optimizer", generalized Alt/ARIA text.
        6. Footers: Group entire text links into a single row.
        7. Visual Bounding Boxes: Provide normalized coordinates [ymin, xmin, ymax, xmax] (0 to 1000 scale).

        Return a JSON array containing objects with these exact keys:
        [
          {{"section": "...", "description": "...", "box_2d": [ymin, xmin, ymax, xmax], "alt_text": "...", "aria_label": "..."}}
        ]
        """

        with st.spinner("Analyzing email structure, extracting ARIA labels, and slicing image regions..."):
            try:
                response = model.generate_content([prompt, image])
                a11y_data = json.loads(response.text)
                
                st.success("Analysis Complete!")
                
                # --- GENERATE WORD DOC IN BACKGROUND ---
                word_file = create_word_doc(a11y_data, image)
                
                # --- SHOW DOWNLOAD BUTTON ---
                st.download_button(
                    label="📄 Download as Word Document (Upload to Google Drive)",
                    data=word_file,
                    file_name="A11y_Documentation.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary"
                )
                
                st.subheader("Preview:")
                for row in a11y_data:
                    st.write(f"**{row.get('section')}** | {row.get('alt_text')} | {row.get('aria_label')}")
                    
            except Exception as e:
                st.error(f"Failed to generate documentation: {str(e)}")

elif not api_key and uploaded_file:
    st.warning("Please enter your Gemini API Key in the sidebar to proceed.")

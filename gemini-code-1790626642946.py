import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Email A11y Generator", layout="wide", page_icon="♿")

st.title("♿ Email Accessibility (A11y) Generator")
st.caption("Generate Deque-compliant Alt Text, ARIA Labels, and auto-cropped Visual Slices from email proofs.")

# --- SIDEBAR: API KEY CONFIGURATION ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
st.sidebar.markdown("[Get a free Gemini API Key here](https://aistudio.google.com/)")

# --- INPUT SECTION ---
col_left, col_right = st.columns([1, 1])

with col_left:
    uploaded_file = st.file_uploader("1. Upload Email Proof (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

with col_right:
    developer_notes = st.text_area(
        "2. Custom Callouts / Build Context", 
        height=150,
        placeholder="e.g.,\n- Hero is an animated GIF\n- Module 2 is a Movable Ink Creative Optimizer block\n- Footer is live text"
    )

if uploaded_file and api_key:
    # Load Image
    image = Image.open(uploaded_file)
    img_width, img_height = image.size
    
    st.divider()
    st.subheader("Uploaded Proof Preview")
    st.image(image, caption=f"Loaded Image ({img_width}x{img_height}px)", width=350)
    
    if st.button("🚀 Generate A11y Table & Visual Slices", type="primary"):
        # Configure Gemini Client
        genai.configure(api_key=api_key)
        
        # Use Gemini 1.5 Pro with forced JSON output
        model = genai.GenerativeModel(
            model_name='gemini-1.5-pro',
            generation_config={"response_mime_type": "application/json"}
        )
        
        # --- SYSTEM PROMPT (Deque Standards + Custom Context) ---
        prompt = f"""
        You are an expert Accessibility (A11y) Specialist. Analyze this email proof and generate data for a strict Deque-compliant A11y table.

        DEVELOPER CALLOUTS / BUILD CONTEXT:
        {developer_notes if developer_notes else "None provided. Rely solely on visual inspection."}

        ACCESSIBILITY RULES:
        1. Decorative Lifestyle Photos: SKIP ROW completely if it is purely a background/lifestyle photo without text or logos. 
           EXCEPTION: If a lifestyle photo contains incidental text important to the photo or an imposed brand logo, INCLUDE IT with descriptive Alt Text.
        2. Essential Graphics & Logos: Provide clear, descriptive Alt Text.
        3. ARIA Labels: Must literally match the exact text in the button or link in the exact word order.
        4. Unclickable Graphics: If an element is a graphic but not a link, set ARIA Label to "n/a - not clickable".
        5. Dynamic Content (Movable Ink / Creative Optimizer): Group the block into a single row. Set Block Description to "Creative Optimizer", and write generalized Alt/ARIA text that covers dynamic variations.
        6. Footers: Group entire text links into a single row.
        7. Visual Bounding Boxes: Provide normalized coordinates `[ymin, xmin, ymax, xmax]` on a scale of 0 to 1000 for each visual row.

        Return a JSON array containing objects with these exact keys:
        [
          {{
            "section": "Section Name (e.g. Hero Header, Module 1)",
            "description": "Block Description (e.g. CTA Button, Creative Optimizer)",
            "box_2d": [ymin, xmin, ymax, xmax],
            "alt_text": "Alt Text",
            "aria_label": "ARIA Label"
          }}
        ]
        """

        with st.spinner("Analyzing email structure, extracting ARIA labels, and slicing image regions..."):
            try:
                # Query Gemini
                response = model.generate_content([prompt, image])
                a11y_data = json.loads(response.text)
                
                st.success("Analysis Complete!")
                st.subheader("Generated Accessibility Documentation")

                # Table Header
                h1, h2, h3, h4, h5 = st.columns([1.5, 2, 2.5, 2.5, 2.5])
                h1.markdown("**Section of Email**")
                h2.markdown("**Block Description**")
                h3.markdown("**Visual Slice**")
                h4.markdown("**Alt Text**")
                h5.markdown("**ARIA Label**")
                st.divider()

                # Render Data Rows
                for row in a11y_data:
                    c1, c2, c3, c4, c5 = st.columns([1.5, 2, 2.5, 2.5, 2.5])
                    
                    c1.write(row.get("section", "—"))
                    c2.write(row.get("description", "—"))
                    
                    # Process & Display Image Slice
                    box = row.get("box_2d")
                    if box and len(box) == 4:
                        ymin, xmin, ymax, xmax = box
                        left = (xmin / 1000.0) * img_width
                        top = (ymin / 1000.0) * img_height
                        right = (xmax / 1000.0) * img_width
                        bottom = (ymax / 1000.0) * img_height
                        
                        cropped_slice = image.crop((left, top, right, bottom))
                        c3.image(cropped_slice, use_container_width=True)
                    else:
                        c3.write("—")

                    c4.code(row.get("alt_text", "n/a"), language=None)
                    c5.code(row.get("aria_label", "n/a"), language=None)
                    st.divider()

            except Exception as e:
                st.error(f"Failed to generate documentation: {str(e)}")

elif not api_key and uploaded_file:
    st.warning("Please enter your Gemini API Key in the sidebar to proceed.")
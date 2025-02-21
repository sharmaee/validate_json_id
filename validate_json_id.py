import streamlit as st
import json
import re

def clean_id(original_id):
    """
    Takes an original id string and:
      - lowers all letters,
      - removes spaces,
      - removes all special characters except underscore,
      - returns the cleaned id.
    """
    # Lowercase
    new_id = original_id.lower()
    # Remove spaces
    new_id = new_id.replace(" ", "")
    # Remove all characters except a–z and underscore
    new_id = re.sub(r'[^a-z_]', '', new_id)
    return new_id

def highlight_ids_in_text(original_text, invalid_ids):
    """
    Highlights invalid IDs in the original JSON text using markdown/HTML.
    'invalid_ids' is a dictionary mapping original_id -> reason (or "duplicate"/"invalid chars").
    
    We'll insert HTML <span> tags around each invalid ID so it displays in red in Streamlit.
    Note: This is a simple approach that does naive string replacement.  If you have the same text
          in multiple places (not just in the "id" field), it might highlight those too.
    """
    highlighted_text = original_text
    for orig_id, reason in invalid_ids.items():
        # We'll do a simple replace. If the original text contains the string "id": "orig_id",
        # we highlight `orig_id`.  We anchor on quotes to reduce risk of partial replacements.
        
        # Construct a highlight span
        span = f"<span style='background-color: yellow; color: red;' title='{reason}'>{orig_id}</span>"
        
        # Replace the exact occurrence of `orig_id` with the highlighted span
        # We also check for bounding quotes to reduce false positives.
        highlighted_text = highlighted_text.replace(f"\"{orig_id}\"", f"\"{span}\"")
    return highlighted_text

def main():
    st.title("ID Validation & Correction for JSON")

    st.write("""
    1. Paste your JSON in the text area below.  
    2. Click **"Validate & Correct"**.  
    3. The app will:  
       - Check if IDs are unique,  
       - Ensure IDs only have lowercase letters and underscores,  
       - Remove any invalid characters,  
       - Highlight incorrect/duplicate IDs in the original text,  
       - Output a corrected JSON.  
    """)

    original_text = st.text_area("Paste your JSON here:", height=400)

    if st.button("Validate & Correct"):
        if not original_text.strip():
            st.error("Please provide a non-empty JSON input.")
            return

        try:
            data = json.loads(original_text)
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
            return

        if "objects" not in data or not isinstance(data["objects"], list):
            st.error("JSON must contain a top-level 'objects' array.")
            return

        cleaned_ids = set()
        invalid_ids = {}  # mapping of original_id -> reason
        # We'll store (original_id -> new_id) so we can highlight.
        id_map = {}

        for obj in data["objects"]:
            if "id" in obj:
                orig_id = obj["id"]
                new_id = clean_id(orig_id)

                # Check if something changed:
                if new_id != orig_id:
                    invalid_ids[orig_id] = "invalid characters or uppercase"

                # Check duplicates
                if new_id in cleaned_ids:
                    # We won't automatically rename duplicates, but let's note it
                    invalid_ids[orig_id] = invalid_ids.get(orig_id, "") + (" (duplicate)" if invalid_ids.get(orig_id) else "duplicate")
                cleaned_ids.add(new_id)

                # Assign the corrected ID back
                obj["id"] = new_id
                id_map[orig_id] = new_id

        # Now highlight in the original text if needed
        if invalid_ids:
            st.markdown("### Invalid or Duplicate IDs Found (highlighted below)")
            st.write("Hover over a highlighted ID to see the reason.")

            # Convert the original text to a form with HTML highlights
            highlighted_text = highlight_ids_in_text(original_text, invalid_ids)
            # Display using unsafe_allow_html (since we inserted HTML spans):
            st.markdown(highlighted_text, unsafe_allow_html=True)
        else:
            st.markdown("### All IDs look good! No invalid or duplicate IDs found.")
            st.text_area("Original JSON", original_text, height=300)

        # Show the corrected JSON
        corrected_json_str = json.dumps(data, indent=2)
        st.markdown("### Corrected JSON")
        st.text_area("Corrected JSON Output", corrected_json_str, height=300)

        # Optionally, provide a download button for the corrected JSON:
        st.download_button(
            label="Download Corrected JSON",
            data=corrected_json_str,
            file_name="corrected.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()

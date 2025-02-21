import streamlit as st
import json
import re

def clean_id(original_id):
    """
    Takes an original id string and:
      - lowers all letters,
      - removes spaces,
      - removes all special characters except underscore,
      - now ALLOWS digits (0-9),
      - returns the cleaned id.
    """
    # Lowercase
    new_id = original_id.lower()
    # Remove spaces
    new_id = new_id.replace(" ", "")
    # Remove all characters except a–z, 0–9, and underscore
    new_id = re.sub(r'[^a-z0-9_]', '', new_id)
    return new_id

def highlight_ids_in_text(original_text, invalid_ids):
    """
    Highlights invalid IDs in the original JSON text by surrounding them
    with a <span>, and appending the reason in text ("### reason ###").
    'invalid_ids' is a dict mapping original_id -> reason string(s).

    Note: This does naive string replacement, which works if the 'id'
    only appears in contexts like "id": "..." in your JSON.
    """
    highlighted_text = original_text
    for orig_id, reason in invalid_ids.items():
        # Construct the highlight text: "orig_id ### reason ###"
        highlight_str = f"{orig_id} ### {reason} ###"
        span = f"<span style='background-color: yellow; color: red;'>{highlight_str}</span>"

        # Replace the exact occurrence of `orig_id` with the new string in quotes
        highlighted_text = highlighted_text.replace(
            f"\"{orig_id}\"",
            f"\"{span}\""
        )
    return highlighted_text

def main():
    st.title("ID Validation & Correction for JSON (Letters, Digits, Underscores)")

    st.write("""
    1. Paste your JSON in the text area below.  
    2. Click **"Validate & Correct"**.  
    3. The app will:  
       - Check if IDs are unique  
       - Convert uppercase letters to lowercase  
       - Remove spaces and any special characters (except underscore)  
       - **Allow digits (0–9)**  
       - Highlight incorrect or duplicate IDs in the original text  
       - Output a corrected JSON  
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
        invalid_ids = {}  # { original_id: reason_string }

        for obj in data["objects"]:
            if "id" in obj:
                orig_id = obj["id"]
                new_id = clean_id(orig_id)

                # If cleaning changed the ID, consider it invalid for some reason
                if new_id != orig_id:
                    invalid_reason = "invalid characters or uppercase"
                else:
                    invalid_reason = ""

                # Check for duplicates
                if new_id in cleaned_ids:
                    if invalid_reason:
                        invalid_reason += " (duplicate)"
                    else:
                        invalid_reason = "duplicate"

                if invalid_reason:
                    invalid_ids[orig_id] = invalid_reason

                cleaned_ids.add(new_id)
                obj["id"] = new_id  # Set the corrected ID

        # Highlight in the original text if needed
        if invalid_ids:
            st.markdown("### Invalid or Duplicate IDs Found")
            st.write("IDs with issues are highlighted in yellow below. The reason is shown next to them.")
            highlighted_text = highlight_ids_in_text(original_text, invalid_ids)
            st.markdown(highlighted_text, unsafe_allow_html=True)
        else:
            st.markdown("### All IDs look good!")
            st.text_area("Original JSON", original_text, height=300)

        # Show the corrected JSON
        corrected_json_str = json.dumps(data, indent=2)
        st.markdown("### Corrected JSON")
        st.text_area("Corrected JSON Output", corrected_json_str, height=300)

        # Optional download button
        st.download_button(
            label="Download Corrected JSON",
            data=corrected_json_str,
            file_name="corrected.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()

import io
import re
import pandas as pd
from rapidfuzz import fuzz, process
import streamlit as st


def load_file(file):
  """Safely load uploaded CSV or Excel files with error handling."""
  try:
    if file.name.endswith(".csv"):
      return pd.read_csv(file, dtype=str)
    else:
      return pd.read_excel(file, dtype=str)
  except Exception as e:
    st.error(f"Error reading file {file.name}: {e}")
    return None


def clean_text(text):
  text = str(text).upper()
  text = re.sub(r"[^A-Z0-9 ]", "", text)
  return text.strip()


def clean_hs_code(code):
  if pd.isna(code):
    return ""
  code = str(code).strip()
  if code.endswith(".0"):
    code = code[:-2]
  if code.endswith("."):
    code = code[:-1]
  code = re.sub(r"\D", "", code)
  if len(code) > 10:
    code = code[:10]
  return code


def run():
  st.subheader("📊 HS Code Validator & Suggestion Tool")

  col1, col2 = st.columns(2)

  with col1:
    # Upload Client
    client_file = st.file_uploader(
        "**Upload Client File**", type=["xlsx", "xls", "csv"]
    )

  with col2:
    # Upload Master
    master_file = st.file_uploader(
        "**Upload Master File**", type=["xlsx", "xls", "csv"]
    )

  st.markdown("---")
  st.caption("© 2026 ACB Toolkit | Developed by IT Department")

  if client_file and master_file:
    client_df = load_file(client_file)
    master_df = load_file(master_file)

    if client_df is None or master_df is None:
      st.stop()

    # Column validation
    if "description" not in client_df.columns:
      st.error("Client file missing required column: 'description'")
      st.stop()
    if "description" not in master_df.columns:
      st.error("Master file missing required column: 'description'")
      st.stop()
    if "harmonized_code" not in master_df.columns:
      st.error("Master file must contain 'harmonized_code'")
      st.stop()

    # Clean text data for matching helper columns
    client_df["_clean_desc"] = client_df["description"].apply(clean_text)
    master_df["_clean_desc"] = master_df["description"].apply(clean_text)
    master_df["_clean_code"] = master_df["harmonized_code"].apply(
        clean_hs_code
    )

    st.subheader("Preview - Files Uploaded Successfully")
    col1, col2 = st.columns(2)
    with col1:
      st.text("Client File Preview")
      st.dataframe(client_df.drop(columns=["_clean_desc"]).head(3))
    with col2:
      st.text("Master File Preview")
      st.dataframe(
          master_df.drop(columns=["_clean_desc", "_clean_code"]).head(3)
      )

    if st.button("Run Suggestion & Cross-Check", type="primary"):
      with st.spinner(
          "Cross-checking client descriptions with Master Database..."
      ):
        # Build master dictionaries mapping clean descriptions to codes and original descriptions
        master_dict = dict(
            zip(master_df["_clean_desc"], master_df["_clean_code"])
        )
        master_desc_dict = dict(
            zip(master_df["_clean_desc"], master_df["description"])
        )
        master_choices = list(master_dict.keys())

        suggested_codes = []
        suggested_descriptions = []
        verification_statuses = []

        HIGH_CONFIDENCE = 90
        LOW_CONFIDENCE = 80

        progress_bar = st.progress(0)
        total_rows = len(client_df)

        for idx, row in client_df.iterrows():
          desc = row["_clean_desc"]

          matched_code = ""
          matched_original_desc = ""
          score = 0
          status = "NO MATCH"

          if desc and len(desc) >= 3:
            match = process.extractOne(
                desc, master_choices, scorer=fuzz.token_set_ratio
            )
            if match:
              matched_desc, score, _ = match
              if score >= LOW_CONFIDENCE:
                matched_code = master_dict.get(matched_desc, "")
                matched_original_desc = master_desc_dict.get(matched_desc, "")

          # Determine status without modifying original client data
          if matched_code:
            suggested_codes.append(matched_code)
            suggested_descriptions.append(matched_original_desc)
            if score >= HIGH_CONFIDENCE:
              status = "MATCH (High Confidence)"
            else:
              status = "REVIEW (Low Confidence Match)"
          else:
            suggested_codes.append("")
            suggested_descriptions.append("")
            status = "NO MATCH"

          verification_statuses.append(status)

          if total_rows > 0:
            progress_bar.progress(min((idx + 1) / total_rows, 1.0))

        # Drop temporary helper column and append suggested columns in order
        client_df = client_df.drop(columns=["_clean_desc"])
        client_df["suggested_hscode"] = suggested_codes
        client_df["suggested_description"] = suggested_descriptions
        client_df["verification_status"] = verification_statuses

        st.session_state["processed_client_df"] = client_df

    # Display results if processed
    if "processed_client_df" in st.session_state:
      st.success("Suggestion process completed successfully!")
      st.subheader(
          "📋 Final Output (Original Data & Unnamed Columns Preserved)"
      )
      st.dataframe(st.session_state["processed_client_df"])

      # Export single consolidated file
      output = io.BytesIO()
      with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state["processed_client_df"].to_excel(
            writer, index=False, sheet_name="Invoice"
        )

      st.download_button(
          label="Download Excel File with Suggestions",
          data=output.getvalue(),
          file_name=(
              "Defender_Industries_Ground_HS_Validation_"
              f"{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.xlsx"
          ),
          mime=(
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          ),
      )


if __name__ == "__main__":
  run()
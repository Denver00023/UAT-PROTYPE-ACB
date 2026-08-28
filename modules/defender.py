import streamlit as st
import pandas as pd
import io
import re
from rapidfuzz import process, fuzz


def run():

    st.subheader("📊 HS Code Validator")

    # Upload files
    client_file = st.file_uploader("**Upload Client File**", type=["xlsx", "xls", "csv"])
    master_file = st.file_uploader("**Upload Master File**", type=["xlsx", "xls", "csv"])

    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")

    # LOAD FILE (SAFE)
    
    def load_file(file):
        if file.name.endswith(".csv"):
            return pd.read_csv(file, dtype=str)
        else:
            return pd.read_excel(file, dtype=str)

    # CLEAN TEXT
    
    def clean_text(text):
        text = str(text).upper()
        text = re.sub(r'[^A-Z0-9 ]', '', text)
        return text.strip()

    # CLEAN HS CODE
    
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

    # VALIDATE HS CODE
    
    def validate_hs(code):
        if len(code) == 0:
            return "MISSING"
        elif not code.isdigit():
            return "INVALID"
        elif len(code) > 10:
            return "TOO LONG"
        else:
            return "VALID"

    # MAIN PROCESS
    
    if client_file and master_file:

        client_df = load_file(client_file)
        master_df = load_file(master_file)

        # Column validation
        required_cols = ["description"]
        for col in required_cols:
            if col not in client_df.columns:
                st.error(f"Client file missing column: {col}")
                st.stop()
            if col not in master_df.columns:
                st.error(f"Master file missing column: {col}")
                st.stop()

        if "harmonized_code" not in client_df.columns:
            client_df["harmonized_code"] = ""

        if "harmonized_code" not in master_df.columns:
            st.error("Master file must contain 'harmonized_code'")
            st.stop()

        # Clean data
        client_df["description"] = client_df["description"].apply(clean_text)
        master_df["description"] = master_df["description"].apply(clean_text)

        client_df["harmonized_code"] = client_df["harmonized_code"].apply(clean_hs_code)
        master_df["harmonized_code"] = master_df["harmonized_code"].apply(clean_hs_code)

        client_df["suggested_hscode"] = ""
        client_df["hs_status"] = client_df["harmonized_code"].apply(validate_hs)

        st.subheader("Preview - Client File")
        st.dataframe(client_df.head())

        st.subheader("Preview - Master File")
        st.dataframe(master_df.head())

        # Matching
        master_choices = master_df["description"].tolist()

        def find_match(desc):
            match = process.extractOne(desc, master_choices, scorer=fuzz.token_set_ratio)

            if match:
                matched_desc, score, _ = match

                if score >= 80:
                    matched_code = master_df.loc[
                        master_df["description"] == matched_desc,
                        "harmonized_code"
                    ].values[0]

                    return matched_code, score

            return None, 0

        HIGH_CONFIDENCE = 90
        LOW_CONFIDENCE = 80

        audit_logs = []

        for idx, row in client_df.iterrows():
            original_code = row["harmonized_code"]
            desc = row["description"]

            matched_code, score = find_match(desc)

            if matched_code:
                client_df.loc[idx, "suggested_hscode"] = matched_code

            if matched_code and score >= HIGH_CONFIDENCE:
                client_df.loc[idx, "harmonized_code"] = matched_code
                decision = "AUTO-UPDATED"

            elif matched_code and score >= LOW_CONFIDENCE:
                decision = "REVIEW"

            else:
                decision = "NO MATCH"

            audit_logs.append({
                "row": idx + 1,
                "sku": row.get("sku", ""),
                "description": desc,
                "decision": decision,
                "match_score": score,
                "old_hscode": original_code,
                "suggested_hscode": matched_code if matched_code else "",
                "final_hscode": client_df.loc[idx, "harmonized_code"]
            })

        audit_df = pd.DataFrame(audit_logs)

        client_df["hs_status"] = client_df["harmonized_code"].apply(validate_hs)

        # Display
        st.subheader("Final Updated Data")
        st.dataframe(client_df)

        st.subheader("Audit Log")
        st.dataframe(audit_df)

        st.subheader("Rows Needing Review")
        review_df = audit_df[audit_df["decision"] == "REVIEW"]
        st.dataframe(review_df)

        # Export
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            client_df.to_excel(writer, index=False, sheet_name='Updated_Data')
            audit_df.to_excel(writer, index=False, sheet_name='Audit_Log')
            review_df.to_excel(writer, index=False, sheet_name='For_Review')

        st.download_button(
            label="Download Combined Excel File",
            data=output.getvalue(),
            file_name=f"Defender_Industries_Ground_HS_Validation{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
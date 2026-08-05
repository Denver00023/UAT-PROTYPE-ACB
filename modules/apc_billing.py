import streamlit as st
import pandas as pd
import io


def run():

    # HEADER
    st.subheader("📦 APC BILLING DETAIL REPORT")

    st.caption("CANDATA REPORT + SFTP = DETAIL REPORT TEMPLATE")

    # FINAL OUTPUT STRUCTURE

    FINAL_COLUMNS = [
        "Transaction Number",
        "Product Description",
        "CCI Line#",
        "Country of Origin",
        "Tariff Treatment",
        "Quantity",
        "Port Number",
        "Vendor Name",
        "Value For (CAD)",
        "USD",
        "Classification",
        "Duty Rate",
        "Customs Duty (CAD)",
        "GST (CAD)",
        "Provincial Sales Tax (CAD)",
        "Surtax (CAD)",
        "HST (CAD)",
        "Payment Terms",
        "Cargo Control Number",
        "Order Number",
        "Bill of Lading",
        "Consignee",
        "Consignee Address",
        "Consignee City",
        "Consignee Postal Code",
        "Consignee Province",
        "GST Rate",
        "PST Rate",
        "HST Rate",
        "APC Number",
        "Vendor Code",
        "Receptacle Number",
        "Exchange Rate"
    ]

    # FILE UPLOAD

    col1, col2 = st.columns(2)

    with col1:
        candata_file = st.file_uploader("Upload CANDATA File", type=["xlsx", "csv"])

    with col2:
        sftp_file = st.file_uploader("Upload SFTP File", type=["xlsx", "csv"])

    mawb_input = st.text_input(
        "MAWB #",
        placeholder="123-45678901"
        )
    st.caption("Note: Please enter MAWB before uploading files. These will be used in the output filename.")

    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")

    # RUN BUTTON

    if st.button("🚀 Process Files"):

        if not candata_file or not sftp_file:
            st.error("Please upload both CANDATA and SFTP files.")
            st.stop()

        try:

            # LOAD DATA
            def load_file(file):
                if file.name.endswith(".csv"):
                    return pd.read_csv(file)
                return pd.read_excel(file)
            
            candata_df = load_file(candata_file).fillna("")
            sftp_df = load_file(sftp_file).fillna("")

            candata_df["Transaction Number"] = candata_df["Transaction Number"].astype(str).str.replace(".0", "", regex=False)

            candata_df.columns = candata_df.columns.str.strip()
            sftp_df.columns = sftp_df.columns.str.strip()

            def fix_hs_code(col):
                return (
                col.astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
                .str.zfill(10)   # ensures 10-digit HS code
                )

            if "Classification" in candata_df.columns:
                candata_df["Classification"] = fix_hs_code(candata_df["Classification"])

            if "Item HS Code" in sftp_df.columns:
                sftp_df["Item HS Code"] = fix_hs_code(sftp_df["Item HS Code"])

            # CANDATA MAPPING
            candata_map = {
                "Transaction Number": "Transaction Number",
                "Product Description": "Product Description",
                "CCI Line#": "CCI Line#",
                "Country of Origin": "Country of Origin",
                "Tariff Treatment": "Tariff Treatment",
                "Quantity": "Quantity",
                "Port Number": "Port Number",
                "Vendor Name": "Vendor Name",
                "Value For Duty (CAD)": "Value For (CAD)",
                "USD": "USD", # Assuming the CANDATA file has a column named "USD" for the value.
                "Classification": "Classification",
                "Duty Rate": "Duty Rate",
                "Customs Duty (CAD)": "Customs Duty (CAD)",
                "GST (CAD)": "GST (CAD)",
                "Provincial Sales Tax (CAD)": "HST (CAD)",
                "Surtax (CAD)": "Surtax (CAD)",
                "Payment Terms": "Payment Terms",
                "Bill of Lading": "Bill of Lading",
                "Cargo Control Number":"Cargo Control Number",
                "Order Number":"Order Number",
                "Consignee": "Consignee",
                "Consignee Address": "Consignee Address",
                "Consignee City": "Consignee City",
                "Consignee Postal Code": "Consignee Postal Code",
                "Consignee Province": "Consignee Province",
                "GST Rate": "GST Rate"
            }

            candata_out = pd.DataFrame()

            for src, tgt in candata_map.items():
                if src in candata_df.columns:
                    candata_out[tgt] = candata_df[src]

            # SFTP MAPPING
            sftp_out = pd.DataFrame()

            sftp_map = {
                "Tracking Number/Package Barcode":"Cargo Control Number",
                "Tracking Number/Package Barcode":"Order Number",
                "Shipper": "Vendor Name",
                "Country Of Origin": "Country of Origin",
                "Consignee": "Consignee",
                "Consignee Address1": "Consignee Address",
                "Consignee City": "Consignee City",
                "Consignee Province": "Consignee Province",
                "Consignee Zip": "Consignee Postal Code",
                "Item Description": "Product Description",
                "Item HS Code": "Classification",
                "Item Quantity": "Quantity",
                "USD": "USD", # Assuming the SFTP file has a column named "USD" for the value.
                "CAD": "Value For (CAD)", # Assuming the SFTP file has a column named "CAD" for the value.
                
            }

            for src, tgt in sftp_map.items():
                if src in sftp_df.columns:
                    sftp_out[tgt] = sftp_df[src]

            # Tracking mapping
            if "Tracking Number/Package Barcode" in sftp_df.columns:
                sftp_out["Cargo Control Number"] = sftp_df["Tracking Number/Package Barcode"]
                sftp_out["Order Number"] = sftp_df["Tracking Number/Package Barcode"]

            # REMOVE MATCHED RECORDS

            # Normalize values
            candata_orders = (
                candata_out["Order Number"]
                .astype(str)
                .str.strip()
            )

            sftp_tracking = (
                sftp_df["Tracking Number/Package Barcode"]
                .astype(str)
                .str.strip()
            )

            # Remove SFTP rows that already exist in Candata
            sftp_out = sftp_out[
                ~sftp_tracking.isin(candata_orders)
            ].copy()

            # Unique values only
            candata_unique = set(candata_orders.unique())
            sftp_unique = set(sftp_tracking.unique())   

                # Match count
            match_count = len(candata_unique.intersection(sftp_unique))

                # No match count
            no_match_count = len(sftp_unique - candata_unique)

                # Show counts in Streamlit
            metric_col1, metric_col2 = st.columns(2)

            with metric_col1:
                st.metric(
                    label="✅ Match Found (Skipped from SFTP)",
                    value=match_count
                    )

            with metric_col2:
                st.metric(
                    label="📦 No Match (Included from SFTP)",
                    value=no_match_count
                    )
                
            # MERGE LOGIC (IMPORTANT)

            final_df = candata_out.copy()

            # INSERT BLANK SEPARATOR ROW

            blank_row = pd.DataFrame([{col: "" for col in FINAL_COLUMNS}])

            final_df = pd.concat([final_df, blank_row], ignore_index=True)

            # ADD SFTP DATA AFTER BLANK ROW
            final_df = pd.concat([final_df, sftp_out], ignore_index=True)

            # FINAL STRUCTURE ENFORCEMENT

            for col in FINAL_COLUMNS:
                if col not in final_df.columns:
                    final_df[col] = ""

            final_df = final_df[FINAL_COLUMNS]

            DEFAULT_VALUES = {
                "Provincial Sales Tax (CAD)":"0",
                "Surtax (CAD)": "0"
            }
            
            HST_MAP = {
                "NB": 15,
                "NL": 15,
                "NS": 14,
                "ON": 13,
                "PE": 15,
            }
            
            if "Consignee Province" in final_df.columns:
                    
                    final_df["Consignee Province"] = final_df["Consignee Province"].astype(str).str.upper().str.strip()

                    final_df["HST Rate"] = final_df["Consignee Province"].map(HST_MAP)
                    final_df["HST Rate"] = final_df["HST Rate"].fillna("")
            
            if "HST (CAD)" in final_df.columns:

                # Convert HST amount to numeric
                final_df["HST (CAD)"] = pd.to_numeric(final_df["HST (CAD)"],errors="coerce").fillna(0)

                # If HST amount is 0 -> HST Rate should also be 0
                final_df.loc[final_df["HST (CAD)"] == 0,"HST Rate"] = 0

                # Fill remaining blanks
                final_df["HST Rate"] = final_df["HST Rate"].fillna(0)

            for col, default_value in DEFAULT_VALUES.items():

                if col in final_df.columns:

                    final_df[col] = final_df[col].replace("", pd.NA)
                    final_df[col] = final_df[col].fillna(default_value)

            # OUTPUT
            st.success("Processing Complete")

            st.subheader("📄 Final Output Preview")

            st.dataframe(final_df, use_container_width=True, height=450)

            # EXPORT
            output = io.BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                final_df.to_excel(writer, index=False, sheet_name="FinalOutput")

            st.download_button(
                "📥 Download Excel",
                data=output.getvalue(),
                file_name=f"APC POSTAL - Detail Report - {mawb_input}_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ENTRY POINT


if __name__ == "__main__":
    run()
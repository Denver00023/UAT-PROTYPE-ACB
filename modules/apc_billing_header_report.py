import streamlit as st
import pandas as pd
import io

def run():

    st.subheader("📦 APC BILLING HEADER REPORT")
    st.caption("CANDATA REPORT + SFTP = HEADER REPORT TEMPLATE")

    FINAL_COLUMNS = [
        "Transaction Number",
        "Cargo Control Number",
        "Port Number",
        "Direct Ship Date",
        "ETA Date",
        "Release Date",
        "Order Number",
        "Brokerage Fee",
        "Total Value For Duty (CAD)",
        "Total Customs Duties (CAD)",
        "Total GST (CAD)",
        "Surtax (CAD)",
        "HST (CAD)",
        "Payment Terms",
        "Bill of Lading"
    ]

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

    if st.button("🚀 Process Files"):

        if not candata_file or not sftp_file:
            st.error("Please upload both CANDATA and SFTP files.")
            st.stop()

        try:


            # LOAD FILES
            def load_file(file):
                if file.name.endswith(".csv"):
                    return pd.read_csv(file)
                return pd.read_excel(file)

            candata_df = load_file(candata_file).fillna("")
            sftp_df = load_file(sftp_file).fillna("")

            candata_df.columns = candata_df.columns.str.strip()
            sftp_df.columns = sftp_df.columns.str.strip()

            # Normalize Cargo Control Number and Order Number Assuming the CANDATA file already contains the Order Number, remove the "8308" prefix from the Cargo Control Number (CCN) and use the resulting value as the Order Number.
            if "Order Number" in candata_df.columns:
                candata_df["Order Number"] = candata_df["Order Number"].astype(str).str.strip()

            if "Tracking Number/Package Barcode" in sftp_df.columns:
                sftp_df["Tracking Number/Package Barcode"] = sftp_df["Tracking Number/Package Barcode"].astype(str).str.strip()
    
            # CANDATA MAP
            candata_map = {
                "Transaction Number": "Transaction Number",
                "Cargo Control Number": "Cargo Control Number",
                "Port Number": "Port Number",
                "Direct Ship Date": "Direct Ship Date",
                "ETA Date": "ETA Date",
                "Release Date": "Release Date",
                "Order Number": "Order Number",
                "Brokerage Fee": "Brokerage Fee",
                "Total Value For Duty (CAD)": "Total Value For Duty (CAD)",
                "Total Customs Duties (CAD)": "Total Customs Duties (CAD)",
                "Surtax (CAD)": "Surtax (CAD)",
                "Total GST (CAD)": "Total GST (CAD)",
                "HST (CAD)": "HST (CAD)",
                "Payment Terms": "Payment Terms",
                "Bill of Lading": "Bill of Lading"
            }

            candata_out = pd.DataFrame()
            for src, tgt in candata_map.items():
                if src in candata_df.columns:
                    candata_out[tgt] = candata_df[src]

            # SFTP FILTER (IMPORTANT FIX)

            candata_ccn = set(candata_out["Order Number"].astype(str))

            # remove duplicates inside SFTP first
            sftp_df = sftp_df.drop_duplicates(subset=["Tracking Number/Package Barcode"])

            # keep ONLY unmatched rows
            sftp_filtered = sftp_df[
                ~sftp_df["Tracking Number/Package Barcode"].isin(candata_ccn)
            ].copy()

            # SFTP MAP
            sftp_map = {
                "Tracking Number/Package Barcode": "Cargo Control Number",
                "Total Value": "Total Value For Duty (CAD)",
            }

            sftp_out = pd.DataFrame()

            for src, tgt in sftp_map.items():
                if src in sftp_filtered.columns:
                    sftp_out[tgt] = sftp_filtered[src]

            # Assign CCN / Order Number properly
            if "Tracking Number/Package Barcode" in sftp_filtered.columns:
                sftp_out["Cargo Control Number"] = sftp_filtered["Tracking Number/Package Barcode"]
                sftp_out["Order Number"] = sftp_filtered["Tracking Number/Package Barcode"]
            
            # METRICS
            sftp_ccn = set(sftp_filtered["Tracking Number/Package Barcode"])

            match_count = len(candata_ccn.intersection(set(sftp_df["Tracking Number/Package Barcode"])))
            no_match_count = len(sftp_ccn)

            colm1, colm2 = st.columns(2)

            with colm1:
                st.metric("✅ Match Found (Skipped)", match_count)

            with colm2:
                st.metric("📦 No Match (Included)", no_match_count)

            # MERGE
            blank_row = pd.DataFrame([{col: "" for col in FINAL_COLUMNS}])

            final_df = pd.concat(
                [candata_out, blank_row, sftp_out],
                ignore_index=True
            )

            # enforce structure
            for col in FINAL_COLUMNS:
                if col not in final_df.columns:
                    final_df[col] = ""

            final_df = final_df[FINAL_COLUMNS]

            # DEFAULT CLEANUP
            DEFAULT_VALUES = {
                "Transaction Number": "CLVS",
                "Brokerage Fee": "0.43",
                "Total Customs Duties (CAD)": "0",
                "Total GST (CAD)": "0",
                "HST (CAD)": "0",
                "Payment Terms": "DDP",
                "Port Number":"496"
            }

            for col, val in DEFAULT_VALUES.items():
                if col in final_df.columns:
                    final_df[col] = final_df[col].replace("", pd.NA).fillna(val)

            # OUTPUT
            st.success("Processing Complete")
            st.subheader("📄 Final Output Preview")
            st.dataframe(final_df, use_container_width=True, height=450)

            output = io.BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                final_df.to_excel(writer, index=False, sheet_name="FinalOutput")

            st.download_button(
                "📥 Download Excel",
                data=output.getvalue(),
                file_name=f"APC POSTAL - Header Report -{mawb_input}_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    run()
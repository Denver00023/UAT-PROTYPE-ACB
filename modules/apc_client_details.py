import streamlit as st
import pandas as pd
import io


def run():

    st.subheader("📦 APC CLIENT DETAILS")
    st.caption("CANDATA + CLIENT = CLIENT DETAILS TEMPLATE")


    # FINAL STRUCTURE

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


    # UPLOADS

    col1, col2 = st.columns(2)

    with col1:
        candata_file = st.file_uploader("Upload CANDATA File", type=["xlsx", "csv"])

    with col2:
        client_file = st.file_uploader("Upload CLIENT File", type=["xlsx", "csv"])

    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")
    
    def load_file(file):
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        return pd.read_excel(file)


    # PROCESS

    if st.button("🚀 Process Files"):

        if not candata_file or not client_file:
            st.error("Please upload both CANDATA and CLIENT files.")
            st.stop()

        try:

            
            # LOAD DATA
            
            candata_df = load_file(candata_file).fillna("")
            client_df = load_file(client_file).fillna("")

            candata_df.columns = candata_df.columns.str.strip()
            client_df.columns = client_df.columns.str.strip()

            candata_df["Order Number"] = candata_df["Order Number"].astype(str).str.strip()
            client_df["Reliable_tracking"] = client_df["Reliable_tracking"].astype(str).str.strip()
            candata_df["Port Number"] = candata_df["Port Number"].astype(str).str.replace(".0", "", regex=False)

            def fix_hs_code(col):
                return (
                col.astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
                .str.zfill(10)   # ensures 10-digit HS code
                )
            
            if "Classification" in candata_df.columns:
                candata_df["Classification"] = fix_hs_code(candata_df["Classification"])

            
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
                "Value For (CAD)": "Value For (CAD)",
                "USD": "USD",
                "Classification": "Classification",
                "Duty Rate": "Duty Rate",
                "Customs Duty (CAD)": "Customs Duty (CAD)",
                "GST (CAD)": "GST (CAD)",
                "HST (CAD)": "HST (CAD)",
                "Provincial Sales Tax (CAD)": "Provincial Sales Tax (CAD)",
                "Surtax (CAD)": "Surtax (CAD)",
                "Payment Terms": "Payment Terms",
                "Bill of Lading": "Bill of Lading",
                "Cargo Control Number": "Cargo Control Number",
                "CCN": "CCN",
                "Order Number": "Order Number",
                "Consignee": "Consignee",
                "Consignee Address": "Consignee Address",
                "Consignee City": "Consignee City",
                "Consignee Postal Code": "Consignee Postal Code",
                "Consignee Province": "Consignee Province",
                "GST Rate": "GST Rate",
                "PST Rate": "PST Rate",
                "HST Rate": "HST Rate"
            }


            # BUILD CANDATA OUTPUT

            candata_out = pd.DataFrame()

            for src, tgt in candata_map.items():
                if src in candata_df.columns:
                    candata_out[tgt] = candata_df[src]


            # CLIENT ENRICHMENT

            client_lookup = client_df[
                [
                    "Reliable_tracking",
                    "Order_number",
                    "Vendor Code",
                    "Receptacle Number"
                ]
            ].drop_duplicates("Reliable_tracking")

            candata_out = candata_out.merge(
                client_lookup,
                left_on="Order Number",
                right_on="Reliable_tracking",
                how="left"
            )


            # APPLY CLIENT RULES


            candata_out["APC Number"] = candata_out["Order_number"].fillna(
                candata_out.get("APC Number", "")
            )

            candata_out["Vendor Code"] = candata_out["Vendor Code"]
            candata_out["Receptacle Number"] = candata_out["Receptacle Number"]

            # cleanup helper columns
            candata_out.drop(
                columns=["Reliable_tracking", "Order_number"],
                inplace=True,
                errors="ignore"
            )


            # FINAL STRUCTURE

            for col in FINAL_COLUMNS:
                if col not in candata_out.columns:
                    candata_out[col] = ""

            candata_out = candata_out[FINAL_COLUMNS]


            # OUTPUT

            st.success("Processing Complete")
            st.dataframe(candata_out, use_container_width=True, height=450)

            output = io.BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                candata_out.to_excel(writer, index=False, sheet_name="FinalOutput")

            st.download_button(
                "📥 Download Excel",
                data=output.getvalue(),
                file_name=f"APC POSTAL - Detail Report - {pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    run()
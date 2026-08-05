import streamlit as st
import pandas as pd
import io


def run():

    st.subheader("📦 ITEM REPORT")
    st.caption("GETS UPLOAD FILE + SFTP = EZCLEAR ITEM REPORT TEMPLATE")

    final_columns = [
        "Transaction Number",
        "Goods Description",
        "Line #",
        "Country of Origin",
        "Tariff Treatment",
        "Part Number",
        "Quantity",
        "Port #",
        "Vendor Name",
        "Value for Duty",
        "HS #",
        "Duty Rate",
        "Duty",
        "Value for Tax",
        "Gov. Sales Tax",
        "Inco Terms",
        "CCN"
    ]

    col1, col2 = st.columns(2)

    with col1:
        gets_file = st.file_uploader(
            "Upload GETS Upload File",
            type=["xlsx", "csv"]
        )
        client_value = st.text_input("CLIENT", placeholder="Client Name")
        rpt_name_value = st.text_input("RPT NAME", placeholder="MAWB #")

    with col2:
        sftp_file = st.file_uploader(
            "Upload SFTP File",
            type=["xlsx", "csv"]
        )
        rpt_date_value = st.text_input("RPT DATE", value=pd.Timestamp.now().strftime("%m/%d/%Y"))
    
    
    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")

    if st.button("🚀 Process Files"):

        if not gets_file or not sftp_file:
            st.error("Please upload both GETS and SFTP files.")
            return

        try:

            # Load Excel or CSV file
            def load_file(file, skip_row=False):

                if file.name.endswith(".csv"):
                    return pd.read_csv(
                        file,
                        skiprows=[1] if skip_row else None
                    )

                return pd.read_excel(
                    file,
                    skiprows=[1] if skip_row else None
                )

            gets_df = load_file(gets_file).fillna("")

            # SFTP data starts from row 3
            sftp_df = load_file(
                sftp_file,
                skip_row=True
            ).fillna("")

            gets_df.columns = gets_df.columns.str.strip()
            sftp_df.columns = sftp_df.columns.str.strip()

            gets_df["CCN_raw"] = gets_df["CCN"].astype(str).str.strip()

            gets_df["CCN_match"] = (
            gets_df["CCN_raw"]
            .str.replace(r"^8308\D*", "", regex=True)
            )

            sftp_df["Reliable_raw"] = sftp_df["Reliable_tracking"].astype(str).str.strip()

            sftp_df["Reliable_match"] = sftp_df["Reliable_raw"]

            # Clean tracking numbers
            gets_df["CCN"] = (
                gets_df["CCN"]
                .astype(str)
                .str.strip()
            )

            sftp_df["Reliable_tracking"] = (
                sftp_df["Reliable_tracking"]
                .astype(str)
                .str.strip()
            )

            # Remove shipments already existing in GETS
            existing_ccn = set(gets_df["CCN_match"])

            new_sftp = sftp_df[
                ~sftp_df["Reliable_match"].isin(existing_ccn)
            ].copy()

            # Create line sequence per Reliable_tracking
            new_sftp["Line #"] = (
                new_sftp
                .groupby("Reliable_tracking")
                .cumcount()
                + 1
            )

            # Map SFTP into ITEM REPORT format
            item_report = pd.DataFrame({

                "Transaction Number":new_sftp["Reliable_tracking"],
                "Goods Description":new_sftp["Goods_Description"],

                "Line #": new_sftp["Line #"],

                "Country of Origin":new_sftp["Country_of_origin"],
                "Tariff Treatment":"2",
                "Part Number":"",
                "Quantity":new_sftp["Quantity"],
                "Port #":new_sftp["Port_of_Discharge"],
                "Vendor Name":new_sftp["Seller_name"],
                "Value for Duty":new_sftp["Total_value_of_item"],
                "HS #":new_sftp["HS_code"],
                "Duty Rate":0,
                "Duty":0,
                "Value for Tax":0,
                "Gov. Sales Tax":0,
                "Inco Terms":new_sftp["Inco_term"],
                "CCN":new_sftp["Reliable_raw"]
            })

            # Apply default values
            defaults = {
                "Tariff Treatment": "2",
                "Part Number": "",
                "Duty Rate": 0,
                "Duty": 0,
                "Value for Tax": 0,
                "Gov. Sales Tax": 0
            }

            for col, value in defaults.items():
                item_report[col] = value

            # Show matching results
            matched = len(
                existing_ccn.intersection(
                    set(sftp_df["Reliable_tracking"])
                )
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "✅ Match Found (Skipped)",
                matched
            )

            col2.metric(
                "📦 New Included",
                len(item_report)
            )

            # Combine GETS + new SFTP records
            blank = pd.DataFrame(
                [{col: "" for col in final_columns}]
            )

            final_df = pd.concat(
                [
                    
                    gets_df[final_columns],
                    blank,
                    item_report
                ],
                ignore_index=True
            )

            
            st.success("Processing Complete")

            st.dataframe(
                final_df,
                use_container_width=True
            )

            # Export Excel
            output = io.BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:

                # STEP 1: write table lower
                final_df.to_excel(
                    writer,
                    index=False,
                    sheet_name="ITEM REPORT",
                    startrow=4  # 👈 IMPORTANT: data starts from row 6
                )
            
                worksheet = writer.sheets["ITEM REPORT"]

                worksheet["A1"] = "CLIENT:"
                worksheet["B1"] = client_value

                worksheet["A2"] = "RPT NAME:"
                worksheet["B2"] = rpt_name_value

                worksheet["A3"] = "RPT DATE :"
                worksheet["B3"] = rpt_date_value

            output.seek(0)

            output_filename = sftp_file.name.rsplit(".", 1)[0]
            
            st.download_button(
                "📥 Download ITEM REPORT",
                output.getvalue(),
                f"{output_filename}_ITEM_REPORT_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:

            st.error(
                f"❌ Error: {str(e)}"
            )


if __name__ == "__main__":
    run()
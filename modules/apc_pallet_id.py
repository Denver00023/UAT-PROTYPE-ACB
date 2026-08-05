import streamlit as st
import pandas as pd
from io import BytesIO
import re


def run():
    st.set_page_config(page_title="APC Pallet ID Automation", layout="wide")

    st.subheader("📦 APC Pallet ID Automation System")
    st.caption("Upload your Excel file and paste APC Tracking IDs to generate structured output.")

    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")


    col1, col2 = st.columns(2)

    with col1:
        # Upload file
        uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    with col2:
        search_mode = st.radio(
        "Search Mode",
        ["Exact Match", "Partial Match"],
        horizontal=True
        )

        expand = st.checkbox("Expand Input Box")

    # APC input
    apc_input = st.text_area(
        "Paste APC Tracking IDs (one per line)",
        height=400 if expand else 150,
        placeholder="APC17008P061521631860\nAPC17008P061521632085"
    )

    if uploaded_file is not None:

        try:
            df = pd.read_excel(uploaded_file)

            st.success("File uploaded successfully!")

            st.write("### Preview of Uploaded Data")

            st.dataframe(df, use_container_width=True)

            if st.button("Process Data"):

                # Normalize APC input
                apc_list = [x.strip() for x in apc_input.splitlines() if x.strip()]

                if not apc_list:
                    st.warning("Please enter at least one APC Tracking ID.")
                    return

                # Ensure enough columns exist
                required_cols = [0, 15, 16, 1, 2, 8]  # 1,16,17,2,3,5 (0-based)
                if df.shape[1] < max(required_cols) + 1:
                    st.error("Excel file does not have enough columns for mapping.")
                    return

                # Rename mapped columns
                mapped_df = pd.DataFrame()

                mapped_df["Tracking ID"] = df.iloc[:, 0]
                mapped_df["Parcel ID"] = df.iloc[:, 15]
                mapped_df["Pallet ID"] = df.iloc[:, 16]
                mapped_df["Consignee"] = df.iloc[:, 1]
                
                mapped_df["Consignee Address"] = (
                    df.iloc[:, [2, 4, 5, 6]]
                    .astype(str)
                    .fillna("")
                    .agg(" ".join, axis=1)
                    .str.replace(r"\s+", " ", regex=True)
                    .str.strip()
                )

                mapped_df["Goods Description"] = (
                    df.iloc[:, 8]
                    .fillna("")
                    .astype(str)
                    .str.upper()
                )

                # Normalize Tracking ID (remove APC prefix)
                tracking_series = (
                    mapped_df["Tracking ID"]
                    .astype(str)
                    .str.strip()
                    .str.replace(r"^APC", "", regex=True)
                )

                # Normalize user input (remove APC prefix if pasted)
                apc_list = [
                    re.sub(r"^APC", "", x.strip())
                    for x in apc_input.splitlines()
                    if x.strip()
                ]

                # Apply search mode
                if search_mode == "Exact Match":
                    mask = tracking_series.isin(apc_list)

                else:
                    pattern = "|".join(re.escape(x) for x in apc_list)
                    mask = tracking_series.str.contains(pattern, na=False)

                result_df = mapped_df[mask]

                st.write("### Matched Results")

                st.dataframe(result_df, use_container_width=True)

                if result_df.empty:
                    st.warning("No matching APC Tracking IDs found.")
                    return

                # Convert to Excel for download
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    result_df.to_excel(writer, index=False, sheet_name="APC_Pallet_ID")

                output.seek(0)

                st.download_button(
                    label="📥 Download Pallet ID Excel",
                    data=output,
                    file_name=f"APC_Pallet_ID_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")


if __name__ == "__main__":
    run()
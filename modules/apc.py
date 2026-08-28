import streamlit as st
import pandas as pd
import io
from collections import Counter
import re


def clean_description(text):

    if pd.isna(text):
        return ""

    text = str(text)

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")

    text = re.sub(
        r"[^A-Za-z0-9\s\-\.,/&()]",
        "",
        text
    )

    text = re.sub(r"\s+", " ", text).strip()

    return text

def run():

    # PAGE HEADER
    st.subheader("📊 APC Excel Processor Tool")

    # FIXED TEMPLATE HEADERS
    TEMPLATE_COLUMNS = [
        "Inco_term",
        "Mode_of_transport",
        "Seller_code",
        "Seller_name",
        "Seller_address",
        "Seller_city",
        "Seller_postal_code",
        "Seller_state",
        "Seller_country",
        "Seller_phone_number",
        "Seller_email",
        "Pickup_code",
        "Pickup_name",
        "Pickup_address",
        "Pickup_city",
        "Pickup_postal_code",
        "Pickup_state",
        "Pickup_country",
        "Buyer_code",
        "Buyer_name",
        "Buyer_address",
        "Buyer_city",
        "Buyer_postal_code",
        "Buyer_province",
        "Buyer_country",
        "Buyer_phone_number",
        "Buyer_email",
        "Order_number",
        "Reliable_tracking",
        "Client_Internal_tracking",
        "Parcel_item_weight",
        "Parcel_item_weight_UOM",
        "Width",
        "Length",
        "Height",
        "Width_Length_Height_UOM",
        "Product_part",
        "Currency_code",
        "Package_no",
        "Quantity",
        "Quantity_UOM",
        "Unit_price",
        "UNDG",
        "Total_value_of_item",
        "Total_value_of_parcel",
        "HS_code",
        "Goods_Description",
        "Country_of_origin",
        "Url",
        "Importer_number",
        "Importer_party_id",
        "AutoCalc_Provincial_Rate",
        "CBSA_Port_of_Release",
        "CBSA_Warehouse_Sub_Location_Code",
        "Port_of_Discharge",
        "IID_Y/N",
        "Masterbill"
    ]
    
    # VALIDATION / FORMAT ROW

    HEADER_RULES = [
        "O,1…8 AN",
        "M,1 N",
        "O,1…35 AN",
        "M,1…70 AN",
        "M,1…105 AN",
        "M,1…35 AN",
        "M,1…9 AN",
        "M,1…9 A",
        "M,1…3 A",
        "M,1…50 N",
        "M,1…100 AN",
        "O,1…35 AN",
        "M,1…70 AN",
        "M,1…105 AN",
        "M,1…35 AN",
        "M,1…9 AN",
        "M,1…9 A",
        "M,1…3 A",
        "O,1…35 AN",
        "M,1…70 AN",
        "M,1…105 AN",
        "M,1…35 AN",
        "M,1…9 AN",
        "M,1…9 A",
        "M,1…3 A",
        "M,1…50 N",
        "M,1…100 AN",
        "M,1…35 AN",
        "M,1…35 AN",
        "M,1…70 AN",
        "M,1…20 N",
        "M,1…3 A",
        "O,1…10 N",
        "O,1…10 N",
        "O,1…10 N",
        "O,1…3 A",
        "O,1…35 AN",
        "M,1…3 A",
        "M,1…8 N",
        "M,1…18 N",
        "M,1…3 A",
        "M,1…18 N",
        "O,4 N",
        "M,1…18 N",
        "M,1…18 N",
        "M,10 N",
        "M,1…256 AN",
        "M,1…3 A",
        "O,1…70 AN",
        "O,15 AN",
        "O,1…50 AN",
        "O,1 A",
        "M,4 N",
        "O,4 N",
        "O,4 N",
        "O,1 A",
        "M,1…256 AN"
    ]
    
    # FILE UPLOADS
    
    # FILENAME
    col1, col2 = st.columns(2)

    with col1:
    # MAWB INPUT
        mawb_input = st.text_input(
        "**MAWB #**",
        placeholder="123-45678901"
        )

    with col2:
        port_input = st.text_input(
        "**Port #**",
        placeholder="EWR or ORD"
        )

    st.caption("Note: Please enter MAWB and Port # before uploading files. These will be used in the output filename.")

    client_file = st.file_uploader(
        "**Upload CLIENT EXCEL File**",
        type=["xlsx", "xls"]
    )

    lookup_file = st.file_uploader(
        "**Upload VENDOR MASTERFILE LOOKUP**",
        type=["xlsx", "xls"]
    )

    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")
    
    # PROCESS BUTTON
    
    if st.button("🚀 Process Files"):

        if not client_file or not lookup_file:

            st.error(
                "Please upload all required files."
            )

            st.stop()

        try:
            
            # READ FILES
            
            client_df = pd.read_excel(
                client_file,
                dtype=str
            ).fillna('')

            lookup_df = pd.read_excel(
                lookup_file,
                dtype=str
            ).fillna('')
            
            # BUILD LOOKUP DICTIONARY
            
            lookup_dict = {}

            for _, row in lookup_df.iterrows():

                vendor_marker = str(
                    row.get('WLR #', '')
                ).strip()

                lookup_dict[vendor_marker] = {
                    'Seller_name': row.get('COMPANY NAME', ''),
                    'Seller_address': row.get('ADDRESS', ''),
                    'Seller_city': row.get('CITY', ''),
                    'Seller_state': row.get('STATE', ''),
                    'Seller_postal_code': row.get('ZIP', ''),
                    'Seller_country': 'US',
                    'Seller_phone_number': '555-555-5555',
                    'Seller_email': 'email@email.com',
                    'Buyer_email': 'email@email.com',
                    'Pickup_name': row.get('COMPANY NAME', ''),
                    'Pickup_address': row.get('ADDRESS', ''),
                    'Pickup_city': row.get('CITY', ''),
                    'Pickup_state': row.get('STATE', ''),
                    'Pickup_postal_code': row.get('ZIP', ''),
                    'Pickup_country': 'US'
                }
            
            # DEFAULT VALUES
            
            DEFAULT_FIELDS = {
                'Inco_term': 'DDP',
                'Mode_of_transport': 2,
                'Buyer_phone_number': '555-555-5555',
                'Buyer_country': 'CA',
                'Parcel_item_weight_UOM': 'KGM',
                'Currency_code': 'CAD',
                'Package_no': 1,
                'Quantity_UOM': 'PK',
                'Importer_number': '101750818RM0017',
                'AutoCalc_Provincial_Rate': 'P',
                'CBSA_Port_of_Release': '0496',
                'CBSA_Warehouse_Sub_Location_Code': '5653',
                'Port_of_Discharge': '0496',
                'IID_Y/N': 'N'
            }
            
            # PROCESS CLIENT DATA
            
            output_rows = []

            current_marker = None

            marker_counter = Counter()

            for _, row in client_df.iterrows():

                first_col = str(
                    row.iloc[0]
                ).strip()
                
                # DETECT MARKER ROWS
                
                if first_col.startswith(("APC", "REL")):

                    current_marker = first_col

                    continue
                
                # SKIP ROWS BEFORE FIRST MARKER
                
                if not current_marker:
                    continue

                data = row.to_dict()

                data['Marker'] = current_marker

                marker_counter[current_marker] += 1
                
                # LOOKUP DATA
                
                lookup_data = lookup_dict.get(
                    current_marker,
                    {}
                )
                
                # APPLY LOOKUP VALUES
                
                for key, value in lookup_data.items():

                    if not data.get(key):

                        data[key] = value
                
                # APPLY DEFAULTS
                
                for key, value in DEFAULT_FIELDS.items():

                    if not data.get(key):

                        data[key] = value

                output_rows.append(data)
            
            # BUILD FINAL DATAFRAME
            
            final_df = pd.DataFrame(output_rows)

            seller = final_df["Seller_name"].astype(str).str.upper().str.strip()

            match = seller.isin(["THAT'S MY GEEK", "THATS MY GEEK"])

            if match.any():
                final_df.loc[match, "AutoCalc_Provincial_Rate"] = "P"
                final_df.loc[match, "Importer_number"] = "101750818RM0017"
                final_df.loc[match, "Importer_party_id"] = "APCGREL01"

            # KEEP ORIGINAL RELIABLE_TRACKING FIRST
            final_df['Client_Internal_tracking'] = final_df['Reliable_tracking']

            # NOW ADD PREFIX
            final_df['Reliable_tracking'] = 'APC' + final_df['Reliable_tracking'].astype(str)

            # ADD MISSING COLUMNS
            for col in TEMPLATE_COLUMNS:

                if col not in final_df.columns:

                    final_df[col] = ''

            # FORCE EXACT COLUMN ORDER
            final_df = final_df[TEMPLATE_COLUMNS]

            final_df["Goods_Description"] = (
            final_df["Goods_Description"]
            .apply(clean_description)
            )

            # FINAL OUTPUT CALCULATION (OVERWRITE VALUES)

            # Ensure numeric conversion
            final_df['Unit_price'] = pd.to_numeric(final_df['Unit_price'], errors='coerce').fillna(0)
            final_df['Quantity'] = pd.to_numeric(final_df['Quantity'], errors='coerce').fillna(0)

            # 1. COMPUTE ITEM TOTAL
            final_df['Total_value_of_item'] = final_df['Unit_price'] * final_df['Quantity']

            # 2. COMPUTE PARCEL TOTAL (GROUP BY RELIABLE_TRACKING)
            final_df['Total_value_of_parcel'] = final_df.groupby(
            'Reliable_tracking'
            )['Total_value_of_item'].transform('sum')

            # CLEAN FLOATING POINT + KEEP NUMERIC
            final_df['Total_value_of_item'] = final_df['Total_value_of_item'].apply(
            lambda x: float(f"{x:.2f}")
            )

            final_df['Total_value_of_parcel'] = final_df['Total_value_of_parcel'].apply(
            lambda x: float(f"{x:.2f}")
            )

            validation_errors = []

            final_df["HS_code"] = (
                final_df["HS_code"]
                .astype(str)
                .str.replace(r"\.0$", "", regex=True)
                .str.strip()
                .apply(lambda x: x.zfill(10) if x.isdigit() and len(x) < 10 else x)
            )

            for idx, row in final_df.iterrows():

                tracking = row.get("Reliable_tracking", "")

                def add(field, issue):
                    validation_errors.append({
                    "Row": idx + 1,
                    "Tracking": tracking,
                    "Field": field,
                    "Issue": issue
                    })
                
                # Buyer Name
                if not str(row.get("Buyer_name", "")).strip():
                    add("Buyer_name", "Blank value")
                
                # Buyer Address
                if not str(row.get("Buyer_address", "")).strip():
                    add("Buyer_address", "Blank value")

                # Quantity
                qty = row.get("Quantity", "")
                try:
                    if float(qty) <= 0:
                        add("Quantity", "Must be greater than 0")
                except:
                    add("Quantity", "Invalid or blank")

                # Buyer Address
                if not str(row.get("Goods_Description", "")).strip():
                    add("Goods_Description", "Blank value")

                # Buyer Province
                if len(str(row.get("Buyer_province", "")).strip()) != 2:
                    add("Buyer_province", "Must be 2 characters")

                # HS CODE
                hs_code = str(row.get("HS_code", "")).strip()
                if len(hs_code) != 10:
                    add("HS_code", "Must be exactly 10 characters")

                # Goods Description (RAW CHECK)
                raw_desc = str(row.get("Goods_Description", ""))

                if re.search(r"[^A-Za-z0-9\s\-\.,/&()]", raw_desc):
                    add("Goods_Description", "Contains invalid special characters")

            if validation_errors:

                st.error(f"❌ Validation failed. Found {len(validation_errors)} issue(s).")

                error_df = pd.DataFrame(validation_errors)

                summary = (
                    error_df.groupby(["Field"])
                    .size()
                    .reset_index(name="Count")
                    .sort_values("Count", ascending=False)
                )

                st.subheader("📄 Full Error Report")
                st.dataframe(error_df, use_container_width=True, height=400)

                st.stop()

            rules_df = pd.DataFrame([HEADER_RULES], columns=TEMPLATE_COLUMNS)
            export_df = pd.concat([rules_df, final_df], ignore_index=True)

            # EXPORT EXCEL
            
            output = io.BytesIO()

            with pd.ExcelWriter(
                output,
                engine='openpyxl'
            ) as writer:
                
                export_df.to_excel(
                    writer,
                    index=False,
                    header=TEMPLATE_COLUMNS,
                    sheet_name='Worksheet'
                )
            
            # SUCCESS
            st.success("✅ Processing Complete!")
            
            # METRICS
            
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric(
                    "Total Processed Rows",
                    len(final_df)
                )
            with metric_col2:
                st.metric(
                    "Order Number Unique",
                    final_df.get(
                        "Order_number",
                        pd.Series(dtype=str)
                    ).nunique()
                )
            
            # FINAL OUTPUT PREVIEW
            
            st.markdown("---")
            st.subheader("📄 Final Output Preview")

            st.dataframe(
                final_df,
                use_container_width=True,
                height=350
            )
            
            # DOWNLOAD BUTTON
            
            st.markdown("---")

            st.download_button(
                label="📥 Download Result",
                data=output.getvalue(),
                file_name=f"RLBE_161_{mawb_input}_{port_input}_496_YYZ_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.xlsx",
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                )
            )
        except Exception as e:
            st.error(
                f"❌ Processing Failed: {str(e)}"
            )
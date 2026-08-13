import streamlit as st
import pandas as pd
import io
from datetime import datetime


# BASE HEADERS
BASE_HEADERS = [
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
    "Product_code",
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
    "Port_of_Discharge_Sublocation Code",
    "IID_Y/N",
    "PGA Flag",
    "Category",
    "MAWB #",
    "Carrier code",
    "Manifest Only",
    "Movement Type",
    "TARIFF_TREATMENT_CODE",
    "External Reference 2",
    "GST CODE",

]

IMPORTER_RULES = {
    "131865263RM0001": {
        "Importer_party_id": "APCCHRI01",
        "AutoCalc_Provincial_Rate": "C"
    },
    "874616311RM0001": {
        "Importer_party_id": "APCB2B01"
    },
    "101750818RM0017": {
        "Importer_party_id": "FBGYYZ01"
    },
    "709267157RM0001": {
        "Importer_party_id": "APCB2B02"
    }
}

# CLIENT CONFIG
CLIENT_CONFIG = {

    "PGA": {

        "filter_iid": "Y",

        "extra_headers": [
            
        ],

        "mapping": {
            "Product_code": "Product_part",
            "PGA Flag": "PGAResult",
            "External Reference 2": "Client_Internal_tracking"
        },

        "defaults": {
            "Importer_party_id": "",
            "Port_of_Discharge_Sublocation Code": "",
            "Carrier code": "8308",

        },

        "importer_rules": {
        
        }
    },

    "B2B": {

            "filter_iid": "Y",

            "extra_headers": [
                
            ],
    
            "mapping": {
                "Product_code": "Product_part",
                "PGA Flag": "PGAResult",
                "External Reference 2": "Client_Internal_tracking"
            },
    
            "defaults": {
                "Importer_number": "874616311RM0001",
                "Importer_party_id": "APCB2B01",
                "AutoCalc_Provincial_Rate": "C",
                "Port_of_Discharge_Sublocation Code": "",
                "Carrier code": "8308",
    
            },
    
            "importer_rules": {
                
            }
        },

    "LVS": {

            "filter_iid": "N",

            "extra_headers": [
                
            ],
    
            "mapping": {
                "Product_code": "Product_part",
                "PGA Flag": "PGAResult",
                "External Reference 2": "Client_Internal_tracking"
            },
    
            "defaults": {
                "Importer_number": "101750818RM0017",
                "Importer_party_id": "FBGYYZ01",
                "AutoCalc_Provincial_Rate": "P",
                "Port_of_Discharge_Sublocation Code": "",
    
            },
    
            "importer_rules": {
                
            }
        },

}

# REQUIRED COLUMNS
REQUIRED_COLUMNS = [
    "Reliable_tracking",
    "IID_Y/N",
    "Total_value_of_item",
    "Total_value_of_parcel"
]


# UTILITIES
def clean_columns(df):

    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\n", " ")
        .str.strip()
    )

    return df


def validate_required_columns(df):

    missing_cols = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    return missing_cols


def safe_float(value):

    try:
        return float(str(value).replace(",", "").strip())

    except:
        return 0.0


def protect_excel_formula(value):

    if isinstance(value, str):

        if value.startswith(("=", "+", "-", "@")):
            return f"'{value}"

    return value


# VALIDATION

def validate_data(df, client_type):

    audit_rows = []

    # COUNTRY OF ORIGIN VALIDATION
    if client_type in ["PGA", "B2B", "LVS"]:

        restricted_origins = {"RU", "BY", "KP"}

        for index, row in df.iterrows():

            origin = str(row.get("Country_of_origin", "")).strip().upper()

            if origin in restricted_origins:

                audit_rows.append({
                    "Reliable_tracking": row.get("Reliable_tracking", ""),
                    "Issue": "Invalid Country_of_origin",
                    "Value": origin,
                    "Details": (
                        f"Country_of_origin '{origin}' is not allowed "
                        f"for {client_type}."
                    )
                })
    
    # IID VALIDATION
    iid_group = (
        df.groupby("Reliable_tracking")["IID_Y/N"]
        .apply(
            lambda x:
            set(
                x.astype(str)
                .str.strip()
                .str.upper()
            )
        )
    )

    for tracking, values in iid_group.items():

        if "Y" in values and "N" in values:

            audit_rows.append({

                "Reliable_tracking": tracking,

                "Issue": "Mixed IID_Y/N values",

                "Details":
                    f"Tracking {tracking} has both Y and N rows"
            })
    
    # VALUE VALIDATION
    
    df["ITEM_VALUE_FLOAT"] = (
        df["Total_value_of_item"]
        .apply(safe_float)
    )

    df["PARCEL_VALUE_FLOAT"] = (
        df["Total_value_of_parcel"]
        .apply(safe_float)
    )

    grouped = df.groupby("Reliable_tracking")

    for tracking, group in grouped:

        item_total = round(
            group["ITEM_VALUE_FLOAT"].sum(),
            2
        )

        parcel_values = (
            group["PARCEL_VALUE_FLOAT"]
            .unique()
            .tolist()
        )

        # PARCEL VALUE CONSISTENCY

        if len(parcel_values) > 1:

            audit_rows.append({

                "Reliable_tracking": tracking,

                "Issue": "Inconsistent Parcel Values",

                "Details":
                    f"Multiple parcel values found: "
                    f"{parcel_values}"
            })

        parcel_value = round(parcel_values[0], 2)

        difference = round(
            item_total - parcel_value,
            2
        )

        if item_total != parcel_value:

            audit_rows.append({

                "Reliable_tracking": tracking,

                "Issue": "VALUE MISMATCH",

                "Calculated_Item_Total": item_total,

                "Parcel_Value": parcel_value,

                "Difference": difference,

                "Details":
                    f"Expected {item_total} "
                    f"but found {parcel_value}"
            })

    return audit_rows

# PROCESS DATA

def process_data(
    df,
    config,
    final_headers,
    overrides
):

    output_rows = []

    mapping = config["mapping"]

    defaults = config["defaults"]

    importer_rules = config.get(
        "importer_rules",
        {}
    )
    
    # FILTER IID = Y
    filter_iid = config.get("filter_iid")

    if filter_iid:

        df = df[
            df["IID_Y/N"]
            .astype(str)
            .str.strip()
            .str.upper()
            == filter_iid
        ]
    
    # PROCESS ROWS
    
    for _, row in df.iterrows():

        mapped_row = {}

        for final_col in final_headers:

            source_col = mapping.get(
                final_col,
                final_col
            )

            value = row.get(
                source_col,
                ""
            )

            # APPLY DEFAULTS

            if not str(value).strip():

                value = defaults.get(
                    final_col,
                    ""
                )

            # APPLY OVERRIDES
            override_value = overrides.get(
                final_col,
                ""
            )

            if override_value:
                value = override_value

            # CURRENCY CODE
            if final_col == "Currency_code":
                value = "USD"
    
            # TARIFF TREATMENT CODE

            if final_col == "TARIFF_TREATMENT_CODE":

                origin = str(
                    row.get(
                        "Country_of_origin",
                        ""
                    )
                ).strip().upper()

                if origin == "US":
                    value = "10"
                else:
                    value = ""

            # COUNTRY OF ORIGIN RULE
            if final_col == "Country_of_origin":

                origin = str(
                    row.get(
                        "Country_of_origin",
                        ""
                    )
                ).strip().upper()

                pickup_state = str(
                    row.get(
                        "Pickup_state",
                        ""
                    )
                ).strip().upper()

                if origin in ["CA", "US"]:

                    value = "U" + pickup_state

                else:
                    
                    value = row.get("Country_of_origin", "")

            # GST CODE RULES
            if final_col == "GST CODE":

                seller_name = str(
                    row.get(
                        "Seller_name",
                        ""
                    )
                ).strip().upper()

                buyer_name = str(
                    row.get(
                        "Buyer_name",
                        ""
                    )
                ).strip().upper()

                # CHRISTIAN LIGHT PUBLICATIONS + RELIABLE LOGISTICS
                if (
                    "CHRISTIAN LIGHT PUBLICATIONS" in seller_name
                    and
                    "RELIABLE LOGISTICS" in buyer_name
                ):
                    value = "065"

                # APC POSTAL + APC C/O CANADA POST
                elif (
                    "APC POSTAL" in seller_name
                    and
                    "APC C/O CANADA POST" in buyer_name
                ):
                    value = "065"

                # APC POSTAL + RELIABLE LOGISTICS
                elif (
                    "APC POSTAL" in seller_name
                    and
                    "RELIABLE LOGISTICS" in buyer_name
                ):
                    value = "001"

                # SECRET LAIR SELLER + Reliable Logistics BUYER
                elif (
                    "SECRET LAIR" in seller_name
                    and
                    "RELIABLE LOGISTICS" in buyer_name
                ):
                    value = "001"

                # PEHR DESIGNS INC SELLER + Reliable Logistics BUYER
                elif (
                    "PEHR DESIGNS INC" in seller_name
                    and
                    "RELIABLE LOGISTICS" in buyer_name
                ):
                    value = ""

                else:
                    value = ""

            if final_col in ["Importer_party_id", "AutoCalc_Provincial_Rate"]:

                importer_number = str(
                    row.get("Importer_number", "")
                ).strip()

                if importer_number in IMPORTER_RULES:

                    rule = IMPORTER_RULES[importer_number]

                    if final_col in rule:
                        value = rule[final_col]

            mapped_row[final_col] = value

        output_rows.append(mapped_row)
    
    # FINAL DATAFRAME
    final_df = pd.DataFrame(output_rows)

    final_df = final_df.reindex(
        columns=final_headers
    )
    
    # EXCEL FORMULA PROTECTION
    final_df = final_df.map(
        protect_excel_formula
    )

    return final_df

# EXPORT EXCEL

def generate_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Output"
        )

    output.seek(0)

    return output

# MAIN APP

def run():

    st.subheader("📊 APC CANDATA FILE PROCESSOR")

    # CLIENT TYPE
    
    client_type = st.radio(
        "Select Client Template",
        list(CLIENT_CONFIG.keys()),
        horizontal=True
    )
    
    # OPTIONAL INPUTS
    
    col1, col2 = st.columns(2)

    with col1:

        mawb_input = st.text_input(
            "**MAWB # (optional)**",
            placeholder="123-45678901"
        )

        carrier_code_input = st.text_input(
            "**Carrier Code (optional COLUMN BI)**",
            placeholder="0000"
        )

    with col2:
        port_of_discharge_input = st.text_input(
            "**Port of Discharge (optional COLUMN BC)**",
            placeholder="0000"
        )

        port_input = st.text_input(
            "**Port Sublocation Code (optional COLUMN BD)**",
            placeholder="0000"
        )

    st.caption("“Note: Filling in these fields is optional. If you prefer not to use them, simply leave them blank. However, if you do provide values, they will be included in the final output of the Excel download file.”")
    
    # FILE UPLOAD
    client_file = st.file_uploader(
        "**Upload Client File**",
        type=["xlsx", "xls"]
    )
    
    st.caption("“Note: Please make sure the file is already cleaned and rows to process are marked as 'Y' in IID_Y/N. Rows marked as 'N' will not be included in the output. Thank you.“")

    st.markdown("----")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")
    
    # PROCESS
    
    if st.button("🚀 Process"):

        if not client_file:

            st.error(
                "Please upload client file."
            )

            return

        try:

            with st.spinner(
                "Processing file..."
            ):
                
                # READ EXCEL
                
                df = pd.read_excel(
                    client_file,
                    dtype=str,
                    engine="openpyxl"
                ).fillna("")
                
                # CLEAN COLUMNS
                
                df = clean_columns(df)
                
                # VALIDATE REQUIRED COLUMNS
                
                missing_cols = validate_required_columns(df)

                if missing_cols:

                    st.error(
                        f"Missing required columns: "
                        f"{', '.join(missing_cols)}"
                    )

                    st.stop()
                
                # CONFIG
                
                config = CLIENT_CONFIG[client_type]

                final_headers = (
                    BASE_HEADERS +
                    config["extra_headers"]
                )
                
                # OVERRIDES
                
                overrides = {

                    "MAWB #":
                        mawb_input.strip(),

                    "Port_of_Discharge_Sublocation Code":
                        port_input.strip(),
                    
                    "Port_of_Discharge":
                        port_of_discharge_input.strip(),

                    "Carrier code":
                        carrier_code_input.strip()
                }
                
                # VALIDATION
                
                audit_rows = validate_data(df, client_type)
                
                # VALIDATION FAILED
                
                if audit_rows:

                    audit_df = pd.DataFrame(
                        audit_rows
                    )

                    st.error(
                        f"❌ Found "
                        f"{len(audit_df)} "
                        f"validation issues"
                    )

                    with st.expander(
                        "View Validation Errors",
                        expanded=True
                    ):

                        st.dataframe(
                            audit_df,
                            use_container_width=True
                        )

                    st.stop()
                
                # PROCESS DATA
                
                final_df = process_data(
                    df=df,
                    config=config,
                    final_headers=final_headers,
                    overrides=overrides
                )

                unique_tracking = final_df["Reliable_tracking"].nunique()

                duplicate_tracking = (
                    final_df["Reliable_tracking"]
                    .value_counts()
                    .gt(1)
                    .sum()
                )

                # METRICS
                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.metric(
                        "Processed Rows",
                        len(final_df)
                    )

                with col2:
                    st.metric(
                        "Duplicate Reliable Tracking",
                        duplicate_tracking
                    )

                with col3:    
                    st.metric(
                        "Unique Reliable Tracking",
                        unique_tracking
                    )

                with col4:

                    st.metric(
                        "Validation Errors",
                        0
                    )

                
                # SUCCESS
                st.success(
                    f"✅ Successfully processed "
                    f"{len(final_df)} rows"
                )
                
                # DISPLAY DATA
                st.dataframe(
                    final_df,
                    use_container_width=True
                )
                
                # EXPORT EXCEL
                output = generate_excel(
                    final_df
                )
                
                # SAFE FILENAME
                safe_mawb = (
                    mawb_input.strip()
                    or "NO_MAWB"
                )

                timestamp = datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )

                filename = (
                    f"{client_type}_"
                    f"{safe_mawb}_"
                    f"{timestamp}_"
                    f"CANDATA_UPLOAD_FILE.xlsx"
                )
                
                # DOWNLOAD BUTTON
                st.download_button(
                    label="📥 Download Result",
                    data=output.getvalue(),
                    file_name=filename,
                    mime=(
                        "application/vnd.openxmlformats-"
                        "officedocument.spreadsheetml.sheet"
                    )
                )

        except Exception as e:

            st.exception(e)


# RUN APP

if __name__ == "__main__":
    run()
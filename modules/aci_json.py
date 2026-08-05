import streamlit as st
import pandas as pd
import json

def run():

    
    st.subheader("📦 Shipment Excel → JSON Converter")

    STATE_MAP = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut",
        "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
        "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
        "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
        "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan",
        "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
        "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
        "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
        "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
        "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
        "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
        "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming"
    }

    CANADA_PROVINCES = {
        "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba",
        "NB": "New Brunswick", "NL": "Newfoundland and Labrador",
        "NS": "Nova Scotia", "ON": "Ontario", "PE": "Prince Edward Island",
        "QC": "Quebec", "SK": "Saskatchewan", "NT": "Northwest Territories",
        "NU": "Nunavut", "YT": "Yukon"
    }

    uploaded_file = st.file_uploader("Upload Excel or CSV File", type=["xlsx", "xls", "csv"])

    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")

    if not uploaded_file:
        return

    # ---------------- LOAD FILE ----------------
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, dtype=str)
        else:
            df = pd.read_excel(uploaded_file, dtype=str)

        st.success("File loaded successfully")
        st.dataframe(df.head())

    except Exception as e:
        st.error(f"Error loading file: {e}")
        return

    # ---------------- CLEAN + MAP STATES ----------------
    for idx, row in df.iterrows():

        shipper_state = str(row.get("Shipper State", "")).strip().upper()
        consignee_state = str(row.get("Consignee Prov", "")).strip().upper()

        df.at[idx, "Shipper State Name"] = STATE_MAP.get(shipper_state, "")
        df.at[idx, "Consignee Prov Name"] = (
            CANADA_PROVINCES.get(consignee_state)
            or STATE_MAP.get(consignee_state, "")
        )

    # ---------------- SESSION STATE (OVERWRITE CONTROL) ----------------
    if "json_output" not in st.session_state:
        st.session_state.json_output = None

    # ---------------- CONVERT BUTTON ----------------
    if st.button("🚀 Convert to JSON"):

        shipments = {}

        for _, row in df.iterrows():

            ccn = str(row.get("Cargo Control Number", "")).strip()
            if not ccn or ccn.lower() == "nan":
                continue

            if ccn not in shipments:
                shipments[ccn] = {
                    "cargoControlNumber": ccn,
                    "shipmentType": row.get("Shipment Type", ""),
                    "portOfEntry": str(row.get("First Port of Arrival", "")).strip().zfill(4),
                    "releaseOffice": str(row.get("Release Office", "")).strip().zfill(4),
                    "estimatedArrivalDate": str(row.get("Estimated Arrival Date", "")),
                    "estimatedArrivalTimeZone": "EST",
                    "cityOfLoading": {
                        "cityName": row.get("Shipper City", ""),
                        "stateProvince": row.get("Shipper State", "")
                    },
                    "shipper": {
                        "name": row.get("Shipper Name", ""),
                        "address": {
                            "addressLine": row.get("Shipper Address", ""),
                            "city": row.get("Shipper City", ""),
                            "stateProvince": row.get("Shipper State", ""),
                            "stateProvinceName": row.get("Shipper State Name", ""),
                            "country": row.get("Country", ""),
                            "countryName": row.get("Country Name", ""),
                            "postalCode": str(row.get("Shipper Zipcode", "")).strip().zfill(5)
                        }
                    },
                    "consignee": {
                        "name": row.get("Consignee Name", ""),
                        "address": {
                            "addressLine": row.get("Consignee Address", ""),
                            "city": row.get("Consignee City", ""),
                            "stateProvince": row.get("Consignee Prov", ""),
                            "stateProvinceName": row.get("Consignee Prov Name", ""),
                            "country": row.get("Consignee County", ""),
                            "countryName": row.get("Consignee County Name", ""),
                            "postalCode": str(row.get("Consignee Postal", "")).strip().zfill(5)
                        }
                    },
                    "commodities": []
                }

            commodity = {
                "description": row.get("Commodity Desc", ""),
                "quantity": int(row.get("Commodity Quantity", 0)) if str(row.get("Commodity Quantity", "")).isdigit() else 0,
                "packagingUnit": row.get("Commodity Quantity Unit", ""),
                "weight": row.get("Commodity Weight", ""),
                "weightUnit": row.get("Commodity Weight Unit", "")
            }

            shipments[ccn]["commodities"].append(commodity)

        # 🔥 OVERWRITE JSON EVERY TIME
        st.session_state.json_output = json.dumps(list(shipments.values()), indent=4)

        st.success("JSON generated (check preview below)")

    # ---------------- OUTPUT ----------------
    if st.session_state.json_output:

        st.subheader("JSON Preview")
        st.code(st.session_state.json_output, language="json")

        output_filename = uploaded_file.name.rsplit(".", 1)[0] + ".json"

        st.download_button(
            "📥 Download JSON File",
            data=st.session_state.json_output,
            file_name=output_filename,
            mime="application/json"
        )

    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Shipment Converter Module")
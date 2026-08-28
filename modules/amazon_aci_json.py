import streamlit as st
import pandas as pd
import json
import re


def clean_description(text):
    if pd.isna(text):
        return ""

    text = str(text)

    # Remove line breaks and tabs
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")

    # Remove special characters, keep letters, numbers, spaces, and common punctuation
    text = re.sub(r"[^A-Za-z0-9\s\-\.,/&()]", "", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text

def run():

    
    st.subheader("📦 AMAZON B2B CANDATA → JSON Converter")

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

    uploaded_file = st.file_uploader("**Upload Excel or CSV File**", type=["xlsx", "xls", "csv"])

    from datetime import datetime
    from zoneinfo import ZoneInfo

    # Current EST time + 2 hours
    est_now = datetime.now(ZoneInfo("Etc/GMT+5"))

    default_arrival = est_now.strftime("%Y-%m-%d %H:%M:%S")

    arrival_datetime = st.text_input(
    "**Estimated Arrival Date/Time (YY-MM-DD HH:MM:SS)**",
    value=default_arrival
    )

    st.caption("Note: Please ensure the you already have the correct Estimated Arrival Date/Time before converting to JSON.")

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

        shipper_state = str(row.get("Seller_state", "")).strip().upper()
        consignee_state = str(row.get("Buyer_province", "")).strip().upper()

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

            carrier_code = str(row.get("Carrier code", "")).strip()
            reliable_tracking = str(row.get("Reliable_tracking", "")).strip()

            ccn = f"{carrier_code}{reliable_tracking}"
            if not ccn or ccn.lower() == "nan":
                continue

            if ccn not in shipments:
                shipments[ccn] = {
                    "cargoControlNumber": ccn,
                    "shipmentType": "PARS",
                    "portOfEntry": str(row.get("CBSA_Port_of_Release", "")).strip().zfill(4),
                    "releaseOffice": str(row.get("CBSA_Port_of_Release", "")).strip().zfill(4),
                    "estimatedArrivalDate": arrival_datetime,
                    "estimatedArrivalTimeZone": "EST",
                    "cityOfLoading": {
                        "cityName": row.get("Seller_city", ""),
                        "stateProvince": row.get("Seller_state", "")
                    },
                    "shipper": {
                        "name": row.get("Seller_name", ""),
                        "address": {
                            "addressLine": row.get("Seller_address", ""),
                            "city": row.get("Seller_city", ""),
                            "stateProvince": row.get("Seller_state", ""),
                            "stateProvinceName": row.get("Shipper State Name", ""),
                            "country": row.get("Seller_country", ""),
                            "countryName": "United States",
                            "postalCode": row.get("Seller_postal_code", "")
                        }
                    },
                    "consignee": {
                        "name": row.get("Buyer_name", ""),
                        "address": {
                            "addressLine": row.get("Buyer_address", ""),
                            "city": row.get("Buyer_city", ""),
                            "stateProvince": row.get("Buyer_province", ""),
                            "stateProvinceName": row.get("Consignee Prov Name", ""),
                            "country": row.get("Buyer_country", ""),
                            "countryName": "Canada",
                            "postalCode": str(row.get("Buyer_postal_code", "")).strip().zfill(5)
                        }
                    },
                    "commodities": []
                }

            commodity = {
                "description": clean_description(row.get("Goods_Description", "")),
                "quantity": int(float(row.get("Quantity", 0) or 0)),
                "packagingUnit": "PCE",
                "weight": row.get("Parcel_item_weight", ""),
                "weightUnit": row.get("Parcel_item_weight_UOM", "")
            }

            shipments[ccn]["commodities"].append(commodity)

        # 🔥 OVERWRITE JSON EVERY TIME
        st.session_state.json_output = json.dumps(list(shipments.values()), indent=4)

        st.success("JSON generated (check preview below)")

    # ---------------- OUTPUT ----------------
    if st.session_state.json_output:

        st.subheader("JSON Preview")
        st.code(st.session_state.json_output, language="json")

        output_filename = f"{uploaded_file.name.rsplit('.', 1)[0]}_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.json"

        st.download_button(
            "📥 Download JSON File",
            data=st.session_state.json_output,
            file_name=output_filename,
            mime="application/json"
        )

    
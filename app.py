import streamlit as st

import uuid
import sqlite3
from datetime import datetime

from utils.theme import load_css

from modules import (
    #candata,
    apc,
    amazon_xml,
    amazon_aci_json,
    #amazon_xml_gets,
    apc_billing,
    apc_billing_header_report,
    apc_client_details,
    #aci_json,
    defender,
    #Item_report,
    spliptpdf,
    #analytics_dashboard,
    apc_pallet_id,
    #airshipment,
    #prohibited,
    #test_sharepoint,
    #excelmerger,
    #gst,
    #candata_to_gets_format,
    compresspdf,
    #bandofcanada,
    #amazon_xml_old,
    #vendor,
    
)


# --------PAGE CONFIG----------

st.set_page_config(
    page_title="ACB Enterprise Portal",
    page_icon="assets/qwe1.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------LOAD THEME----------
load_css()

# -------------STATE-----------
if "module" not in st.session_state:
    st.session_state.module = "HOME"

if "active_group" not in st.session_state:
    st.session_state.active_group = None

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ---- SIDEBAR NAVIGATION (ENTERPRISE STYLE) ----------

NAV_GROUPS = {

    "🚚 APC": {
        "🚚 APC sFTP": "APC",
        "💳 APC BILLING DETAIL": "APC_BILLING",
        "💳 APC CLIENT DETAILS": "APC_CLIENT_DETAILS",
        "💳 APC BILLING HEADER": "APC_BILLING_HEADER",
        "📦 APC PALLET ID": "APC_PALLET_ID",
    },

    "📦 AMAZON": {
        "📊 AMAZON XML TO CANDATA": "AMAZON_XML",
        "📦 AMAZON ACI JSON": "AMAZON_ACI_JSON",
    },
    
    "📊 Data Processing": {
        "📊 CANDATA UPLOAD FILE": "CANDATA",
        "📦 ACI JSON": "ACI_JSON",
        "✈️ AIR SHIPMENT":"AIRSHIPMENT",
        "📄 PROHIBITED ITEM DETECTION":"PROHIBITED",
    },

    "🛠 Utilities": {
        "🛡️ DEFENDER": "DEFENDER",
        "📑 Split PDF": "SPLIT_PDF",
        "📦 Compress PDF": "compresspdf",
        "📊 EZCLEAR": "Item_report",
    }
}


st.sidebar.title("☰ MENU")
st.sidebar.caption("NAVIGATION")

for group_name, items in NAV_GROUPS.items():

    is_open = st.session_state.active_group == group_name

    with st.sidebar.expander(group_name, expanded=is_open):

        for label, module in items.items():

            if st.button(
                label,
                key=f"{group_name}_{module}"
            ):

                st.session_state.module = module
                st.session_state.active_group = group_name
                st.rerun()

MODULES = {
    
    "AMAZON_XML": amazon_xml.run,
    "AMAZON_ACI_JSON": amazon_aci_json.run,
    #"AMAZON_XML_GETS": amazon_xml_gets.run,

    #"CANDATA": candata.run,
    #"ACI_JSON": aci_json.run,
    #"AIRSHIPMENT": airshipment.run,

    "APC": apc.run,
    "APC_BILLING": apc_billing.run,
    "APC_CLIENT_DETAILS": apc_client_details.run,
    "APC_BILLING_HEADER": apc_billing_header_report.run,
    "APC_PALLET_ID": apc_pallet_id.run,

    "DEFENDER": defender.run,
    "SPLIT_PDF": spliptpdf.run,
    #"Item_report": Item_report.run,
    #"DASHBOARD": analytics_dashboard.run,
    #"PROHIBITED": prohibited.run,
    #"test_sharepoint": test_sharepoint.run,

    #"excelmerger": excelmerger.run,
    #"gst": gst.run,
    #"candata_to_gets_format": candata_to_gets_format.run,
    "compresspdf": compresspdf.run,
}

# ---------------- HOME PAGE ----------------
if st.session_state.module == "HOME":
    
    st.markdown('<div class="main-header">🚀 ACB Enterprise Portal</div>', unsafe_allow_html=True)
    st.caption('<div class="sub-header">Centralized Automation & Validation System</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        Welcome to ACB Toolkit. Select a module from the sidebar to begin processing.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")
else:

    module = st.session_state.module

    if module in MODULES:
        try:
            MODULES[module]()
        except Exception as e:
            st.error(f"Failed loading {module}")
            st.exception(e)

    else:
        st.error(f"Module {module} not registered")
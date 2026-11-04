from datetime import datetime
import io
import re
from openpyxl.styles import Font, PatternFill
import pandas as pd
import streamlit as st

# ============================================================
# TARGET SCHEMA DEFINITIONS
# ============================================================

INVOICE_COLUMNS = [
    "Operation",
    "Invoice Number",
    "Invoice Date",
    "Exportation Country",
    "Exportation State",
    "Direct Shipment Date",
    "Direct Shipment Country",
    "Direct Shipment State",
    "Foreign Registered Facility",
    "Foreign Facility State",
    "Invoice Total Amount",
    "Total Addition",
    "Total Deduction",
    "Currency",
    "Exchange Rate",
    "Invoice Quantity",
    "Invoice Quantity UOM",
    "Weight / Volume",
    "Weight / Volume UOM",
    "Measured Attribute",
    "US Exit Port",
    "Time Limit",
    "Time Limit Unit",
    "Value for Duty Code",
    "Freight Charges",
    "Cargo Control Number",
    # Delivery Party
    "Delivery Party Identifier",
    "Delivery Party Name",
    "Delivery Party Address",
    "Delivery Party City",
    "Delivery Party Postal Code",
    "Delivery Party State",
    "Delivery Party Country",
    "Delivery Party Info Contact Name",
    "Delivery Party Info Email",
    "Delivery Party Info Fax",
    "Delivery Party Info Phone",
    "Delivery Party Coord Contact Name",
    "Delivery Party Coord Email",
    "Delivery Party Coord Fax",
    "Delivery Party Coord Phone",
    # Ultimate Consignee
    "Consignee Identifier",
    "Consignee Name",
    "Consignee Address",
    "Consignee City",
    "Consignee Postal Code",
    "Consignee State",
    "Consignee Country",
    "Consignee Info Contact Name",
    "Consignee Info Email",
    "Consignee Info Fax",
    "Consignee Info Phone",
    "Consignee Coord Contact Name",
    "Consignee Coord Email",
    "Consignee Coord Fax",
    "Consignee Coord Phone",
    # Vendor
    "Vendor Identifier",
    "Vendor Name",
    "Vendor Address",
    "Vendor City",
    "Vendor Postal Code",
    "Vendor State",
    "Vendor Country",
    "Vendor Info Contact Name",
    "Vendor Info Email",
    "Vendor Info Fax",
    "Vendor Info Phone",
    "Vendor Coord Contact Name",
    "Vendor Coord Email",
    "Vendor Coord Fax",
    "Vendor Coord Phone",
    # Additional Header / Customs fields
    "Importer party id",
    "AutoCalc Provincial Rate",
    "CBSA Port of Release",
    "CBSA Warehouse Sub Location Code",
    "Port of Discharge",
    "Port of Discharge Sublocation Code",
    "IID Y/N",
    "PGA Flag",
    "Category",
    "BOL #",
    "Carrier code",
    "Manifest Only",
    "Movement Type",
    "TARIFF TREATMENT CODE",
    "External Reference 2",
    "GST CODE",
    "Container",
]

ITEMS_COLUMNS = [
    "Operation",
    "Invoice Number",
    "Classification No*",
    "Item Description*",
    "Tariff Treatment Code",
    "B3 Weight Quantity*",
    "Unit Price*",
    "Goods Total Value*",
    "Country of Origin*",
    "State of Origin",
    "Inner Quantity",
    "Inner UOM",
    "Intermediate Quantity",
    "Intermediate UOM",
    "Outer Quantity",
    "Outer UOM",
    "No hierarchy quantity",
    "No hierarchy uom",
    "Converted quantity",
    "Actual UOM",
    "Shipping Mark Description",
    "Item Net Weight",
    "Item Net Weight UOM",
    "Item Gross Weight",
    "Item Gross Weight UOM",
    "Unit Weight",
    "Unit Weight UOM",
    "Unit Volume",
    "Unit Volume UOM",
    "Radioactivity",
    "Radioactivity UOM",
    "PGA/Attention Required",
    # CFIA
    "CFIA Program Code",
    "CFIA AIRS Extension Code",
    "CFIA AIRS End Use",
    "CFIA AIRS Miscellaneous",
    # CNSC
    "CNSC Program Code",
    "CNSC UNDG",
    "CNSC Chemical Specification",
    # DFO
    "DFO Program Code",
    "DFO Intended Use",
    "DFO Trade Mark Name",
    "DFO Common Name",
    "DFO Model Name",
    "DFO Genus/ species name",
    "DFO Life Stage",
    "DFO Gender",
    "DFO Taxonomic Serial Number",
    "DFO Name of Commission",
    "DFO Genetic Modification Indicator",
    "DFO Genetic Modification Description",
    "DFO Gene(s) Nucleotide Sequence",
    "DFO Purpose of Genetic Modification",
    "DFO Compliance Statement",
    # ECCC
    "ECCC Program Code",
    "ECCC Intended Use Code",
    "ECCC CAS Registry Number",
    "ECCC Purpose",
    "ECCC Common Name",
    "ECCC Scientific Name",
    "ECCC Age",
    "ECCC Life Stage",
    "ECCC Gender",
    "ECCC Identification Tag, affixed",
    "ECCC Identification Tattoo",
    "ECCC Authority Registered Number",
    "ECCC Identification Wingband",
    "ECCC Leg Band",
    "ECCC Marking/label number",
    "ECCC Taxonomic Serial Number",
    "ECCC AphiaID",
    "ECCC Source of the Specimen",
    "ECCC Identification of ECCC Regulated Goods",
    "ECCC Make of Machine",
    "ECCC Model of Machine",
    "ECCC Model Year of Machine",
    "ECCC Make of Vehicle",
    "ECCC Model of Vehicle",
    "ECCC Vehicle Identification Number",
    "ECCC Model Year of Vehicle",
    "ECCC Make of Engine",
    "ECCC Model of Engine",
    "ECCC Model Year of Engine",
    "ECCC Engine Manufacturer",
    "ECCC Engine Power Rating",
    "ECCC Engine Identification Number",
    "ECCC Engine Family Name",
    "ECCC Vehicle Test Group",
    "ECCC Evaporative Family Name",
    "ECCC - Vehicle Class",
    "ECCC - Engine Class",
    "ECCC Exception Processes",
    "ECCC Identification of ECCC Regulated Goods 2",
    "ECCC Compliance Statement",
    # GAC
    "GAC Program Code",
    "GAC Free Trade Agreement Processing Code",
    "GAC Annex Code",
    "GAC Exception Processes",
    "GAC Compliance Statement",
    # HC
    "HC Program Code",
    "HC Commodity Type",
    "HC UNDG",
    "HC Intended Use",
    "HC Compliance Statement",
    "HC Product Name",
    "HC Brand Name",
    "HC CAS Name",
    "HC Model Number",
    "HC Model Designation",
    "HC GS1 Global Trade Identification Number",
    "HC FDA Product Code",
    "HC Exception Processes",
    # NRCan DG
    "NRCan Program Code",
    "NRCan UNDG",
    "NRCan Commodity Type",
    "NRCan Purpose",
    "NRCan Product Name",
    "NRCan Brand Name",
    "NRCan Model Name",
    "NRCan Authorized Product Identifier",
    "NRCan Authorized Product Name",
    # PHAC
    "PHAC Program Code",
    "PHAC UNDG",
    "PHAC Intended Use",
    "PHAC Commodity Type",
    "PHAC Exception Processes",
    # TC
    "TC Program Code",
    "TC Reason for Import",
    "TC Brand Name",
    "TC Tire Class",
    "TC Tire Type",
    "TC Tire Size",
    "TC Make of Vehicle",
    "TC Model of Vehicle",
    "TC Vehicle Class",
    "TC Vehicle Identification Number",
    "TC Model Year",
    "TC Vehicle Condition",
    "TC Vehicle Title Status",
    "TC Vehicle Status",
    "TC Chassis Manufacturer",
    "TC Chassis Make",
    "TC Chassis Model",
    "TC Chassis Year",
    "TC Vehicle Mileage(kms)",
    "TC Importer Language",
    "TC Compliance Statement",
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_header(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())

def clean_invoice_number(val) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip()

def safe_float(val) -> float:
    try:
        if pd.isna(val):
            return 0.0
        cleaned = re.sub(r"[^\d.-]", "", str(val))
        return float(cleaned) if cleaned else 0.0
    except Exception:
        return 0.0

def find_column(df: pd.DataFrame, candidates: list):
    source_lookup = {normalize_header(c): c for c in df.columns}
    for cand in candidates:
        norm = normalize_header(cand)
        if norm in source_lookup:
            return source_lookup[norm]
    return None

# ============================================================
# DATA TRANSFORMATION LOGIC
# ============================================================

def process_data(source_df: pd.DataFrame):
    inv_col = find_column(
        source_df,
        [
            "Client_Internal_tracking",
            "Client Internal tracking",
            "Order_number",
            "Invoice_Number",
        ],
    )
    if not inv_col:
        inv_col = source_df.columns[0]

    order_num_col = find_column(source_df, ["Order_Number", "Order Number"])
    ccn_col = find_column(
        source_df, ["Reliable_tracking", "Reliable tracking", "CCN"]
    )
    total_val_col = find_column(
        source_df, ["Total_value_of_item", "Total value of item"]
    )
    qty_col = find_column(source_df, ["Quantity"])
    weight_col = find_column(
        source_df, ["Parcel_item_weight", "Parcel item weight"]
    )
    weight_uom_col = find_column(
        source_df, ["Parcel_item_weight_UOM", "Parcel item weight UOM"]
    )

    qty_uom_col = find_column(source_df, ["Quantity_UOM", "Quantity UOM"])
    converted_qty_col = find_column(
        source_df, ["Converted_Quantity", "Converted Quantity"]
    )
    uom_qty_col = find_column(source_df, ["UOM_Quantity", "UOM Quantity"])

    # Seller fields
    s_country = find_column(source_df, ["Seller_country", "Seller country"])
    s_state = find_column(source_df, ["Seller_state", "Seller state"])
    s_name = find_column(source_df, ["Seller_name", "Seller name"])
    s_addr = find_column(source_df, ["Seller_address", "Seller address"])
    s_city = find_column(source_df, ["Seller_city", "Seller city"])
    s_postal = find_column(
        source_df, ["Seller_postal_code", "Seller postal code"]
    )

    # Buyer fields
    b_name = find_column(source_df, ["Buyer_name", "Buyer name"])
    b_addr = find_column(source_df, ["Buyer_address", "Buyer address"])
    b_city = find_column(source_df, ["Buyer_city", "Buyer city"])
    b_postal = find_column(
        source_df, ["Buyer_postal_code", "Buyer postal code"]
    )
    b_state = find_column(source_df, ["Buyer_province", "Buyer state", "State"])
    b_country = find_column(source_df, ["Buyer_country", "Buyer country"])

    # Item fields
    hs_col = find_column(source_df, ["HS_code", "Classification No"])
    desc_col = find_column(
        source_df, ["Goods_Description", "Item Description", "Description"]
    )
    tariff_col = find_column(
        source_df, ["TARIFF_TREATMENT_CODE", "Tariff Treatment Code"]
    )
    unit_price_col = find_column(source_df, ["Unit_price", "Unit Price"])
    origin_col = find_column(
        source_df, ["Country_of_origin", "Country of Origin"]
    )

    working_df = source_df.copy()

    # Clean tracking and seller names
    working_df["CleanInvoiceNo"] = working_df[inv_col].apply(clean_invoice_number)

    if s_name:
        working_df["CleanSellerName"] = (
            working_df[s_name].fillna("").astype(str).str.strip()
        )
    else:
        raise ValueError("Seller Name column was not found.")

    # Validation tracking metrics
    total_source_rows = len(working_df)
    blank_tracking_count = int(working_df["CleanInvoiceNo"].eq("").sum())
    blank_seller_count = int(working_df["CleanSellerName"].eq("").sum())

    # Build unique invoice groups based on Client Internal Tracking + Seller Name
    unique_invoice_groups = (
        working_df.loc[
            working_df["CleanInvoiceNo"].ne("") & working_df["CleanSellerName"].ne(""),
            ["CleanInvoiceNo", "CleanSellerName"]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Map sequential invoice numbers
    invoice_number_mapping = {}
    for index, group_row in unique_invoice_groups.iterrows():
        key = (group_row["CleanInvoiceNo"], group_row["CleanSellerName"])
        invoice_number_mapping[key] = f"AMZ{index:03d}"

    working_df["GeneratedInvoiceNo"] = working_df.apply(
        lambda row: invoice_number_mapping.get(
            (row["CleanInvoiceNo"], row["CleanSellerName"]), ""
        ),
        axis=1,
    )

    # ---------------------------------------------------------
    # BUILD ITEMS SHEET
    # ---------------------------------------------------------
    items_rows = []
    for _, row in working_df.iterrows():
        item_row = {col: "" for col in ITEMS_COLUMNS}
        item_row["Operation"] = "ADD"
        item_row["Invoice Number"] = row["GeneratedInvoiceNo"]
        item_row["Classification No*"] = str(row[hs_col]) if hs_col and not pd.isna(row[hs_col]) else ""
        item_row["Item Description*"] = str(row[desc_col]) if desc_col and not pd.isna(row[desc_col]) else ""
        item_row["Tariff Treatment Code"] = str(row[tariff_col]) if tariff_col and not pd.isna(row[tariff_col]) else ""
        item_row["B3 Weight Quantity*"] = str(row[weight_col]) if weight_col and not pd.isna(row[weight_col]) else ""
        item_row["Unit Price*"] = str(row[unit_price_col]) if unit_price_col and not pd.isna(row[unit_price_col]) else ""
        item_row["Goods Total Value*"] = str(row[total_val_col]) if total_val_col and not pd.isna(row[total_val_col]) else ""
        item_row["Country of Origin*"] = str(row[origin_col]) if origin_col and not pd.isna(row[origin_col]) else ""
        #item_row["State of Origin"] = str(row[s_state]) if s_state and not pd.isna(row[s_state]) else "" # Remove in favor of "Country of Origin" if not applicable
        item_row["No hierarchy quantity"] = str(row[qty_col]) if qty_col and not pd.isna(row[qty_col]) else ""
        
        if qty_uom_col and not pd.isna(row[qty_uom_col]):
            item_row["No hierarchy uom"] = str(row[qty_uom_col])
        if converted_qty_col and not pd.isna(row[converted_qty_col]):
            item_row["Converted quantity"] = str(row[converted_qty_col])
        if uom_qty_col and not pd.isna(row[uom_qty_col]):
            item_row["Actual UOM"] = str(row[uom_qty_col])

        item_row["Item Net Weight"] = str(row[weight_col]) if weight_col and not pd.isna(row[weight_col]) else ""
        item_row["Item Net Weight UOM"] = str(row[weight_uom_col]) if weight_uom_col and not pd.isna(row[weight_uom_col]) else ""
        items_rows.append(item_row)

    items_df = pd.DataFrame(items_rows, columns=ITEMS_COLUMNS)

    # ---------------------------------------------------------
    # BUILD INVOICES SHEET
    # ---------------------------------------------------------
    invoices_rows = []
    invoice_groups = working_df.groupby(
        ["CleanInvoiceNo", "CleanSellerName"], sort=False, dropna=False
    )

    for (inv_no, seller_name), group in invoice_groups:
        if not inv_no:
            continue

        first_row = group.iloc[0]

        total_amount = group[total_val_col].apply(safe_float).sum() if total_val_col else 0.0
        total_qty = group[qty_col].apply(safe_float).sum() if qty_col else 0.0
        total_weight = group[weight_col].apply(safe_float).sum() if weight_col else 0.0

        w_uom = str(first_row[weight_uom_col]) if weight_uom_col and not pd.isna(first_row[weight_uom_col]) else ""

        def get_val(row, col):
            if col is None or pd.isna(row[col]):
                return ""
            return str(row[col]).strip()

        country_val = get_val(first_row, s_country)
        state_val = get_val(first_row, s_state)
        carrier_code_col = find_column(source_df, ["Carrier code", "Carrier_code"])
        carrier_code = get_val(first_row, carrier_code_col)
        reliable_tracking = get_val(first_row, ccn_col)
        ccn = f"{carrier_code}{reliable_tracking}" if (carrier_code or reliable_tracking) else get_val(first_row, order_num_col)

        inv_row = {col: "" for col in INVOICE_COLUMNS}
        inv_row["Operation"] = "ADD"
        inv_row["Invoice Number"] = invoice_number_mapping.get((inv_no, seller_name), "")
        #inv_row["Exportation Country"] = country_val #Pickup State
        inv_row["Exportation State"] = state_val
        inv_row["Direct Shipment Country"] = country_val
        #inv_row["Direct Shipment State"] = state_val #Pickup State
        inv_row["Invoice Total Amount"] = total_amount
        inv_row["Currency"] = "USD"
        inv_row["Invoice Quantity"] = total_qty
        inv_row["Weight / Volume"] = total_weight
        inv_row["Weight / Volume UOM"] = w_uom
        inv_row["Value for Duty Code"] = "13"
        inv_row["Cargo Control Number"] = ccn

        buyer_name = get_val(first_row, b_name)
        buyer_addr = get_val(first_row, b_addr)
        buyer_city = get_val(first_row, b_city)
        buyer_postal = get_val(first_row, b_postal)
        buyer_state = get_val(first_row, b_state)
        buyer_country = get_val(first_row, b_country)

        # Delivery Party
        inv_row["Delivery Party Name"] = buyer_name
        inv_row["Delivery Party Address"] = buyer_addr
        inv_row["Delivery Party City"] = buyer_city
        inv_row["Delivery Party Postal Code"] = buyer_postal
        inv_row["Delivery Party State"] = buyer_state
        inv_row["Delivery Party Country"] = buyer_country
        inv_row["Delivery Party Info Contact Name"] = buyer_name
        inv_row["Delivery Party Info Email"] = "email@email.com"
        inv_row["Delivery Party Info Fax"] = "555-555-5555"
        inv_row["Delivery Party Info Phone"] = "555-555-5555"

        # Consignee
        inv_row["Consignee Name"] = buyer_name
        inv_row["Consignee Address"] = buyer_addr
        inv_row["Consignee City"] = buyer_city
        inv_row["Consignee Postal Code"] = buyer_postal
        inv_row["Consignee State"] = buyer_state
        inv_row["Consignee Country"] = buyer_country
        inv_row["Consignee Info Contact Name"] = buyer_name
        inv_row["Consignee Info Email"] = "email@email.com"
        inv_row["Consignee Info Fax"] = "555-555-5555"
        inv_row["Consignee Info Phone"] = "555-555-5555"

        # Vendor
        inv_row["Vendor Name"] = seller_name
        inv_row["Vendor Address"] = get_val(first_row, s_addr)
        inv_row["Vendor City"] = get_val(first_row, s_city)
        inv_row["Vendor Postal Code"] = get_val(first_row, s_postal)
        inv_row["Vendor State"] = state_val
        inv_row["Vendor Country"] = country_val
        inv_row["Vendor Info Contact Name"] = seller_name
        inv_row["Vendor Info Email"] = "email@email.com"
        inv_row["Vendor Info Fax"] = "555-555-5555"
        inv_row["Vendor Info Phone"] = "555-555-5555"

        additional_fields_mapping = {
            "Importer party id": ["Importer_party_id", "Importer party id"],
            "AutoCalc Provincial Rate": ["AutoCalc_Provincial_Rate", "AutoCalc Provincial Rate"],
            "CBSA Port of Release": ["CBSA_Port_of_Release", "CBSA Port of Release"],
            "CBSA Warehouse Sub Location Code": ["CBSA_Warehouse_Sub_Location_Code", "CBSA Warehouse Sub Location Code"],
            "Port of Discharge": ["Port_of_Discharge", "Port of Discharge"],
            "Port of Discharge Sublocation Code": ["Port_of_Discharge_Sublocation Code", "Port of Discharge Sublocation Code"],
            "IID Y/N": ["IID_Y/N", "IID Y/N"],
            "PGA Flag": ["PGA Flag", "PGA_Flag"],
            "Category": ["Category"],
            "BOL #": ["MAWB #", "BOL #", "MAWB"],
            "Carrier code": ["Carrier code", "Carrier_code"],
            "Manifest Only": ["Manifest Only", "Manifest_Only"],
            "Movement Type": ["Movement Type", "Movement_Type"],
            "TARIFF TREATMENT CODE": ["TARIFF_TREATMENT_CODE", "Tariff Treatment Code"],
            "External Reference 2": ["External Reference 2", "External_Reference_2"],
            "GST CODE": ["GST CODE", "GST_CODE"],
            "Container": ["Container"],
        }

        for target_field, candidates in additional_fields_mapping.items():
            src_col = find_column(source_df, candidates)
            if src_col and not pd.isna(first_row[src_col]):
                val_str = str(first_row[src_col]).strip()
                if target_field == "CBSA Port of Release":
                    val_str = val_str.zfill(4)
                inv_row[target_field] = val_str

        invoices_rows.append(inv_row)

    invoices_df = pd.DataFrame(invoices_rows, columns=INVOICE_COLUMNS)

    # Diagnostic metadata dictionary
    metrics = {
        "total_source_rows": total_source_rows,
        "unique_tracking_nos": working_df["CleanInvoiceNo"].nunique(),
        "unique_sellers": working_df["CleanSellerName"].nunique(),
        "unique_combinations": len(unique_invoice_groups),
        "generated_invoices": len(invoices_df),
        "generated_items": len(items_df),
        "blank_tracking": blank_tracking_count,
        "blank_sellers": blank_seller_count,
    }

    return invoices_df, items_df, metrics

def build_excel_workbook(invoices_df, items_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        invoices_df.to_excel(writer, sheet_name="Invoices", index=False)
        items_df.to_excel(writer, sheet_name="Items", index=False)

        header_fill = PatternFill(fill_type="solid", fgColor="1F4E78")
        header_font = Font(bold=True, color="FFFFFF")

        for sheet_name in ["Invoices", "Items"]:
            ws = writer.sheets[sheet_name]
            ws.auto_filter.ref = ws.dimensions
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font

    return output.getvalue()

# ============================================================
# STREAMLIT UI APP
# ============================================================

def run():
    st.set_page_config(
        page_title="Customs Automation Mapping Tool",
        layout="wide",
    )

    st.subheader("📦 Customs Invoice & Item Mapping Automation")
    st.info(
        "Upload your source data file to automatically transform and map it into "
        "the two-sheet template (**Invoices** & **Items**)."
    )

    uploaded_file = st.file_uploader(
        "Upload Source File (Excel or CSV)", type=["xlsx", "xls", "csv"]
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                source_df = pd.read_csv(uploaded_file)
            else:
                source_df = pd.read_excel(uploaded_file)

            st.success(
                f"Successfully loaded `{uploaded_file.name}` with {len(source_df)} rows."
            )

            with st.spinner("Processing and mapping data..."):
                invoices_result, items_result, metrics = process_data(source_df)

            # Summary Dashboard Section
            st.markdown("### 📊 Summary Dashboard")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Source Records", metrics["total_source_rows"])
            col2.metric("Unique Tracking Numbers", metrics["unique_tracking_nos"])
            col3.metric("Unique Sellers", metrics["unique_sellers"])
            col4.metric("Tracking + Seller Pairs", metrics["unique_combinations"])

            col5, col6 = st.columns(2)
            col5.metric("Generated Invoices", metrics["generated_invoices"])
            col6.metric("Generated Items", metrics["generated_items"])

            # Validation Report Section
            if metrics["blank_tracking"] > 0 or metrics["blank_sellers"] > 0:
                st.warning(
                    f"⚠️ **Validation Notice:** Found **{metrics['blank_tracking']}** blank tracking numbers "
                    f"and **{metrics['blank_sellers']}** blank seller names in the source dataset."
                )
            else:
                st.success("✅ **Validation Report:** All records contain valid tracking numbers and seller names.")

            st.markdown("---")
            st.subheader("📊 Preview: Invoices Sheet (Unique per Tracking + Seller)")
            st.dataframe(invoices_result, use_container_width=True)

            st.subheader("📊 Preview: Items Sheet (All Items Preserved)")
            st.dataframe(items_result, use_container_width=True)

            excel_data = build_excel_workbook(invoices_result, items_result)

            st.download_button(
                label="⬇️ Download Final Two-Sheet Excel Workbook",
                data=excel_data,
                file_name="B2B2C_AMAZON_CUSTOMS_INVOICE_ITEMS.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"Error processing file: {e}")

if __name__ == "__main__":
    run()
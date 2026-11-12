import datetime
import io
import os
import sqlite3
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import streamlit as st
from fpdf import FPDF

# --- DATABASE SETUP ---
DB_FILE = "reliable_logistics.db"

def init_rl_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rl_headers (
            reference_no TEXT PRIMARY KEY,
            date TEXT,
            shipper TEXT,
            consignee TEXT,
            bill_to TEXT,
            origin TEXT,
            destination TEXT,
            carrier TEXT,
            sub_total REAL,
            total_amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rl_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_no TEXT,
            pay_to TEXT,
            cost REAL,
            details TEXT,
            qty INTEGER,
            unit_price REAL,
            total REAL,
            FOREIGN KEY (reference_no) REFERENCES rl_headers(reference_no)
        )
    """)
    conn.commit()
    conn.close()

def generate_default_reference_no():
    init_rl_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    current_year = datetime.date.today().strftime("%Y")
    prefix = f"03X-{current_year}-"
    
    cursor.execute("SELECT reference_no FROM rl_headers WHERE reference_no LIKE ?", (f"{prefix}%",))
    results = cursor.fetchall()
    conn.close()

    max_seq = 0
    for row in results:
        parts = row[0].split("-")
        if len(parts) == 3 and parts[2].isdigit():
            seq_num = int(parts[2])
            if seq_num > max_seq:
                max_seq = seq_num

    next_seq = max_seq + 1
    return f"03X-{next_seq:06d}-0"


# --- EXCEL GENERATOR (Exact Layout Match) ---
def generate_excel_bytes(reference_no, inv_date_str, shipper, consignee, bill_to, origin, destination, carrier, line_items, sub_total, total_amount):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reliable Logistics Invoice"
    ws.views.sheetView[0].showGridLines = True

    font_family = "Arial"
    header_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
    light_blue_fill = PatternFill(start_color="D2E6F0", end_color="D2E6F0", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )

    # Reference No & Date Alignment
    ws["A3"] = "REFERENCE NO:"
    ws["A3"].font = Font(name=font_family, size=9, bold=True)
    ws["A4"] = str(reference_no)
    ws["A4"].font = Font(name=font_family, size=9)

    ws["E3"] = "DATE:"
    ws["E3"].font = Font(name=font_family, size=9, bold=True)
    ws["E3"].alignment = Alignment(horizontal="right")
    ws["F3"] = str(inv_date_str)
    ws["F3"].font = Font(name=font_family, size=9)

    # Metadata Header Block matching layout
    ws["A6"] = "SHIPPER:"
    ws["A6"].font = Font(name=font_family, size=8, bold=True)
    ws["B6"] = shipper if shipper else ""
    ws["B6"].font = Font(name=font_family, size=8)

    ws["C6"] = "CONSIGNEE:"
    ws["C6"].font = Font(name=font_family, size=8, bold=True)
    ws["D6"] = consignee if consignee else ""
    ws["D6"].font = Font(name=font_family, size=8)

    ws["E6"] = "Bill To:"
    ws["E6"].font = Font(name=font_family, size=8, bold=True)
    ws["F6"] = bill_to if bill_to else ""
    ws["F6"].font = Font(name=font_family, size=8)

    ws["A7"] = "ORIGIN:"
    ws["A7"].font = Font(name=font_family, size=8, bold=True)
    ws["B7"] = origin if origin else ""
    ws["B7"].font = Font(name=font_family, size=8)

    ws["C7"] = "DESTINATION:"
    ws["C7"].font = Font(name=font_family, size=8, bold=True)
    ws["D7"] = destination if destination else ""
    ws["D7"].font = Font(name=font_family, size=8)

    ws["A9"] = "CARRIER/AIRLINE:"
    ws["A9"].font = Font(name=font_family, size=8, bold=True)
    ws["B9"] = carrier if carrier else ""
    ws["B9"].font = Font(name=font_family, size=8)

    # Table Headers (Row 11)
    headers = ["PAY TO:", "COST:", "DETAILS:", "QTY", "Unit Price", "TOTAL"]
    cols = ["A", "B", "C", "D", "E", "F"]
    for col, h in zip(cols, headers):
        cell = ws[f"{col}11"]
        cell.value = h
        cell.fill = header_fill
        cell.font = Font(name=font_family, size=9, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center" if col in ["D", "E", "F"] else "left", vertical="center")

    # Populate Line Items (Starting Row 12)
    for idx, item in enumerate(line_items, start=12):
        ws[f"A{idx}"] = item["Pay To"]
        ws[f"C{idx}"] = item["Details"]
        ws[f"D{idx}"] = item["Qty"]
        
        if item["Cost"] > 0:
            ws[f"B{idx}"] = item["Cost"]
            ws[f"B{idx}"].number_format = '$#,##0.00'
        else:
            ws[f"B{idx}"] = "-"
            ws[f"B{idx}"].alignment = Alignment(horizontal="center")

        if item["Unit Price"] > 0:
            ws[f"E{idx}"] = item["Unit Price"]
            ws[f"E{idx}"].number_format = '$#,##0.000'
        else:
            ws[f"E{idx}"] = "-"
            ws[f"E{idx}"].alignment = Alignment(horizontal="center")

        ws[f"F{idx}"] = f"=D{idx}*E{idx}" if item["Unit Price"] > 0 else "-"

        ws[f"A{idx}"].font = Font(name=font_family, size=8)
        ws[f"B{idx}"].font = Font(name=font_family, size=8)
        ws[f"C{idx}"].font = Font(name=font_family, size=8)
        ws[f"D{idx}"].font = Font(name=font_family, size=8)
        ws[f"D{idx}"].alignment = Alignment(horizontal="center")
        ws[f"E{idx}"].font = Font(name=font_family, size=8)
        ws[f"F{idx}"].font = Font(name=font_family, size=8)

        for c in cols:
            ws[f"{c}{idx}"].border = thin_border

    last_row = 11 + len(line_items)

    ws[f"A{last_row+1}"] = "Sub-Total of Services"
    ws.merge_cells(f"A{last_row+1}:E{last_row+1}")
    ws[f"A{last_row+1}"].alignment = Alignment(horizontal="right")
    ws[f"A{last_row+1}"].font = Font(name=font_family, size=9, bold=True)
    ws[f"F{last_row+1}"] = f"=SUM(F14:F{last_row})"
    ws[f"F{last_row+1}"].font = Font(name=font_family, size=9, bold=True)
    ws[f"F{last_row+1}"].number_format = '$#,##0.00'

    ws[f"A{last_row+2}"] = "Total Amount Due"
    ws.merge_cells(f"A{last_row+2}:E{last_row+2}")
    ws[f"A{last_row+2}"].alignment = Alignment(horizontal="right")
    ws[f"A{last_row+2}"].font = Font(name=font_family, size=9, bold=True, color="186982")
    ws[f"F{last_row+2}"] = f"=F{last_row+1}+F12+F13"
    ws[f"F{last_row+2}"].font = Font(name=font_family, size=9, bold=True, color="186982")
    ws[f"F{last_row+2}"].number_format = '$#,##0.00'
    ws[f"F{last_row+2}"].fill = light_blue_fill

    column_widths = {'A': 25, 'B': 14, 'C': 48, 'D': 8, 'E': 14, 'F': 16}
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# --- PDF GENERATION FUNCTION ---
def create_reliable_pdf(
    reference_no,
    inv_date_str,
    shipper,
    consignee,
    bill_to,
    origin,
    destination,
    carrier,
    line_items,
    sub_total,
    total_amount,
):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    # --- LOGO & HEADER ---
    if os.path.exists("assets/reliablelogistisca.png"):
        pdf.image("assets/reliablelogistisca.png", x=10, y=8, w=45)
        pdf.set_y(26)
    else:
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(15, 60, 110)
        pdf.cell(0, 6, "RELIABLE LOGISTICS", ln=1)
        pdf.set_y(26)

    pdf.set_text_color(0, 0, 0)
    
    # --- REFERENCE NO & DATE ROW ---
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(110, 5, "REFERENCE NO:", 0, 0)
    pdf.cell(0, 5, "DATE:", 0, 1)

    pdf.set_font("helvetica", "", 8.5)
    pdf.cell(110, 5, str(reference_no), 0, 0)
    pdf.cell(0, 5, str(inv_date_str), 0, 1)

    pdf.ln(4)

    # --- SHIPPER / CONSIGNEE / BILL TO BLOCK ---
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(20, 5, "SHIPPER:", 0, 0)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(70, 5, str(shipper if shipper else ""), 0, 0)

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(22, 5, "CONSIGNEE:", 0, 0)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(38, 5, str(consignee if consignee else ""), 0, 0)

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(15, 5, "Bill To:", 0, 0)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(0, 5, str(bill_to if bill_to else ""), 0, 1)

    # --- ORIGIN & DESTINATION BLOCK ---
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(20, 5, "ORIGIN:", 0, 0)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(70, 5, str(origin if origin else ""), 0, 0)

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(22, 5, "DESTINATION:", 0, 0)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(0, 5, str(destination if destination else ""), 0, 1)

    pdf.ln(1)

    # --- CARRIER / AIRLINE BLOCK ---
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(30, 5, "CARRIER/AIRLINE:", 0, 0)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(0, 5, str(carrier if carrier else ""), 0, 1)

    pdf.ln(6)

    # --- TABLE HEADERS ---
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_fill_color(25, 25, 25)
    pdf.set_text_color(255, 255, 255)

    pdf.cell(35, 6, "PAY TO:", 1, 0, "C", True)
    pdf.cell(22, 6, "COST:", 1, 0, "C", True)
    pdf.cell(63, 6, "DETAILS:", 1, 0, "C", True)
    pdf.cell(15, 6, "QTY", 1, 0, "C", True)
    pdf.cell(27, 6, "Unit Price", 1, 0, "C", True)
    pdf.cell(28, 6, "TOTAL", 1, 1, "C", True)

    # --- TABLE ROWS (Filtering out items with Total == 0 or '-') ---
    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(0, 0, 0)

    for item in line_items:
        # Skip printing rows where total is 0 or negative/empty
        if item['Total'] <= 0:
            continue

        cost_str = f"${item['Cost']:,.2f}" if item['Cost'] > 0 else "-"
        unit_str = f"${item['Unit Price']:,.2f}" if item['Unit Price'] > 0 else "-"
        tot_str = f"${item['Total']:,.2f}"

        pdf.cell(35, 5, str(item['Pay To']), 1, 0, "L")
        pdf.cell(22, 5, cost_str, 1, 0, "R" if item['Cost'] > 0 else "C")
        pdf.cell(63, 5, str(item['Details']), 1, 0, "L")
        pdf.cell(15, 5, str(item['Qty']), 1, 0, "C")
        pdf.cell(27, 5, unit_str, 1, 0, "R" if item['Unit Price'] > 0 else "C")
        pdf.cell(28, 5, tot_str, 1, 1, "R")

    # --- TOTALS SUMMARY ---
    pdf.set_font("helvetica", "B", 8.5)
    pdf.cell(162, 6, "Sub-Total of Services", 1, 0, "R")
    pdf.cell(28, 6, f"${sub_total:,.2f}", 1, 1, "R")

    pdf.cell(162, 6, "Total Amount Due", 1, 0, "R")
    pdf.cell(28, 6, f"${total_amount:,.2f}", 1, 1, "R")

    return bytes(pdf.output())


# --- STREAMLIT UI ROUTER FUNCTION ---
def run():
    if "rl_ref" not in st.session_state:
        st.session_state["rl_ref"] = generate_default_reference_no()

    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.subheader("📦 RELIABLE LOGISTICS INVOICE & BILLING FORM")
        st.markdown("*Manage shipping fees, duties, and disbursement charges.*")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 New Billing Entry", use_container_width=True):
            st.session_state["rl_ref"] = generate_default_reference_no()
            st.session_state["rl_submitted"] = False
            st.rerun()

    st.divider()

    with st.form("reliable_logistics_form"):
        col1, col2 = st.columns(2)
        with col1:
            reference_no = st.text_input("Reference No.", value=st.session_state["rl_ref"])
            shipper = st.text_input("Shipper")
            origin = st.text_input("Origin")
            carrier = st.text_input("Carrier / Airline")
        with col2:
            raw_date = st.date_input("Date", datetime.date.today())
            formatted_date = raw_date.strftime("%A, %B %d, %Y")
            st.markdown(f"**Formatted Date:** {formatted_date}")
            
            consignee = st.text_input("Consignee")
            destination = st.text_input("Destination")
            bill_to = st.text_input("Bill To")

        st.markdown("### BILLING & TARIFF DETAILS")

        standard_details = [
            ("Canada Revenue Agency", 0.0, "GST", 0, 0.0),
            ("Canada Revenue Agency", 4880.0, "Duties", 1, 4880.0),
            ("", 0.0, "Disbursement Fee", 1, 122.0),
            ("", 0.0, "Merchandise Processing Fee", 1, 84.52),
            ("", 0.0, "Harbor Maintenance Fee", 0, 0.0),
            ("", 0.0, "Brokerage Fee", 1, 125.0),
            ("", 0.0, "FDA Fee", 0, 25.0),
            ("", 0.0, "Prior Notice", 0, 25.0),
            ("", 0.0, "Additional lines after 5 lines", 1, 0.0),
            ("", 0.0, "One Time Account Set up Fee", 0, 50.0),
            ("", 0.0, "Single Entry Bond", 1, 450.0),
            ("", 0.0, "B2C Spreadsheet Mgmt (Change Counts)", 0, 10.0),
            ("", 0.0, "B2C Spreadsheet (Good Description)", 0, 10.5),
            ("", 0.0, "Manifest Forward Fee", 0, 8.5),
            ("", 0.0, "ACI Transmission Fee", 0, 2.0),
            ("", 0.0, "ACI Manifest Fee", 0, 15.0),
        ]

        header_cols = st.columns([2, 1.2, 3, 0.8, 1.2, 1.2])
        header_cols[0].markdown("**Pay To**")
        header_cols[1].markdown("**Cost ($)**")
        header_cols[2].markdown("**Details (Locked)**")
        header_cols[3].markdown("**Qty**")
        header_cols[4].markdown("**Unit Price ($)**")
        header_cols[5].markdown("**Total ($)**")

        line_items = []
        sub_total_services = 0.0
        duties_total = 0.0
        gst_total = 0.0

        for idx, (default_pay, default_cost, locked_det, default_qty, default_unit) in enumerate(standard_details):
            r_cols = st.columns([2, 1.2, 3, 0.8, 1.2, 1.2])

            with r_cols[0]:
                pay_to = st.text_input(f"pay_{idx}", value=default_pay, label_visibility="collapsed")
            with r_cols[1]:
                cost = st.number_input(f"cost_{idx}", value=float(default_cost), step=10.0, format="%.2f", label_visibility="collapsed")
            with r_cols[2]:
                st.markdown(f"**{locked_det}**")
                details = locked_det
            with r_cols[3]:
                qty = st.number_input(f"qty_{idx}", min_value=0, value=int(default_qty), step=1, label_visibility="collapsed")
            with r_cols[4]:
                unit_price = st.number_input(f"unit_{idx}", value=float(default_unit), step=1.0, format="%.3f", label_visibility="collapsed")
            with r_cols[5]:
                row_total = qty * unit_price
                if row_total > 0:
                    st.markdown(f"**${row_total:,.2f}**")
                else:
                    st.markdown("**-**")

            if details not in ["Duties", "GST"]:
                sub_total_services += row_total
            elif details == "Duties":
                duties_total += row_total
            elif details == "GST":
                gst_total += row_total

            line_items.append({
                "Pay To": pay_to,
                "Cost": cost,
                "Details": details,
                "Qty": qty,
                "Unit Price": unit_price,
                "Total": row_total
            })

        total_amount_due = sub_total_services + duties_total + gst_total

        st.divider()

        col_sum1, col_sum2 = st.columns([3, 1])
        with col_sum1:
            st.markdown("### Sub-Total of Services")
            st.markdown("### Total Amount Due")
        with col_sum2:
            st.markdown(f"### ${sub_total_services:,.2f}")
            st.markdown(f"### ${total_amount_due:,.2f}")

        submitted = st.form_submit_button("💾 Save & Generate Billing Records", use_container_width=True)

        if submitted:
            init_rl_db()
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO rl_headers 
                    (reference_no, date, shipper, consignee, bill_to, origin, destination, carrier, sub_total, total_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    reference_no, formatted_date, shipper, consignee, bill_to,
                    origin, destination, carrier, sub_total_services, total_amount_due
                ))

                cursor.execute("DELETE FROM rl_items WHERE reference_no = ?", (reference_no,))

                for item in line_items:
                    cursor.execute("""
                        INSERT INTO rl_items (reference_no, pay_to, cost, details, qty, unit_price, total)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        reference_no, item["Pay To"], item["Cost"],
                        item["Details"], item["Qty"], item["Unit Price"], item["Total"]
                    ))

                conn.commit()
                conn.close()
                st.success(f"Invoice {reference_no} successfully saved!")
                st.session_state["rl_submitted"] = True
                st.session_state["rl_pdf_data"] = {
                    "reference_no": reference_no, "date": formatted_date,
                    "shipper": shipper, "consignee": consignee, "bill_to": bill_to,
                    "origin": origin, "destination": destination, "carrier": carrier,
                    "line_items": line_items, "sub_total": sub_total_services, "total_amount": total_amount_due
                }
            except Exception as e:
                st.error(f"Database error: {e}")

    if st.session_state.get("rl_submitted", False) and "rl_pdf_data" in st.session_state:
        data = st.session_state["rl_pdf_data"]
        pdf_bytes = create_reliable_pdf(
            reference_no=data["reference_no"],
            inv_date_str=data["date"],
            shipper=data["shipper"],
            consignee=data["consignee"],
            bill_to=data["bill_to"],
            origin=data["origin"],
            destination=data["destination"],
            carrier=data["carrier"],
            line_items=data["line_items"],
            sub_total=data["sub_total"],
            total_amount=data["total_amount"]
        )

        excel_bytes = generate_excel_bytes(
            reference_no=data["reference_no"],
            inv_date_str=data["date"],
            shipper=data["shipper"],
            consignee=data["consignee"],
            bill_to=data["bill_to"],
            origin=data["origin"],
            destination=data["destination"],
            carrier=data["carrier"],
            line_items=data["line_items"],
            sub_total=data["sub_total"],
            total_amount=data["total_amount"]
        )

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 Download Secure Invoice PDF",
                data=pdf_bytes,
                file_name=f"{data['reference_no']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col_dl2:
            st.download_button(
                label="📊 Download Excel Spreadsheet (.xlsx)",
                data=excel_bytes,
                file_name=f"{data['reference_no']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

if __name__ == "__main__":
    st.set_page_config(page_title="Reliable Logistics Billing", page_icon="📦", layout="wide")
    run()
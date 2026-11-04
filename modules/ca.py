import datetime
import os
import sqlite3
import streamlit as st
from fpdf import FPDF

# --- DATABASE SETUP ---
DB_FILE = "cash_advance.db"

def init_ca_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ca_headers (
            ca_no TEXT PRIMARY KEY,
            requested_by TEXT,
            department TEXT,
            request_date TEXT,
            reason TEXT,
            date_needed TEXT,
            bank_name TEXT,
            account_no TEXT,
            account_name TEXT,
            designated_approver TEXT,
            custodian TEXT,
            total_funding REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ca_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ca_no TEXT,
            item_no INTEGER,
            description TEXT,
            quantity INTEGER,
            unit_cost REAL,
            total_cost REAL,
            FOREIGN KEY (ca_no) REFERENCES ca_headers(ca_no)
        )
    """)
    conn.commit()
    conn.close()

def generate_new_ca_no():
    init_ca_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    current_year = datetime.date.today().strftime("%Y")
    prefix = f"CA-{current_year}-"

    cursor.execute("SELECT ca_no FROM ca_headers WHERE ca_no LIKE ?", (f"{prefix}%",))
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
    return f"{prefix}{next_seq:03d}"


# --- PDF GENERATION FUNCTION ---
def create_ca_pdf(
    ca_no,
    requested_by,
    department,
    request_date,
    reason,
    date_needed,
    expense_items,
    grand_total,
    bank_name,
    account_no,
    account_name,
    approver,
    custodian,
):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    # --- LOGO / HEADER SECTION ---
    if os.path.exists("assets/ABS_logo.png"):
        pdf.image("assets/ABS_logo.png", x=80, y=8, w=50)
        pdf.ln(18)
    else:
        pdf.set_font("helvetica", "B", 16)
        pdf.set_text_color(24, 105, 130)
        pdf.cell(0, 6, "access", ln=True, align="C")
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, "Brokerage Support Inc.", ln=True, align="C")
        pdf.ln(4)

    pdf.set_text_color(0, 0, 0)

    # --- TITLE BANNER ---
    pdf.set_fill_color(24, 105, 130)  # Teal Header Bar
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, "CASH ADVANCE", 1, 1, "C", True)

    pdf.set_font("helvetica", "BI", 7.5)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 4.5, "Use for transactions P2,000 up to P15,000 per transaction.", 1, 1, "L", False)

    # --- METADATA BOXES ---
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(210, 230, 240)

    # Row 1
    pdf.cell(32, 5.5, "Requested by", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(63, 5.5, str(requested_by), 1, 0, "L")
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(32, 5.5, "CA No.", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(63, 5.5, str(ca_no), 1, 1, "L")

    # Row 2
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(32, 5.5, "Department/Team", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(63, 5.5, str(department), 1, 0, "L")
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(32, 5.5, "Request Date", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(63, 5.5, str(request_date), 1, 1, "L")

    # Row 3
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(32, 5.5, "Reason", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(63, 5.5, str(reason), 1, 0, "L")
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(32, 5.5, "Date Needed", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(63, 5.5, str(date_needed), 1, 1, "L")

    pdf.ln(3)

    # --- EXPENSE DETAILS TABLE HEADER ---
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(24, 105, 130)
    pdf.set_text_color(255, 255, 255)

    pdf.cell(10, 5.5, "#", 1, 0, "C", True)
    pdf.cell(85, 5.5, "Description", 1, 0, "C", True)
    pdf.cell(25, 5.5, "Quantity", 1, 0, "C", True)
    pdf.cell(40, 5.5, "Unit Cost", 1, 0, "C", True)
    pdf.cell(30, 5.5, "Total Cost", 1, 1, "C", True)

    # --- EXPENSE ROWS (10 rows) ---
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)

    for i in range(1, 11):
        matching_item = next((item for item in expense_items if item["No"] == i), None)
        desc = str(matching_item["Description"]) if matching_item else ""
        qty = str(matching_item["Quantity"]) if matching_item and matching_item["Quantity"] > 0 else ""
        unit_cost_val = matching_item["Unit Cost"] if matching_item else 0.0
        total_cost_val = matching_item["Total Cost"] if matching_item else 0.0

        unit_cost_str = f"{unit_cost_val:,.2f}" if unit_cost_val > 0 else ""
        total_cost_str = f"{total_cost_val:,.2f}" if total_cost_val > 0 else "-"

        pdf.cell(10, 5, str(i), 1, 0, "C")
        pdf.cell(85, 5, desc, 1, 0, "L")
        pdf.cell(25, 5, qty, 1, 0, "C")
        pdf.cell(40, 5, unit_cost_str, 1, 0, "R")
        pdf.cell(30, 5, total_cost_str, 1, 1, "R")

    # --- TOTAL ROW ---
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_fill_color(24, 105, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(160, 6, "TOTAL AMOUNT REQUESTED", 1, 0, "R", True)
    pdf.cell(30, 6, f"P{grand_total:,.2f}", 1, 1, "R", True)

    pdf.ln(3)

    # --- BANK DETAILS SECTION ---
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(24, 105, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 5.5, "Bank Details for Cash Advance Release", 1, 1, "C", True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "B", 8)
    
    pdf.cell(45, 5, "Bank Name:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(145, 5, str(bank_name), 1, 1, "L")

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(45, 5, "Account No.:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(145, 5, str(account_no), 1, 1, "L")

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(45, 5, "Account Name:", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(145, 5, str(account_name), 1, 1, "L")

    pdf.ln(3)

    # --- APPROVAL / RELEASE SECTION ---
    pdf.set_fill_color(24, 105, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.cell(0, 5.5, "APPROVAL / RELEASE", 1, 1, "C", True)

    pdf.cell(95, 5.5, "Designated Approver", 1, 0, "C", True)
    pdf.cell(95, 5.5, "Custodian", 1, 1, "C", True)

    pdf.ln(10)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(95, 4, f"{approver if approver else ''}", 0, 0, "C")
    pdf.cell(95, 4, f"{custodian if custodian else ''}", 0, 1, "C")

    pdf.cell(95, 4, "___________________________________", 0, 0, "C")
    pdf.cell(95, 4, "___________________________________", 0, 1, "C")

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(95, 4.5, "Name/Signature", 0, 0, "C")
    pdf.cell(95, 4.5, "Name/Signature", 0, 1, "C")

    return bytes(pdf.output())


# --- STREAMLIT UI ROUTER FUNCTION ---
def run():
    if "ca_no" not in st.session_state:
        st.session_state["ca_no"] = generate_new_ca_no()

    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.subheader("💳 CASH ADVANCE VOUCHER")
        st.markdown("*Use for transactions ₱2,000 up to ₱15,000 per transaction.*")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Create New CA", use_container_width=True):
            st.session_state["ca_no"] = generate_new_ca_no()
            st.session_state["ca_submitted"] = False
            if "ca_pdf_data" in st.session_state:
                del st.session_state["ca_pdf_data"]
            st.rerun()

    st.divider()

    with st.form("cash_advance_form"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            requested_by = st.text_input("Requested by")
        with col2:
            ca_no = st.text_input("CA No.", value=st.session_state["ca_no"], disabled=True)
        with col3:
            department = st.selectbox(
                "Department/Team",
                [
                    "Select Department",
                    "Finance",
                    "Operations",
                    "IT / Engineering",
                    "Marketing",
                    "Human Resources",
                    "Administration",
                ],
            )
        with col4:
            request_date = st.date_input("Request Date", datetime.date.today())

        col_r1, col_r2 = st.columns([2, 2])
        with col_r1:
            reason = st.text_input("Reason")
        with col_r2:
            date_needed = st.date_input("Date Needed", datetime.date.today() + datetime.timedelta(days=3))

        st.markdown("### EXPENSE DETAILS")

        header_cols = st.columns([0.5, 3.5, 1, 1.5, 1.5])
        header_cols[0].markdown("**#**")
        header_cols[1].markdown("**Description**")
        header_cols[2].markdown("**Quantity**")
        header_cols[3].markdown("**Unit Cost (₱)**")
        header_cols[4].markdown("**Total Cost (₱)**")

        expense_items = []
        grand_total = 0.0

        for i in range(1, 11):
            r_cols = st.columns([0.5, 3.5, 1, 1.5, 1.5])

            with r_cols[0]:
                st.markdown(f"**{i}**")
            with r_cols[1]:
                desc = st.text_input(f"CA_Desc_{i}", label_visibility="collapsed")
            with r_cols[2]:
                qty = st.number_input(f"CA_Qty_{i}", min_value=0, value=0, step=1, label_visibility="collapsed")
            with r_cols[3]:
                unit_cost = st.number_input(f"CA_Unit_{i}", min_value=0.0, value=0.0, step=10.0, format="%.2f", label_visibility="collapsed")

            total_cost = qty * unit_cost
            grand_total += total_cost

            with r_cols[4]:
                st.markdown(f"**₱ {total_cost:,.2f}**")

            expense_items.append({
                "No": i,
                "Description": desc,
                "Quantity": qty,
                "Unit Cost": unit_cost,
                "Total Cost": total_cost,
            })

        st.divider()

        col_tot1, col_tot2 = st.columns([3, 1])
        with col_tot1:
            st.markdown("### TOTAL AMOUNT REQUESTED")
        with col_tot2:
            st.markdown(f"### ₱ {grand_total:,.2f}")

        if grand_total > 0 and grand_total < 2000.00:
            st.warning("⚠️ Warning: Cash Advance total is below ₱2,000.00 (Consider using Petty Cash Voucher instead).")
        elif grand_total > 15000.00:
            st.warning("⚠️ Warning: Cash Advance total exceeds the ₱15,000.00 limit!")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Bank Details for Cash Advance Release")
        bank_name = st.text_input("Bank Name")
        account_no = st.text_input("Account No.")
        account_name = st.text_input("Account Name")

        st.markdown("<br>", unsafe_allow_html=True)
        sig_col1, sig_col2 = st.columns(2)
        with sig_col1:
            designated_approver = st.selectbox(
                "Designated Approver (Name/Signature)",
                [
                    "Select Approver",
                    "Tyler Upper",
                    "Wale Saka",
                ],
            )
            
        with sig_col2:
            custodian = st.selectbox(
                "Custodian (Name/Signature)",
                [
                    "Select Custodian",
                    "Dianna Kaye Casabuena",
                ],
            )

        submitted = st.form_submit_button("💾 Save & Generate Cash Advance PDF", use_container_width=True)

        if submitted:
            if department == "Select Department":
                st.error("Please select a valid Department/Team.")
            elif not requested_by:
                st.error("Please fill out the 'Requested by' field.")
            elif not reason:
                st.error("Please fill out the 'Reason' field.")
            elif grand_total > 15000.00:
                st.error(f"❌ Access Denied: Total funding (₱{grand_total:,.2f}) exceeds the maximum ₱15,000.00 limit.")
                st.session_state["ca_submitted"] = False
            else:
                init_ca_db()
                try:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT OR REPLACE INTO ca_headers 
                        (ca_no, requested_by, department, request_date, reason, date_needed, bank_name, account_no, account_name, designated_approver, custodian, total_funding)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        st.session_state["ca_no"], requested_by, department, str(request_date),
                        reason, str(date_needed), bank_name, account_no, account_name,
                        designated_approver, custodian, grand_total
                    ))

                    cursor.execute("DELETE FROM ca_items WHERE ca_no = ?", (st.session_state["ca_no"],))

                    for item in expense_items:
                        if item["Description"].strip() or item["Total Cost"] > 0:
                            cursor.execute("""
                                INSERT INTO ca_items (ca_no, item_no, description, quantity, unit_cost, total_cost)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                st.session_state["ca_no"], item["No"], item["Description"],
                                item["Quantity"], item["Unit Cost"], item["Total Cost"]
                            ))

                    conn.commit()
                    conn.close()
                    st.success(f"Cash Advance Voucher {st.session_state['ca_no']} saved successfully!")
                    st.session_state["ca_submitted"] = True
                    st.session_state["ca_pdf_data"] = {
                        "requested_by": requested_by, "department": department,
                        "request_date": request_date, "reason": reason, "date_needed": date_needed,
                        "expense_items": expense_items, "grand_total": grand_total,
                        "bank_name": bank_name, "account_no": account_no, "account_name": account_name,
                        "designated_approver": designated_approver, "custodian": custodian
                    }
                except Exception as e:
                    st.error(f"Database error: {e}")

    if st.session_state.get("ca_submitted", False) and "ca_pdf_data" in st.session_state:
        data = st.session_state["ca_pdf_data"]
        pdf_bytes = create_ca_pdf(
            ca_no=st.session_state["ca_no"],
            requested_by=data["requested_by"],
            department=data["department"],
            request_date=data["request_date"],
            reason=data["reason"],
            date_needed=data["date_needed"],
            expense_items=data["expense_items"],
            grand_total=data["grand_total"],
            bank_name=data["bank_name"],
            account_no=data["account_no"],
            account_name=data["account_name"],
            approver=data["designated_approver"],
            custodian=data["custodian"]
        )

        st.download_button(
            label="📥 Download Cash Advance Voucher PDF",
            data=pdf_bytes,
            file_name=f"{st.session_state['ca_no']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
import datetime
import os
import sqlite3
import streamlit as st
from fpdf import FPDF

# --- DATABASE SETUP ---
DB_FILE = "liquidation.db"

def init_liq_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS liq_headers (
            liq_no TEXT PRIMARY KEY,
            requester TEXT,
            transaction_type TEXT,
            submission_date TEXT,
            original_ref TEXT,
            funds_received REAL,
            total_verified REAL,
            unused_returned REAL,
            reimbursement_requested REAL,
            chk_signed_pdf INTEGER,
            chk_invoices INTEGER,
            chk_proof_payment INTEGER,
            chk_excel_pdf INTEGER,
            chk_unused_returned INTEGER,
            chk_non_cash INTEGER,
            requester_sig TEXT,
            approver_sig TEXT,
            custodian_sig TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS liq_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            liq_no TEXT,
            item_no INTEGER,
            expense_date TEXT,
            vendor TEXT,
            description TEXT,
            invoice_ref TEXT,
            amount REAL,
            remarks TEXT,
            FOREIGN KEY (liq_no) REFERENCES liq_headers(liq_no)
        )
    """)
    conn.commit()
    conn.close()

def generate_new_liq_no(tx_type):
    init_liq_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    current_year = datetime.date.today().strftime("%Y")
    
    # Prefix based on transaction type selection
    if "Reimbursement" in tx_type:
        prefix = f"REIM-{current_year}-"
    else:
        prefix = f"LIQ-{current_year}-"

    cursor.execute("SELECT liq_no FROM liq_headers WHERE liq_no LIKE ?", (f"{prefix}%",))
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
    return f"{prefix}{next_seq:04d}"


# --- PDF GENERATION FUNCTION ---
def create_liq_pdf(
    liq_no,
    requester,
    transaction_type,
    submission_date,
    original_ref,
    expense_items,
    funds_received,
    total_verified,
    unused_returned,
    reimbursement_requested,
    checklists,
    requester_sig,
    approver_sig,
    custodian_sig,
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
    pdf.set_fill_color(24, 105, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, "LIQUIDATION / REIMBURSEMENT FORM", 1, 1, "C", True)

    # --- METADATA BOXES ---
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(210, 230, 240)

    # Row 1
    pdf.cell(25, 5.5, "Requester", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(50, 5.5, str(requester), 1, 0, "L")
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(32, 5.5, "Transaction Type", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(43, 5.5, str(transaction_type), 1, 0, "L")
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(25, 5.5, "Submission Date", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(15, 5.5, str(submission_date), 1, 1, "L")

    # Row 2
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(35, 5.5, "Original PCV / CA Ref.", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(40, 5.5, str(original_ref), 1, 0, "L")
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(50, 5.5, "Liquidation / Reimbursement Ref. No.", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(65, 5.5, str(liq_no), 1, 1, "L")

    pdf.ln(3)

    # --- EXPENSE DETAILS TABLE HEADER ---
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(24, 105, 130)
    pdf.set_text_color(255, 255, 255)

    pdf.cell(22, 6, "Date", 1, 0, "C", True)
    pdf.cell(35, 6, "Vendor / Payee", 1, 0, "C", True)
    pdf.cell(53, 6, "Description / Business Purpose", 1, 0, "C", True)
    pdf.cell(30, 6, "Receipt / Invoice Ref.", 1, 0, "C", True)
    pdf.cell(25, 6, "Amount (P)", 1, 0, "C", True)
    pdf.cell(25, 6, "Remarks", 1, 1, "C", True)

    # --- EXPENSE ROWS (10 rows) ---
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)

    for i in range(1, 11):
        matching_item = next((item for item in expense_items if item["No"] == i), None)
        edate = str(matching_item["Expense Date"]) if matching_item and matching_item["Expense Date"] else ""
        vendor = str(matching_item["Vendor"]) if matching_item else ""
        desc = str(matching_item["Description"]) if matching_item else ""
        inv = str(matching_item["Invoice Ref"]) if matching_item else ""
        amt_val = matching_item["Amount"] if matching_item else 0.0
        remarks = str(matching_item["Remarks"]) if matching_item else ""

        amt_str = f"{amt_val:,.2f}" if amt_val > 0 else ""

        pdf.cell(22, 5, edate, 1, 0, "C")
        pdf.cell(35, 5, vendor, 1, 0, "L")
        pdf.cell(53, 5, desc, 1, 0, "L")
        pdf.cell(30, 5, inv, 1, 0, "L")
        pdf.cell(25, 5, amt_str, 1, 0, "R")
        pdf.cell(25, 5, remarks, 1, 1, "L")

    # --- TOTAL VERIFIED EXPENSES ---
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_fill_color(24, 105, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(165, 6, "Total Verified Expenses (P)", 1, 0, "R", True)
    pdf.cell(25, 6, f"P{total_verified:,.2f}", 1, 1, "R", True)

    pdf.ln(3)

    # --- SETTLEMENT SUMMARY ---
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_fill_color(24, 105, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 5.5, "SETTLEMENT SUMMARY", 1, 1, "C", True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "B", 8)

    pdf.cell(165, 5, "Funds Received (P)", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(25, 5, f"P{funds_received:,.2f}", 1, 1, "R")

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(165, 5, "Verified Expenses (P)", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(25, 5, f"P{total_verified:,.2f}", 1, 1, "R")

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(165, 5, "Unused Cash Returned (P)", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(25, 5, f"P{unused_returned:,.2f}", 1, 1, "R")

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(165, 5, "Reimbursement Amount Requested (P)", 1, 0, "L", True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(25, 5, f"P{reimbursement_requested:,.2f}", 1, 1, "R")

    pdf.ln(3)

    # --- DOCUMENT CHECKLIST ---
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_fill_color(24, 105, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 5.5, "DOCUMENT CHECKLIST", 1, 1, "C", True)

    chk_labels = [
        "Signed form PDF",
        "Invoices / receipts attached",
        "Proof of payment attached where applicable",
        "Supporting Excel schedules exported to PDF",
        "Unused cash returned, if applicable",
        "Remaining non-cash items listed, if applicable"
    ]

    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    for idx, label in enumerate(chk_labels):
        checked = checklists[idx]
        box_text = "[X]" if checked else "[   ]"
        pdf.cell(10, 5, box_text, 1, 0, "C")
        pdf.cell(180, 5, f" {label}", 1, 1, "L")

    pdf.ln(3)

    # --- APPROVAL / ACKNOWLEDGMENT ---
    pdf.set_fill_color(24, 105, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.cell(0, 5.5, "APPROVAL / ACKNOWLEDGMENT", 1, 1, "C", True)

    pdf.cell(63.3, 5.5, "Requester", 1, 0, "C", True)
    pdf.cell(63.3, 5.5, "Designated Approver", 1, 0, "C", True)
    pdf.cell(63.4, 5.5, "Custodian / Reviewer", 1, 1, "C", True)

    pdf.ln(10)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(63.3, 4, f"{requester_sig if requester_sig else ''}", 0, 0, "C")
    pdf.cell(63.3, 4, f"{approver_sig if approver_sig else ''}", 0, 0, "C")
    pdf.cell(63.4, 4, f"{custodian_sig if custodian_sig else ''}", 0, 1, "C")

    pdf.cell(63.3, 4, "___________________________", 0, 0, "C")
    pdf.cell(63.3, 4, "___________________________", 0, 0, "C")
    pdf.cell(63.4, 4, "___________________________", 0, 1, "C")

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(63.3, 4.5, "Name / Signature", 0, 0, "C")
    pdf.cell(63.3, 4.5, "Name / Signature", 0, 0, "C")
    pdf.cell(63.4, 4.5, "Name / Signature", 0, 1, "C")

    return bytes(pdf.output())


# --- STREAMLIT UI ROUTER FUNCTION ---
def run():
    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.subheader("📋 LIQUIDATION / REIMBURSEMENT FORM")
        st.markdown("*Handle liquidations and expense reimbursements efficiently.*")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Create New Form", use_container_width=True):
            st.session_state["liq_submitted"] = False
            if "liq_pdf_data" in st.session_state:
                del st.session_state["liq_pdf_data"]
            st.rerun()

    st.divider()

    with st.form("liquidation_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            requester = st.text_input("Requester")
        with col2:
            transaction_type = st.selectbox(
                "Transaction Type",
                ["PCV Liquidation", "Cash Advance Liquidation", "Reimbursement"]
            )
        with col3:
            submission_date = st.date_input("Submission Date", datetime.date.today())

        col_ref1, col_ref2 = st.columns(2)
        with col_ref1:
            original_ref = st.text_input("Original PCV / CA Reference (if applicable)")
        with col_ref2:
            current_liq_no = generate_new_liq_no(transaction_type)
            liq_no = st.text_input("Liquidation / Reimbursement Ref. No.", value=current_liq_no, disabled=True)

        st.markdown("### EXPENSE DETAILS")

        header_cols = st.columns([1.2, 2, 2.5, 1.8, 1.2, 1.5])
        header_cols[0].markdown("**Date**")
        header_cols[1].markdown("**Vendor / Payee**")
        header_cols[2].markdown("**Description**")
        header_cols[3].markdown("**Invoice Ref**")
        header_cols[4].markdown("**Amount (₱)**")
        header_cols[5].markdown("**Remarks**")

        expense_items = []
        total_verified = 0.0

        for i in range(1, 11):
            r_cols = st.columns([1.2, 2, 2.5, 1.8, 1.2, 1.5])

            with r_cols[0]:
                edate = st.date_input(f"Date_{i}", datetime.date.today(), label_visibility="collapsed")
            with r_cols[1]:
                vendor = st.text_input(f"Vendor_{i}", label_visibility="collapsed")
            with r_cols[2]:
                desc = st.text_input(f"Desc_{i}", label_visibility="collapsed")
            with r_cols[3]:
                inv = st.text_input(f"Inv_{i}", label_visibility="collapsed")
            with r_cols[4]:
                amt = st.number_input(f"Amt_{i}", min_value=0.0, value=0.0, step=10.0, format="%.2f", label_visibility="collapsed")
            with r_cols[5]:
                rem = st.text_input(f"Rem_{i}", label_visibility="collapsed")

            total_verified += amt

            expense_items.append({
                "No": i,
                "Expense Date": str(edate),
                "Vendor": vendor,
                "Description": desc,
                "Invoice Ref": inv,
                "Amount": amt,
                "Remarks": rem
            })

        st.divider()

        col_tot1, col_tot2 = st.columns([3, 1])
        with col_tot1:
            st.markdown("### Total Verified Expenses")
        with col_tot2:
            st.markdown(f"### ₱ {total_verified:,.2f}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### SETTLEMENT SUMMARY")
        
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            funds_received = st.number_input("Funds Received (₱)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
            
            calculated_unused = max(0.0, funds_received - total_verified)
            unused_returned = st.number_input("Unused Cash Returned (₱)", min_value=0.0, value=calculated_unused, step=100.0, format="%.2f")
            #unused_returned = st.number_input("Unused Cash Returned (₱)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
        with s_col2:
            reimbursement_requested = max(0.0, total_verified - funds_received)
            st.markdown(f"**Calculated Reimbursement Requested:** ₱ {reimbursement_requested:,.2f}")
            st.markdown(f"**Calculated Unused Return:** ₱ {calculated_unused:,.2f}")
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### DOCUMENT CHECKLIST")
        
        chk_signed_pdf = st.checkbox("Signed form PDF")
        chk_invoices = st.checkbox("Invoices / receipts attached")
        chk_proof_payment = st.checkbox("Proof of payment attached where applicable")
        chk_excel_pdf = st.checkbox("Supporting Excel schedules exported to PDF")
        chk_unused_returned = st.checkbox("Unused cash returned, if applicable")
        chk_non_cash = st.checkbox("Remaining non-cash items listed, if applicable")

        checklists = [
            chk_signed_pdf, chk_invoices, chk_proof_payment,
            chk_excel_pdf, chk_unused_returned, chk_non_cash
        ]

        st.markdown("<br>", unsafe_allow_html=True)
        sig_col1, sig_col2, sig_col3 = st.columns(3)
        with sig_col1:
            requester_sig = st.text_input("Requester (Name/Signature)")
        with sig_col2:
            approver_sig = st.selectbox(
                      "Designated Approver (Name/Signature)",
                      [
                          "Select Approver",
                          "Tyler Upper",
                          "Wale Saka",
                      ],
                  )
        with sig_col3:
            custodian_sig = st.selectbox(
                      "Custodian / Reviewer (Name/Signature)",
                      [
                          "Select Custodian",
                          "Dianna Kaye Casabuena",
                      ],
                  )

        submitted = st.form_submit_button("💾 Save & Generate Liquidation/Reimbursement PDF", use_container_width=True)

        if submitted:
            if not requester:
                st.error("Please fill out the 'Requester' field.")
            else:
                init_liq_db()
                try:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT OR REPLACE INTO liq_headers 
                        (liq_no, requester, transaction_type, submission_date, original_ref, funds_received, total_verified, unused_returned, reimbursement_requested, chk_signed_pdf, chk_invoices, chk_proof_payment, chk_excel_pdf, chk_unused_returned, chk_non_cash, requester_sig, approver_sig, custodian_sig)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        current_liq_no, requester, transaction_type, str(submission_date), original_ref,
                        funds_received, total_verified, unused_returned, reimbursement_requested,
                        int(chk_signed_pdf), int(chk_invoices), int(chk_proof_payment),
                        int(chk_excel_pdf), int(chk_unused_returned), int(chk_non_cash),
                        requester_sig, approver_sig, custodian_sig
                    ))

                    cursor.execute("DELETE FROM liq_items WHERE liq_no = ?", (current_liq_no,))

                    for item in expense_items:
                        if item["Description"].strip() or item["Amount"] > 0:
                            cursor.execute("""
                                INSERT INTO liq_items (liq_no, item_no, expense_date, vendor, description, invoice_ref, amount, remarks)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                current_liq_no, item["No"], item["Expense Date"], item["Vendor"],
                                item["Description"], item["Invoice Ref"], item["Amount"], item["Remarks"]
                            ))

                    conn.commit()
                    conn.close()
                    st.success(f"Form {current_liq_no} successfully saved and registered!")
                    st.session_state["liq_submitted"] = True
                    st.session_state["liq_pdf_data"] = {
                        "liq_no": current_liq_no, "requester": requester, "transaction_type": transaction_type,
                        "submission_date": submission_date, "original_ref": original_ref,
                        "expense_items": expense_items, "funds_received": funds_received,
                        "total_verified": total_verified, "unused_returned": unused_returned,
                        "reimbursement_requested": reimbursement_requested, "checklists": checklists,
                        "requester_sig": requester_sig, "approver_sig": approver_sig, "custodian_sig": custodian_sig
                    }
                except Exception as e:
                    st.error(f"Database error: {e}")

    if st.session_state.get("liq_submitted", False) and "liq_pdf_data" in st.session_state:
        data = st.session_state["liq_pdf_data"]
        pdf_bytes = create_liq_pdf(
            liq_no=data["liq_no"],
            requester=data["requester"],
            transaction_type=data["transaction_type"],
            submission_date=data["submission_date"],
            original_ref=data["original_ref"],
            expense_items=data["expense_items"],
            funds_received=data["funds_received"],
            total_verified=data["total_verified"],
            unused_returned=data["unused_returned"],
            reimbursement_requested=data["reimbursement_requested"],
            checklists=data["checklists"],
            requester_sig=data["requester_sig"],
            approver_sig=data["approver_sig"],
            custodian_sig=data["custodian_sig"]
        )

        st.download_button(
            label="📥 Download Liquidation / Reimbursement Form PDF",
            data=pdf_bytes,
            file_name=f"{data['liq_no']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

if __name__ == "__main__":
    st.set_page_config(page_title="Liquidation & Reimbursement", page_icon="📋", layout="wide")
    run()
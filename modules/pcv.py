import datetime
import os
import sqlite3
import streamlit as st
from fpdf import FPDF

# --- DATABASE SETUP ---
DB_FILE = "petty_cash.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pcv_headers (
            pcv_no TEXT PRIMARY KEY,
            requested_by TEXT,
            department TEXT,
            request_date TEXT,
            designated_approver TEXT,
            custodian TEXT,
            total_funding REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pcv_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pcv_no TEXT,
            item_no INTEGER,
            description TEXT,
            quantity INTEGER,
            unit_cost REAL,
            total_cost REAL,
            FOREIGN KEY (pcv_no) REFERENCES pcv_headers(pcv_no)
        )
    """)
  conn.commit()
  conn.close()


def generate_new_pcv_no():
  init_db()
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()

  current_year = datetime.date.today().strftime("%Y")
  prefix = f"PCV-{current_year}-"

  cursor.execute(
      "SELECT pcv_no FROM pcv_headers WHERE pcv_no LIKE ?", (f"{prefix}%",)
  )
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
def create_pdf(
    pcv_no,
    requested_by,
    department,
    request_date,
    expense_items,
    grand_total,
    approver,
    custodian,
):
  pdf = FPDF(orientation="P", unit="mm", format="A4")
  pdf.add_page()
  pdf.set_auto_page_break(auto=True, margin=15)

# --- LOGO / HEADER SECTION ---
    # If you have a logo image file named 'ABS_logo.png', uncomment the line below:
  if os.path.exists("assets/ABS_logo.png"):
      pdf.image("assets/ABS_logo.png", x=80, y=10, w=50)
      pdf.ln(20)
  else:
      pdf.ln(5)

  # Fallback text header if logo image isn't loaded yet
  #pdf.set_font("helvetica", "B", 18)
  #pdf.set_text_color(24, 105, 130)  # Primary teal brand color
  #pdf.cell(0, 8, "access", ln=True, align="C")
  #pdf.set_font("helvetica", "", 9)
  #pdf.set_text_color(100, 100, 100)
  #pdf.cell(0, 4, "Brokerage Support Inc.", ln=True, align="C")
  #pdf.ln(8)

  # Reset text color to black
  pdf.set_text_color(0, 0, 0)

  # --- TITLE BANNER ---
  pdf.set_fill_color(24, 105, 130)  # Teal Header Bar
  pdf.set_text_color(255, 255, 255)
  pdf.set_font("helvetica", "B", 11)
  pdf.cell(0, 8, "PETTY CASH VOUCHER", 1, 1, "C", True)

  pdf.set_font("helvetica", "BI", 8)
  pdf.set_text_color(0, 0, 0)
  pdf.cell(
      0,
      5,
      "Use for PCF transactions up to P2,000 per transaction.",
      1,
      1,
      "L",
      False,
  )

  # --- METADATA BOXES ---
  pdf.set_font("helvetica", "B", 9)
  pdf.set_fill_color(210, 230, 240)  # Light blue accent fill

  pdf.cell(45, 7, "Requested by", 1, 0, "L", True)
  pdf.set_font("helvetica", "", 9)
  pdf.cell(50, 7, str(requested_by), 1, 0, "L")

  pdf.set_font("helvetica", "B", 9)
  pdf.cell(45, 7, "PCV No.", 1, 0, "L", True)
  pdf.set_font("helvetica", "", 9)
  pdf.cell(50, 7, str(pcv_no), 1, 1, "L")

  pdf.set_font("helvetica", "B", 9)
  pdf.cell(45, 7, "Department/Team", 1, 0, "L", True)
  pdf.set_font("helvetica", "", 9)
  pdf.cell(50, 7, str(department), 1, 0, "L")

  pdf.set_font("helvetica", "B", 9)
  pdf.cell(45, 7, "Request Date", 1, 0, "L", True)
  pdf.set_font("helvetica", "", 9)
  pdf.cell(50, 7, str(request_date), 1, 1, "L")

  pdf.ln(6)

  # --- EXPENSE DETAILS TABLE HEADER ---
  pdf.set_font("helvetica", "B", 9)
  pdf.set_fill_color(24, 105, 130)
  pdf.set_text_color(255, 255, 255)

  pdf.cell(10, 7, "#", 1, 0, "C", True)
  pdf.cell(85, 7, "Description / Business Purpose", 1, 0, "C", True)
  pdf.cell(30, 7, "Quantity", 1, 0, "C", True)
  pdf.cell(35, 7, "Unit Cost", 1, 0, "C", True)
  pdf.cell(30, 7, "Total Cost", 1, 1, "C", True)

  # --- EXPENSE ROWS (Padded to 10 rows to match layout) ---
  pdf.set_font("helvetica", "", 8)
  pdf.set_text_color(0, 0, 0)

  for i in range(1, 11):
    # Find matching item if it exists in expense_items
    matching_item = next((item for item in expense_items if item["No"] == i), None)

    desc = str(matching_item["Description"]) if matching_item else ""
    qty = str(matching_item["Quantity"]) if matching_item and matching_item["Quantity"] > 0 else ""
    unit_cost_val = matching_item["Unit Cost"] if matching_item else 0.0
    total_cost_val = matching_item["Total Cost"] if matching_item else 0.0

    unit_cost_str = f"{unit_cost_val:,.2f}" if unit_cost_val > 0 else ""
    total_cost_str = f"{total_cost_val:,.2f}" if total_cost_val > 0 else "-"

    pdf.cell(10, 6, str(i), 1, 0, "C")
    pdf.cell(85, 6, desc, 1, 0, "L")
    pdf.cell(30, 6, qty, 1, 0, "C")
    pdf.cell(35, 6, unit_cost_str, 1, 0, "R")
    pdf.cell(30, 6, total_cost_str, 1, 1, "R")

  # --- TOTAL ROW ---
  pdf.set_font("helvetica", "B", 9)
  pdf.set_fill_color(24, 105, 130)
  pdf.set_text_color(255, 255, 255)
  pdf.cell(160, 7, "TOTAL FUNDING REQUESTED", 1, 0, "R", True)
  pdf.cell(30, 7, f"P{grand_total:,.2f}", 1, 1, "R", True)

  pdf.ln(10)

  # --- SIGNATURES SECTION ---
  pdf.set_text_color(0, 0, 0)
  pdf.set_fill_color(24, 105, 130)
  pdf.set_font("helvetica", "B", 9)
  pdf.cell(0, 6, "", 0, 1)  # spacing
  
  # Approver / Custodian Header Bar
  pdf.set_fill_color(24, 105, 130)
  pdf.set_text_color(255, 255, 255)
  pdf.cell(95, 6, "Designated Approver", 1, 0, "C", True)
  pdf.cell(5, 6, "", 0, 0)  # Gap
  pdf.cell(90, 6, "Custodian", 1, 1, "C", True)

  pdf.ln(15)

  # Signature Lines
  pdf.set_text_color(0, 0, 0)
  pdf.set_font("helvetica", "", 9)
  pdf.cell(95, 4, f"{approver if approver else ''}", 0, 0, "C")
  pdf.cell(5, 4, "", 0, 0)
  pdf.cell(90, 4, f"{custodian if custodian else ''}", 0, 1, "C")

  pdf.cell(95, 4, "___________________________________", 0, 0, "C")
  pdf.cell(5, 4, "", 0, 0)
  pdf.cell(90, 4, "___________________________________", 0, 1, "C")

  pdf.set_font("helvetica", "B", 8)
  pdf.cell(95, 5, "Name/Signature", 0, 0, "C")
  pdf.cell(5, 5, "", 0, 0)
  pdf.cell(90, 5, "Name/Signature", 0, 1, "C")

  return bytes(pdf.output())


# --- MAIN RUN FUNCTION FOR MULTI-PAGE ROUTER ---
def run():
  if "pcv_no" not in st.session_state:
    st.session_state["pcv_no"] = generate_new_pcv_no()

  # Top Action Bar
  col_title, col_btn = st.columns([3, 1])
  with col_title:
    st.subheader("💸 PETTY CASH VOUCHER")
    st.markdown("*Use for PCF transactions up to ₱2,000 per transaction.*")
  with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Create New PCV", use_container_width=True):
      st.session_state["pcv_no"] = generate_new_pcv_no()
      st.session_state["form_submitted"] = False
      if "pdf_data" in st.session_state:
        del st.session_state["pdf_data"]
      st.rerun()

  st.divider()

  # Form Container
  with st.form("petty_cash_form"):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
      requested_by = st.text_input("Requested by")

    with col2:
      pcv_no = st.text_input(
          "PCV No.", value=st.session_state["pcv_no"], disabled=True
      )

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

    st.markdown("### EXPENSE DETAILS")

    header_cols = st.columns([0.5, 3.5, 1, 1.5, 1.5])
    header_cols[0].markdown("**#**")
    header_cols[1].markdown("**Description / Business Purpose**")
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
        desc = st.text_input(f"Desc_{i}", label_visibility="collapsed")
      with r_cols[2]:
        qty = st.number_input(
            f"Qty_{i}",
            min_value=0,
            value=0,
            step=1,
            label_visibility="collapsed",
        )
      with r_cols[3]:
        unit_cost = st.number_input(
            f"Unit_{i}",
            min_value=0.0,
            value=0.0,
            step=10.0,
            format="%.2f",
            label_visibility="collapsed",
        )

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
      st.markdown("### TOTAL FUNDING REQUESTED")
    with col_tot2:
      st.markdown(f"### ₱ {grand_total:,.2f}")

    if grand_total > 2000.00:
      st.warning(
          "⚠️ Warning: Total funding requested exceeds the ₱2,000.00 limit per"
          " petty cash transaction!"
      )

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
      
    submitted = st.form_submit_button(
        "💾 Save & Generate Voucher PDF", use_container_width=True
    )

    if submitted:
      if department == "Select Department":
        st.error("Please select a valid Department/Team.")
      elif not requested_by:
        st.error("Please fill out the 'Requested by' field.")
      elif grand_total > 2000.00:
        # BLOCK PERMISSION: Prevent save & block PDF generation
        st.error(
            "❌ Access Denied: Total funding requested (₱"
            f"{grand_total:,.2f}) exceeds the maximum limit of ₱2,000.00. PDF"
            " generation and saving are disabled."
        )
        st.session_state["form_submitted"] = False
        if "pdf_data" in st.session_state:
          del st.session_state["pdf_data"]
      else:
        init_db()
        try:
          conn = sqlite3.connect(DB_FILE)
          cursor = conn.cursor()

          cursor.execute(
              """
                            INSERT OR REPLACE INTO pcv_headers 
                            (pcv_no, requested_by, department, request_date, designated_approver, custodian, total_funding)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
              (
                  st.session_state["pcv_no"],
                  requested_by,
                  department,
                  str(request_date),
                  designated_approver,
                  custodian,
                  grand_total,
              ),
          )

          cursor.execute(
              "DELETE FROM pcv_items WHERE pcv_no = ?",
              (st.session_state["pcv_no"],),
          )

          for item in expense_items:
            if item["Description"].strip() or item["Total Cost"] > 0:
              cursor.execute(
                  """
                                    INSERT INTO pcv_items (pcv_no, item_no, description, quantity, unit_cost, total_cost)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """,
                  (
                      st.session_state["pcv_no"],
                      item["No"],
                      item["Description"],
                      item["Quantity"],
                      item["Unit Cost"],
                      item["Total Cost"],
                  ),
              )

          conn.commit()
          conn.close()
          st.success(
              f"Voucher {st.session_state['pcv_no']} successfully saved to"
              " database!"
          )
          st.session_state["form_submitted"] = True
          st.session_state["pdf_data"] = {
              "requested_by": requested_by,
              "department": department,
              "request_date": request_date,
              "expense_items": expense_items,
              "grand_total": grand_total,
              "designated_approver": designated_approver,
              "custodian": custodian,
          }
        except Exception as e:
          st.error(f"Database error: {e}")

  # --- PDF DOWNLOAD BUTTON (Rendered ONLY if valid and submitted) ---
  if (
      st.session_state.get("form_submitted", False)
      and "pdf_data" in st.session_state
  ):
    data = st.session_state["pdf_data"]
    if data["grand_total"] <= 2000.00:
      pdf_bytes = create_pdf(
          pcv_no=st.session_state["pcv_no"],
          requested_by=data["requested_by"],
          department=data["department"],
          request_date=data["request_date"],
          expense_items=data["expense_items"],
          grand_total=data["grand_total"],
          approver=data["designated_approver"],
          custodian=data["custodian"],
      )

      st.download_button(
          label="📥 Download Petty Cash Voucher PDF",
          data=pdf_bytes,
          file_name=f"{st.session_state['pcv_no']}.pdf",
          mime="application/pdf",
          use_container_width=True,
      )
      
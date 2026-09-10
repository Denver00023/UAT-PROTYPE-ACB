import streamlit as st
import pandas as pd



# LOAD AND CLEAN FILE

def load_clean_file(file):

    if file.name.lower().endswith(".csv"):

        df = pd.read_csv(file)

    else:

        # IMPORTANT:
        # Do not skip row 2.
        # Every row in the Excel file will be read.
        df = pd.read_excel(
            file,
            header=0
        )

    # Clean column names
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # Clean important columns
    for col in [
        "Reliable_tracking",
        "Reference",
        "Reference 2"
    ]:

        if col in df.columns:

            df[col] = (
                df[col]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

    return df


# MAIN APP

def run():

    st.subheader("✈️ APC Billing Validation - Cargo Control Number & Reliable Tracking")

    st.info("This tool validates Cargo Control Number and Reliable Tracking " "between the Scrubbing File, Original SFTP File, and Client File.")

    # FILE UPLOAD
    
    col1, col2, col3 = st.columns(3)

    with col1:

        scrub_file = st.file_uploader(
            "📄 **Upload Scrubbing File**",
            type=["xlsx", "xls", "csv"],
            key="scrub_file"
        )

    with col2:

        sftp_file = st.file_uploader(
            "📄 **Upload Original SFTP File**",
            type=["xlsx", "xls", "csv"],
            key="sftp_file"
        )

    with col3:

        client_file = st.file_uploader(
            "📄 **Upload Client File**",
            type=["xlsx", "xls", "csv"],
            key="client_file"
        )

    # WAIT FOR FILES
    
    if not scrub_file or not sftp_file or not client_file:

        st.info(
            "Please upload the Scrubbing File, Original SFTP File, "
            "and Client File to start validation."
        )

        return

    # READ FILES
    
    try:

        scrub_df = load_clean_file(scrub_file)
        sftp_df = load_clean_file(sftp_file)
        client_df = load_clean_file(client_file)

    except Exception as e:

        st.error(
            f"Error reading Excel file: {e}"
        )

        return

    # CLIENT FILE
    
    # The first column of the Client File is used as
    # Reliable_tracking.
    #
    # APC and REL records are ignored.
    #
    # Example:
    #
    # APC7316       -> IGNORED
    # APC0003       -> IGNORED
    # REL062        -> IGNORED
    # REL137        -> IGNORED
    # P0002201703   -> KEPT
    #
    # IMPORTANT:
    # We use startswith() instead of "APC" not in x.
    # This prevents accidental removal of other values.
    
    if len(client_df.columns) == 0:

        st.error(
            "Client File has no columns."
        )

        return

    client_source_column = client_df.columns[0]

    client_df["Reliable_tracking"] = (
        client_df[client_source_column]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # IGNORE CLIENT VALUES STARTING WITH APC OR REL
    
    client_df = client_df[
        ~client_df["Reliable_tracking"].str.startswith(
            ("APC", "REL"),
            na=False
        )
    ].copy()

    # REQUIRED COLUMNS
    
    required_scrub_columns = [
        "Reference",
        "Reference 2"
    ]

    required_sftp_columns = [
        "Reference"
    ]

    required_client_columns = [
        "Reliable_tracking"
    ]

    # CHECK SCRUBBING FILE
    
    missing_scrub = [
        col
        for col in required_scrub_columns
        if col not in scrub_df.columns
    ]

    # CHECK ORIGINAL SFTP FILE
    
    missing_sftp = [
        col
        for col in required_sftp_columns
        if col not in sftp_df.columns
    ]

    # CHECK CLIENT FILE
    
    missing_client = [
        col
        for col in required_client_columns
        if col not in client_df.columns
    ]

    # DISPLAY ERRORS
    
    if missing_scrub:

        st.error(
            f"Scrubbing File missing column(s): "
            f"{', '.join(missing_scrub)}"
        )

        return

    if missing_sftp:

        st.error(
            f"Original SFTP File missing column(s): "
            f"{', '.join(missing_sftp)}"
        )

        return

    if missing_client:

        st.error(
            f"Client File missing column(s): "
            f"{', '.join(missing_client)}"
        )

        return

    # CLEAN MATCHING COLUMNS
    
    scrub_df["Reference"] = (
        scrub_df["Reference"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    scrub_df["Reference 2"] = (
        scrub_df["Reference 2"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    sftp_df["Reference"] = (
        sftp_df["Reference"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    client_df["Reliable_tracking"] = (
        client_df["Reliable_tracking"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    
    # GROUP SCRUBBING FILE
    # Reference   = Cargo Control Number
    # Reference 2 = Reliable Tracking

    scrub_group = (
        scrub_df[
            (scrub_df["Reference"] != "")
            |
            (scrub_df["Reference 2"] != "")
        ]
        .groupby(
            [
                "Reference",
                "Reference 2"
            ],
            dropna=False
        )
        .size()
        .reset_index(
            name="Scrubbing Count"
        )
    )

    # GROUP ORIGINAL SFTP FILE
    # Reference = Cargo Control Number

    sftp_group = (
        sftp_df[
            sftp_df["Reference"] != ""
        ]
        .groupby(
            "Reference"
        )
        .size()
        .reset_index(
            name="Original SFTP Count"
        )
    )

    # GROUP CLIENT FILE
    # Reliable_tracking = Reliable Tracking APC / REL records have already been removed.
    
    client_group = (
        client_df[
            client_df["Reliable_tracking"] != ""
        ]
        .groupby(
            "Reliable_tracking"
        )
        .size()
        .reset_index(
            name="Client Count"
        )
    )

    
    # RENAME ORIGINAL SFTP
    
    cargo_sftp = (
        sftp_group
        .rename(
            columns={
                "Reference": "Cargo Control Number"
            }
        )
    )
    
    # RENAME CLIENT
    
    client_tracking = (
        client_group
        .rename(
            columns={
                "Reliable_tracking": "Reliable Tracking"
            }
        )
    )

    
    # CREATE FINAL COMPARISON
    
    final_compare = (
        scrub_group
        .rename(
            columns={
                "Reference": "Cargo Control Number",
                "Reference 2": "Reliable Tracking"
            }
        )
        .merge(
            cargo_sftp,
            on="Cargo Control Number",
            how="outer"
        )
        .merge(
            client_tracking,
            on="Reliable Tracking",
            how="outer"
        )
    )

    
    # FILL MISSING COUNTS
    
    final_compare["Scrubbing Count"] = (
        final_compare["Scrubbing Count"]
        .fillna(0)
        .astype(int)
    )

    final_compare["Original SFTP Count"] = (
        final_compare["Original SFTP Count"]
        .fillna(0)
        .astype(int)
    )

    final_compare["Client Count"] = (
        final_compare["Client Count"]
        .fillna(0)
        .astype(int)
    )

    
    # CLEAN FINAL KEYS
    
    final_compare["Cargo Control Number"] = (
        final_compare["Cargo Control Number"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    final_compare["Reliable Tracking"] = (
        final_compare["Reliable Tracking"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    
    # STATUS
    
    def get_status(row):

        cargo = row["Cargo Control Number"]
        tracking = row["Reliable Tracking"]

        scrub_count = row["Scrubbing Count"]
        sftp_count = row["Original SFTP Count"]
        client_count = row["Client Count"]

        
        # Missing Cargo Control Number
        
        if cargo == "":
            return (
                "❌ MISSING CARGO CONTROL NUMBER"
            )

        # Cargo Control Number not in Original SFTP
        
        if sftp_count == 0:
            return (
                "❌ CARGO CONTROL NUMBER NOT IN ORIGINAL SFTP"
            )

        # Scrubbing vs Original SFTP mismatch
        
        if scrub_count != sftp_count:
            return (
                "⚠️ CARGO CONTROL NUMBER COUNT MISMATCH"
            )

        # Missing Reliable Tracking
        
        if tracking == "":
            return (
                "⚠️ MISSING RELIABLE TRACKING"
            )

        # Reliable Tracking not in Client
        
        if client_count == 0:
            return (
                "❌ RELIABLE TRACKING NOT IN CLIENT"
            )

        # Scrubbing vs Client mismatch
        
        if scrub_count != client_count:
            return (
                "⚠️ RELIABLE TRACKING COUNT MISMATCH"
            )

        
        # Perfect Match
        
        return "✅ PERFECT MATCH CLEAR"

    final_compare["Status"] = (
        final_compare.apply(
            get_status,
            axis=1
        )
    )

    # FINAL COLUMN ORDER
    
    final_compare = final_compare[
        [
            "Cargo Control Number",
            "Reliable Tracking",
            "Scrubbing Count",
            "Original SFTP Count",
            "Client Count",
            "Status"
        ]
    ]

    # SORT RESULTS
    
    final_compare = (
        final_compare
        .sort_values(
            by="Status"
        )
        .reset_index(drop=True)
    )

    # VALIDATION METRICS
    
    st.subheader(
        "📊 Validation Metrics"
    )

    total = len(final_compare)

    perfect = len(
        final_compare[
            final_compare["Status"]
            == "✅ PERFECT MATCH CLEAR"
        ]
    )

    missing_extra = len(
        final_compare[
            final_compare["Status"].str.contains(
                "NOT IN|MISSING",
                na=False
            )
        ]
    )

    count_mismatch = len(
        final_compare[
            final_compare["Status"].str.contains(
                "COUNT MISMATCH",
                na=False
            )
        ]
    )

    issues = len(
        final_compare[
            final_compare["Status"]
            != "✅ PERFECT MATCH CLEAR"
        ]
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Total Records",
        total
    )

    col2.metric(
        "Perfect Match",
        perfect
    )

    col3.metric(
        "Missing / Extra",
        missing_extra
    )

    col4.metric(
        "Count Mismatch",
        count_mismatch
    )

    col5.metric(
        "Total Issues",
        issues
    )

    # GLOBAL ALERT
    
    if issues > 0:

        st.error(
            f"🚨 {issues} validation issue(s) found."
        )

    else:

        st.success(
            "No validation issues found. "
            "Cargo Control Number, Reliable Tracking, "
            "and row counts are clear. ✅"
        )

    # FINAL VALIDATION
    
    st.subheader(
        "📋 Final Validation"
    )

    st.dataframe(
        final_compare,
        use_container_width=True,
        hide_index=True
    )

    # VALIDATION ALERTS

    final_issues = final_compare[
        final_compare["Status"]
        != "✅ PERFECT MATCH CLEAR"
    ].copy()

    st.subheader(
        "🚨 Validation Alerts"
    )

    if len(final_issues) > 0:

        st.error(
            f"{len(final_issues)} validation issue(s) found."
        )

        st.dataframe(
            final_issues,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "No validation issues found. "
            "Cargo Control Number, Reliable Tracking, "
            "and row counts are clear. ✅"
        )

    # FOOTER
    st.caption(
        "© 2026 ACB Toolkit | Developed by IT Department"
    )

# START APPLICATION
if __name__ == "__main__":
    run()

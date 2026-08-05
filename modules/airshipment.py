import streamlit as st
import pandas as pd

def load_clean_file(file):

        # Row 1 = header, Row 2 = skip validation rules
        df = pd.read_excel(file, header=0, skiprows=[1])

        # clean column names
        df.columns = df.columns.str.strip()

        # remove empty tracking
        if "Reliable_tracking" in df.columns:
            df = df.dropna(subset=["Reliable_tracking"])
            df["Reliable_tracking"] = (
                df["Reliable_tracking"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

        return df

def run():

    st.subheader("✈️ AIR SHIPMENT VALIDATION GETS UPLOAD")

    col1, col2 = st.columns(2)

    with col1:
        scrub_file = st.file_uploader("📄 Upload Scrubbing File", type=["xlsx"])
    with col2:
        sftp_file = st.file_uploader("📄 Upload Original SFTP File", type=["xlsx"])

    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")
    
    if scrub_file and sftp_file:

        scrub_df = load_clean_file(scrub_file)
        sftp_df = load_clean_file(sftp_file)

        scrub_df.columns = scrub_df.columns.str.strip()
        sftp_df.columns = sftp_df.columns.str.strip()

        if "Reliable_tracking" not in scrub_df.columns or "Reliable_tracking" not in sftp_df.columns:
            st.error("Reliable_tracking column missing")
            return

        # GROUPING

        scrub_group = scrub_df.groupby("Reliable_tracking").size().reset_index(name="scrub_count")
        sftp_group = sftp_df.groupby("Reliable_tracking").size().reset_index(name="sftp_count")

        compare = scrub_group.merge(
            sftp_group,
            on="Reliable_tracking",
            how="outer"
        )

        compare["scrub_count"] = compare["scrub_count"].fillna(0)
        compare["sftp_count"] = compare["sftp_count"].fillna(0)

        # STATUS LOGIC

        def status(row):
            if row["scrub_count"] == 0:
                return "❌ EXTRA IN SFTP POSSIBLE IS (cLVS)"
            if row["sftp_count"] == 0:
                return "⚠️ MISSING IN SFTP"
            if row["scrub_count"] != row["sftp_count"]:
                return "⚠️ COUNT MISMATCH"
            return "✅ PERFECT MATCH CLEAR"

        compare["status"] = compare.apply(status, axis=1)


        # METRICS
        st.subheader("📊 Summary Metrics")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("**Scrubbing Items**", len(scrub_group))
        col2.metric("**SFTP Items**", len(sftp_group))

        missing = len(compare[compare["status"] == "⚠️ MISSING IN SFTP"])
        extra = len(compare[compare["status"] == "❌ EXTRA IN SFTP POSSIBLE IS (cLVS)"])
        mismatch = len(compare[compare["status"] == "⚠️ COUNT MISMATCH"])

        col3.metric("**Missing**", missing)
        col4.metric("**Extra**", extra)
        col5.metric("**Mismatch**", mismatch)

        # FULL TABLE

        st.subheader("📋 Full Tracking Comparison")

        compare = compare.rename(columns={
            "scrub_count": "Scrubbing Count",
            "sftp_count": "Original sFTP Count",
            "status": "Status"

        })

        st.dataframe(
            compare.sort_values(by="Status"),
            use_container_width=True
        )

        # ISSUES ONLY
        st.subheader("❌ Issues Only")

        issues = compare[compare["Status"] != "✅ PERFECT MATCH CLEAR"]

        if len(issues) > 0:
            st.dataframe(issues, use_container_width=True)
        else:
            st.success("No issues found — full match ✅")


if __name__ == "__main__":
    run()
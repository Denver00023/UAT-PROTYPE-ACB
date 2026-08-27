import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime


# CONFIG

st.set_page_config(
    page_title="Attendance Payroll Dashboard",
    page_icon="📊",
    layout="wide"
)


# HELPERS

def parse_duration(value):

    if pd.isna(value):
        return 0

    value = str(value).strip()

    if value in ("", "-", "nan", "None"):
        return 0

    hours = 0
    minutes = 0

    hour_match = re.search(
        r"(\d+)\s*h",
        value,
        re.IGNORECASE
    )

    minute_match = re.search(
        r"(\d+)\s*m",
        value,
        re.IGNORECASE
    )

    if hour_match:
        hours = int(hour_match.group(1))

    if minute_match:
        minutes = int(minute_match.group(1))

    return hours * 60 + minutes


def minutes_to_duration(minutes):

    if pd.isna(minutes):
        return "0h 00m"

    minutes = int(round(minutes))

    sign = "-" if minutes < 0 else ""

    minutes = abs(minutes)

    hours = minutes // 60
    mins = minutes % 60

    return f"{sign}{hours}h {mins:02d}m"


def status_count(series, status):

    return int(
        series.astype(str)
        .str.strip()
        .eq(status)
        .sum()
    )


def clean_time(value):

    if pd.isna(value):
        return None

    if isinstance(value, datetime):
        return value

    if hasattr(value, "hour") and hasattr(value, "minute"):

        return datetime(
            1900,
            1,
            1,
            value.hour,
            value.minute,
            getattr(value, "second", 0)
        )

    value = str(value).strip()

    if value in ("", "-", "nan", "None"):
        return None

    parsed = pd.to_datetime(
        value,
        errors="coerce"
    )

    if pd.isna(parsed):
        return None

    return parsed.to_pydatetime()


def time_to_minutes(value):

    parsed = clean_time(value)

    if parsed is None:
        return None

    return (
        parsed.hour * 60
        + parsed.minute
        + parsed.second / 60
    )


def format_time(value):

    parsed = clean_time(value)

    if parsed is None:
        return "-"

    return parsed.strftime("%I:%M %p").lstrip("0")


def is_overnight_shift(
    shift_start,
    shift_end
):

    start = time_to_minutes(shift_start)
    end = time_to_minutes(shift_end)

    if start is None or end is None:
        return False

    return end < start


def calculate_scheduled_minutes(
    shift_start,
    shift_end
):

    start = time_to_minutes(shift_start)
    end = time_to_minutes(shift_end)

    if start is None or end is None:
        return 0

    if end < start:
        end += 1440

    return max(
        0,
        int(round(end - start))
    )


def calculate_actual_minutes(
    shift_start,
    shift_end,
    clock_in,
    clock_out
):

    shift_start_minutes = time_to_minutes(
        shift_start
    )

    shift_end_minutes = time_to_minutes(
        shift_end
    )

    clock_in_minutes = time_to_minutes(
        clock_in
    )

    clock_out_minutes = time_to_minutes(
        clock_out
    )

    if (
        shift_start_minutes is None
        or shift_end_minutes is None
        or clock_in_minutes is None
        or clock_out_minutes is None
    ):
        return 0

    overnight = (
        shift_end_minutes
        < shift_start_minutes
    )

    actual_start = clock_in_minutes
    actual_end = clock_out_minutes

    if overnight:

        if actual_start < shift_start_minutes:
            actual_start += 1440

        if actual_end < shift_start_minutes:
            actual_end += 1440

    else:

        if actual_end < actual_start:
            return 0

    return max(
        0,
        int(round(actual_end - actual_start))
    )


def calculate_tardiness(
    shift_start,
    shift_end,
    clock_in
):

    shift_start_minutes = time_to_minutes(
        shift_start
    )

    shift_end_minutes = time_to_minutes(
        shift_end
    )

    clock_in_minutes = time_to_minutes(
        clock_in
    )

    if (
        shift_start_minutes is None
        or shift_end_minutes is None
        or clock_in_minutes is None
    ):
        return 0

    overnight = (
        shift_end_minutes
        < shift_start_minutes
    )

    actual_clock_in = clock_in_minutes

    if overnight and actual_clock_in < shift_start_minutes:
        actual_clock_in += 1440

    difference = (
        actual_clock_in
        - shift_start_minutes
    )

    scheduled_duration = calculate_scheduled_minutes(
        shift_start,
        shift_end
    )

    if difference < 0:
        difference += 1440

    if difference > scheduled_duration:
        return 0

    return max(
        0,
        int(round(difference))
    )


def calculate_early_departure(
    shift_start,
    shift_end,
    clock_out
):

    shift_start_minutes = time_to_minutes(
        shift_start
    )

    shift_end_minutes = time_to_minutes(
        shift_end
    )

    clock_out_minutes = time_to_minutes(
        clock_out
    )

    if (
        shift_start_minutes is None
        or shift_end_minutes is None
        or clock_out_minutes is None
    ):
        return 0

    overnight = (
        shift_end_minutes
        < shift_start_minutes
    )

    actual_clock_out = clock_out_minutes

    if overnight and actual_clock_out < shift_start_minutes:
        actual_clock_out += 1440

    expected_end = shift_end_minutes

    if overnight:
        expected_end += 1440

    difference = (
        expected_end
        - actual_clock_out
    )

    if difference <= 0:
        return 0

    return int(round(difference))


def calculate_overtime(
    shift_start,
    shift_end,
    clock_out
):

    shift_start_minutes = time_to_minutes(
        shift_start
    )

    shift_end_minutes = time_to_minutes(
        shift_end
    )

    clock_out_minutes = time_to_minutes(
        clock_out
    )

    if (
        shift_start_minutes is None
        or shift_end_minutes is None
        or clock_out_minutes is None
    ):
        return 0

    overnight = (
        shift_end_minutes
        < shift_start_minutes
    )

    actual_clock_out = clock_out_minutes

    if overnight and actual_clock_out < shift_start_minutes:
        actual_clock_out += 1440

    expected_end = shift_end_minutes

    if overnight:
        expected_end += 1440

    overtime = (
        actual_clock_out
        - expected_end
    )

    return max(
        0,
        int(round(overtime))
    )


def get_coverage(group):

    valid_dates = group["Date"].dropna()

    if valid_dates.empty:
        return "-"

    start = valid_dates.min()
    end = valid_dates.max()

    if start.year == end.year:

        if start.month == end.month:

            return (
                f"{start.strftime('%b')} "
                f"{start.day}–"
                f"{end.day}, "
                f"{end.year}"
            )

        return (
            f"{start.strftime('%b')} "
            f"{start.day}–"
            f"{end.strftime('%b')} "
            f"{end.day}, "
            f"{end.year}"
        )

    return (
        f"{start.strftime('%b')} "
        f"{start.day}, "
        f"{start.year}–"
        f"{end.strftime('%b')} "
        f"{end.day}, "
        f"{end.year}"
    )


def make_excel(
    dashboard_df,
    summary_df,
    monthly_employee_df,
    verification_df,
    detail_df
):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        dashboard_df.to_excel(
            writer,
            sheet_name="Dashboard",
            index=False
        )

        summary_df.to_excel(
            writer,
            sheet_name="Employee Summary",
            index=False
        )

        monthly_employee_df.to_excel(
            writer,
            sheet_name="Employee Monthly",
            index=False
        )

        verification_df.to_excel(
            writer,
            sheet_name="DTR Verification",
            index=False
        )

        detail_df.to_excel(
            writer,
            sheet_name="Detail",
            index=False
        )

    output.seek(0)

    return output


# MAIN APP

def run():

    st.title(
        "📊 Attendance Payroll Dashboard"
    )

    st.write(
        "DTR verification for duty hours, "
        "tardiness, early departure, overtime, "
        "breaks, lunch, and recorded totals."
    )


    # UPLOAD

    uploaded_file = st.file_uploader(
        "Upload Excel DTR",
        type=["xlsx", "xls"]
    )

    if uploaded_file is None:

        st.info(
            "Please upload your attendance Excel file."
        )

        return


    # READ

    try:

        df = pd.read_excel(
            uploaded_file
        )

    except Exception as e:

        st.error(
            f"Unable to read the Excel file: {e}"
        )

        return


    # COLUMNS

    expected_columns = [
        "User",
        "Team / Department",
        "Date",
        "Shift Start",
        "Shift End",
        "Status",
        "Clock In",
        "Clock Out",
        "1st Break",
        "2nd Break",
        "Lunch",
        "Total"
    ]

    missing_columns = [
        col
        for col in expected_columns
        if col not in df.columns
    ]

    if missing_columns:

        st.error(
            "Required columns are missing."
        )

        st.write(
            missing_columns
        )

        return


    # CLEAN

    df = df[
        expected_columns
    ].copy()

    df["User"] = (
        df["User"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["Team / Department"] = (
        df["Team / Department"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["Status"] = (
        df["Status"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )


    # DURATIONS

    df["_1st_Break_minutes"] = (
        df["1st Break"]
        .apply(parse_duration)
    )

    df["_2nd_Break_minutes"] = (
        df["2nd Break"]
        .apply(parse_duration)
    )

    df["_Lunch_minutes"] = (
        df["Lunch"]
        .apply(parse_duration)
    )

    df["_Recorded_Total_minutes"] = (
        df["Total"]
        .apply(parse_duration)
    )


    # SCHEDULED SHIFT

    df["_Scheduled_Shift_minutes"] = df.apply(
        lambda row:
            calculate_scheduled_minutes(
                row["Shift Start"],
                row["Shift End"]
            ),
        axis=1
    )


    # ACTUAL SHIFT

    df["_Gross_Duty_minutes"] = df.apply(
        lambda row:
            calculate_actual_minutes(
                row["Shift Start"],
                row["Shift End"],
                row["Clock In"],
                row["Clock Out"]
            ),
        axis=1
    )


    # TARDINESS

    df["_Tardiness_minutes"] = df.apply(
        lambda row:
            calculate_tardiness(
                row["Shift Start"],
                row["Shift End"],
                row["Clock In"]
            ),
        axis=1
    )


    # EARLY DEPARTURE

    df["_Early_Departure_minutes"] = df.apply(
        lambda row:
            calculate_early_departure(
                row["Shift Start"],
                row["Shift End"],
                row["Clock Out"]
            ),
        axis=1
    )


    # OVERTIME

    df["_Overtime_minutes"] = df.apply(
        lambda row:
            calculate_overtime(
                row["Shift Start"],
                row["Shift End"],
                row["Clock Out"]
            ),
        axis=1
    )


    # BREAKS

    df["_Break_Lunch_minutes"] = (
        df["_1st_Break_minutes"]
        + df["_2nd_Break_minutes"]
        + df["_Lunch_minutes"]
    )


    # NET

    df["_Calculated_Net_minutes"] = (
        df["_Gross_Duty_minutes"]
        - df["_Break_Lunch_minutes"]
    )

    df["_Calculated_Net_minutes"] = (
        df["_Calculated_Net_minutes"]
        .clip(lower=0)
    )


    # DUTY DAY

    df["_Duty_Day"] = (
        df["_Gross_Duty_minutes"] > 0
    )


    # TOTAL DIFFERENCE

    df["_Total_Difference_minutes"] = (
        df["_Calculated_Net_minutes"]
        - df["_Recorded_Total_minutes"]
    )


    # DATA VALIDATION

    def validate_record(row):

        if not row["_Duty_Day"]:
            return "No Completed Duty"

        if (
            row["_Gross_Duty_minutes"]
            > row["_Scheduled_Shift_minutes"] + 720
        ):
            return "Check DTR"

        if (
            row["_Gross_Duty_minutes"]
            > 18 * 60
        ):
            return "Check DTR"

        difference = abs(
            row["_Total_Difference_minutes"]
        )

        if difference <= 1:
            return "Verified"

        return "Check DTR"


    df["_Verification"] = df.apply(
        validate_record,
        axis=1
    )


    # DISPLAY VALUES

    df["Calculated Shift Start"] = (
        df["Clock In"]
        .apply(format_time)
    )

    df["Calculated Shift End"] = (
        df["Clock Out"]
        .apply(format_time)
    )

    df["Scheduled Shift"] = (
        df["_Scheduled_Shift_minutes"]
        .apply(minutes_to_duration)
    )

    df["Gross Duty"] = (
        df["_Gross_Duty_minutes"]
        .apply(minutes_to_duration)
    )

    df["Tardiness"] = (
        df["_Tardiness_minutes"]
        .apply(minutes_to_duration)
    )

    df["Early Departure"] = (
        df["_Early_Departure_minutes"]
        .apply(minutes_to_duration)
    )

    df["Overtime"] = (
        df["_Overtime_minutes"]
        .apply(minutes_to_duration)
    )

    df["1st Break Total"] = (
        df["_1st_Break_minutes"]
        .apply(minutes_to_duration)
    )

    df["2nd Break Total"] = (
        df["_2nd_Break_minutes"]
        .apply(minutes_to_duration)
    )

    df["Lunch Total"] = (
        df["_Lunch_minutes"]
        .apply(minutes_to_duration)
    )

    df["Break + Lunch Total"] = (
        df["_Break_Lunch_minutes"]
        .apply(minutes_to_duration)
    )

    df["Calculated Net Duty"] = (
        df["_Calculated_Net_minutes"]
        .apply(minutes_to_duration)
    )

    df["Recorded Total"] = (
        df["_Recorded_Total_minutes"]
        .apply(minutes_to_duration)
    )

    df["Total Difference"] = (
        df["_Total_Difference_minutes"]
        .apply(minutes_to_duration)
    )


    # EMPLOYEE SUMMARY

    summary_rows = []

    for (
        user,
        team
    ), group in df.groupby(
        [
            "User",
            "Team / Department"
        ],
        dropna=False
    ):

        duty_days = int(
            group["_Duty_Day"].sum()
        )

        summary_rows.append({

            "User": user,

            "Team / Department": team,

            "Coverage":
                get_coverage(group),

            "Duty Days":
                duty_days,

            "Gross Duty":
                minutes_to_duration(
                    group["_Gross_Duty_minutes"].sum()
                ),

            "Tardiness":
                minutes_to_duration(
                    group["_Tardiness_minutes"].sum()
                ),

            "Early Departure":
                minutes_to_duration(
                    group["_Early_Departure_minutes"].sum()
                ),

            "Overtime":
                minutes_to_duration(
                    group["_Overtime_minutes"].sum()
                ),

            "1st Break":
                minutes_to_duration(
                    group["_1st_Break_minutes"].sum()
                ),

            "2nd Break":
                minutes_to_duration(
                    group["_2nd_Break_minutes"].sum()
                ),

            "Lunch":
                minutes_to_duration(
                    group["_Lunch_minutes"].sum()
                ),

            "Break + Lunch":
                minutes_to_duration(
                    group["_Break_Lunch_minutes"].sum()
                ),

            "Calculated Net Duty":
                minutes_to_duration(
                    group["_Calculated_Net_minutes"].sum()
                ),

            "Recorded Total":
                minutes_to_duration(
                    group["_Recorded_Total_minutes"].sum()
                ),

            "Total Difference":
                minutes_to_duration(
                    group["_Total_Difference_minutes"].sum()
                ),

            "Late":
                status_count(
                    group["Status"],
                    "Late"
                ),

            "Absent":
                status_count(
                    group["Status"],
                    "Absent"
                ),

            "Vacation Leave":
                status_count(
                    group["Status"],
                    "Leave (Vacation Leave)"
                ),

            "Sick Leave":
                int(
                    group["Status"]
                    .astype(str)
                    .str.contains(
                        "Sick Leave",
                        case=False,
                        na=False
                    )
                    .sum()
                ),

            "Rest Days":
                status_count(
                    group["Status"],
                    "Rest Day"
                ),

            "DTR Records to Check":
                int(
                    (
                        group["_Verification"]
                        == "Check DTR"
                    ).sum()
                )
        })

    summary_df = pd.DataFrame(
        summary_rows
    )


    # MONTHLY EMPLOYEE

    monthly_source = df.copy()

    monthly_source["Month"] = (
        monthly_source["Date"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly_rows = []

    for (
        user,
        team,
        month
    ), group in monthly_source.groupby(
        [
            "User",
            "Team / Department",
            "Month"
        ],
        dropna=False
    ):

        monthly_rows.append({

            "User": user,

            "Team / Department": team,

            "Month": month,

            "Coverage":
                get_coverage(group),

            "Duty Days":
                int(
                    group["_Duty_Day"].sum()
                ),

            "Gross Duty":
                minutes_to_duration(
                    group["_Gross_Duty_minutes"].sum()
                ),

            "Tardiness":
                minutes_to_duration(
                    group["_Tardiness_minutes"].sum()
                ),

            "Early Departure":
                minutes_to_duration(
                    group["_Early_Departure_minutes"].sum()
                ),

            "Overtime":
                minutes_to_duration(
                    group["_Overtime_minutes"].sum()
                ),

            "1st Break":
                minutes_to_duration(
                    group["_1st_Break_minutes"].sum()
                ),

            "2nd Break":
                minutes_to_duration(
                    group["_2nd_Break_minutes"].sum()
                ),

            "Lunch":
                minutes_to_duration(
                    group["_Lunch_minutes"].sum()
                ),

            "Break + Lunch":
                minutes_to_duration(
                    group["_Break_Lunch_minutes"].sum()
                ),

            "Calculated Net Duty":
                minutes_to_duration(
                    group["_Calculated_Net_minutes"].sum()
                ),

            "Recorded Total":
                minutes_to_duration(
                    group["_Recorded_Total_minutes"].sum()
                ),

            "Total Difference":
                minutes_to_duration(
                    group["_Total_Difference_minutes"].sum()
                ),

            "Late":
                status_count(
                    group["Status"],
                    "Late"
                ),

            "Absent":
                status_count(
                    group["Status"],
                    "Absent"
                ),

            "Vacation Leave":
                status_count(
                    group["Status"],
                    "Leave (Vacation Leave)"
                ),

            "Sick Leave":
                int(
                    group["Status"]
                    .astype(str)
                    .str.contains(
                        "Sick Leave",
                        case=False,
                        na=False
                    )
                    .sum()
                ),

            "Rest Days":
                status_count(
                    group["Status"],
                    "Rest Day"
                ),

            "DTR Records to Check":
                int(
                    (
                        group["_Verification"]
                        == "Check DTR"
                    ).sum()
                )
        })

    monthly_employee_df = pd.DataFrame(
        monthly_rows
    )


    # VERIFICATION

    verification_columns = [
        "User",
        "Team / Department",
        "Date",
        "Shift Start",
        "Shift End",
        "Status",
        "Clock In",
        "Clock Out",
        "Calculated Shift Start",
        "Calculated Shift End",
        "Scheduled Shift",
        "Gross Duty",
        "Tardiness",
        "Early Departure",
        "Overtime",
        "1st Break Total",
        "2nd Break Total",
        "Lunch Total",
        "Break + Lunch Total",
        "Calculated Net Duty",
        "Total",
        "Recorded Total",
        "Total Difference",
        "_Verification"
    ]

    verification_df = df[
        verification_columns
    ].copy()

    verification_df = verification_df.rename(
        columns={
            "_Verification": "Verification"
        }
    )


    # DASHBOARD TOTALS

    total_employees = (
        df["User"]
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

    total_records = len(df)

    total_duty_days = int(
        df["_Duty_Day"].sum()
    )

    total_gross = int(
        df["_Gross_Duty_minutes"].sum()
    )

    total_tardiness = int(
        df["_Tardiness_minutes"].sum()
    )

    total_early = int(
        df["_Early_Departure_minutes"].sum()
    )

    total_overtime = int(
        df["_Overtime_minutes"].sum()
    )

    total_break_1 = int(
        df["_1st_Break_minutes"].sum()
    )

    total_break_2 = int(
        df["_2nd_Break_minutes"].sum()
    )

    total_lunch = int(
        df["_Lunch_minutes"].sum()
    )

    total_break_lunch = int(
        df["_Break_Lunch_minutes"].sum()
    )

    total_net = int(
        df["_Calculated_Net_minutes"].sum()
    )

    total_recorded = int(
        df["_Recorded_Total_minutes"].sum()
    )

    total_difference = int(
        df["_Total_Difference_minutes"].sum()
    )

    records_to_check = int(
        (
            df["_Verification"]
            == "Check DTR"
        ).sum()
    )


    dashboard_df = pd.DataFrame({

        "Metric": [

            "Employees",
            "Attendance Records",
            "Duty Days",
            "Gross Duty",
            "Tardiness",
            "Early Departure",
            "Overtime",
            "1st Break",
            "2nd Break",
            "Lunch",
            "Break + Lunch",
            "Calculated Net Duty",
            "Recorded Total",
            "Total Difference",
            "DTR Records to Check"
        ],

        "Value": [

            total_employees,
            total_records,
            total_duty_days,

            minutes_to_duration(
                total_gross
            ),

            minutes_to_duration(
                total_tardiness
            ),

            minutes_to_duration(
                total_early
            ),

            minutes_to_duration(
                total_overtime
            ),

            minutes_to_duration(
                total_break_1
            ),

            minutes_to_duration(
                total_break_2
            ),

            minutes_to_duration(
                total_lunch
            ),

            minutes_to_duration(
                total_break_lunch
            ),

            minutes_to_duration(
                total_net
            ),

            minutes_to_duration(
                total_recorded
            ),

            minutes_to_duration(
                total_difference
            ),

            records_to_check
        ]
    })


    # DASHBOARD

    st.subheader(
        "📊 Payroll Dashboard"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Employees",
            total_employees
        )

    with col2:
        st.metric(
            "Duty Days",
            total_duty_days
        )

    with col3:
        st.metric(
            "Gross Duty",
            minutes_to_duration(
                total_gross
            )
        )

    with col4:
        st.metric(
            "Net Duty",
            minutes_to_duration(
                total_net
            )
        )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Tardiness",
            minutes_to_duration(
                total_tardiness
            )
        )

    with col2:
        st.metric(
            "Early Departure",
            minutes_to_duration(
                total_early
            )
        )

    with col3:
        st.metric(
            "Overtime",
            minutes_to_duration(
                total_overtime
            )
        )

    with col4:
        st.metric(
            "DTR To Check",
            records_to_check
        )


    # EMPLOYEE SUMMARY

    st.subheader(
        "📋 Employee Payroll Summary"
    )

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )


    # MONTHLY EMPLOYEE

    st.subheader(
        "📅 Employee Monthly Payroll"
    )

    st.dataframe(
        monthly_employee_df,
        use_container_width=True,
        hide_index=True
    )


    # VERIFICATION

    st.subheader(
        "🔎 DTR Verification"
    )

    st.dataframe(
        verification_df,
        use_container_width=True,
        hide_index=True
    )


    # PROBLEM RECORDS

    check_df = verification_df[
        verification_df["Verification"]
        == "Check DTR"
    ].copy()

    if not check_df.empty:

        st.subheader(
            "⚠️ Records Requiring Verification"
        )

        st.warning(
            f"{len(check_df)} DTR record(s) "
            "require admin verification."
        )

        st.dataframe(
            check_df,
            use_container_width=True,
            hide_index=True
        )


    # STATUS

    st.subheader(
        "📌 Status Summary"
    )

    status_summary = (
        df["Status"]
        .value_counts()
        .reset_index()
    )

    status_summary.columns = [
        "Status",
        "Count"
    ]

    st.dataframe(
        status_summary,
        use_container_width=True,
        hide_index=True
    )


    # MONTHLY OVERALL

    st.subheader(
        "📅 Overall Monthly Payroll"
    )

    monthly_overall = (
        monthly_source
        .groupby("Month")
        .agg(

            Duty_Days=(
                "_Duty_Day",
                "sum"
            ),

            Gross_Duty=(
                "_Gross_Duty_minutes",
                "sum"
            ),

            Tardiness=(
                "_Tardiness_minutes",
                "sum"
            ),

            Early_Departure=(
                "_Early_Departure_minutes",
                "sum"
            ),

            Overtime=(
                "_Overtime_minutes",
                "sum"
            ),

            First_Break=(
                "_1st_Break_minutes",
                "sum"
            ),

            Second_Break=(
                "_2nd_Break_minutes",
                "sum"
            ),

            Lunch=(
                "_Lunch_minutes",
                "sum"
            ),

            Net_Duty=(
                "_Calculated_Net_minutes",
                "sum"
            ),

            Recorded_Total=(
                "_Recorded_Total_minutes",
                "sum"
            )
        )
        .reset_index()
    )


    monthly_overall[
        "Gross Duty"
    ] = monthly_overall[
        "Gross_Duty"
    ].apply(minutes_to_duration)

    monthly_overall[
        "Tardiness"
    ] = monthly_overall[
        "Tardiness"
    ].apply(minutes_to_duration)

    monthly_overall[
        "Early Departure"
    ] = monthly_overall[
        "Early_Departure"
    ].apply(minutes_to_duration)

    monthly_overall[
        "Overtime"
    ] = monthly_overall[
        "Overtime"
    ].apply(minutes_to_duration)

    monthly_overall[
        "1st Break"
    ] = monthly_overall[
        "First_Break"
    ].apply(minutes_to_duration)

    monthly_overall[
        "2nd Break"
    ] = monthly_overall[
        "Second_Break"
    ].apply(minutes_to_duration)

    monthly_overall[
        "Lunch"
    ] = monthly_overall[
        "Lunch"
    ].apply(minutes_to_duration)

    monthly_overall[
        "Net Duty"
    ] = monthly_overall[
        "Net_Duty"
    ].apply(minutes_to_duration)

    monthly_overall[
        "Recorded Total"
    ] = monthly_overall[
        "Recorded_Total"
    ].apply(minutes_to_duration)


    monthly_overall = monthly_overall[
        [
            "Month",
            "Duty_Days",
            "Gross Duty",
            "Tardiness",
            "Early Departure",
            "Overtime",
            "1st Break",
            "2nd Break",
            "Lunch",
            "Net Duty",
            "Recorded Total"
        ]
    ]

    monthly_overall = monthly_overall.rename(
        columns={
            "Duty_Days": "Duty Days"
        }
    )


    st.dataframe(
        monthly_overall,
        use_container_width=True,
        hide_index=True
    )


    # DETAIL

    st.subheader(
        "📝 Attendance Detail"
    )

    detail_columns = [
        "User",
        "Team / Department",
        "Date",
        "Shift Start",
        "Shift End",
        "Status",
        "Clock In",
        "Clock Out",
        "Calculated Shift Start",
        "Calculated Shift End",
        "Scheduled Shift",
        "Gross Duty",
        "Tardiness",
        "Early Departure",
        "Overtime",
        "1st Break",
        "1st Break Total",
        "2nd Break",
        "2nd Break Total",
        "Lunch",
        "Lunch Total",
        "Break + Lunch Total",
        "Calculated Net Duty",
        "Total",
        "Recorded Total",
        "Total Difference",
        "_Verification"
    ]

    detail_df = df[
        detail_columns
    ].copy()

    detail_df = detail_df.rename(
        columns={
            "_Verification": "Verification"
        }
    )


    st.dataframe(
        detail_df,
        use_container_width=True,
        hide_index=True
    )


    # DOWNLOAD

    excel_file = make_excel(
        dashboard_df,
        summary_df,
        monthly_employee_df,
        verification_df,
        detail_df
    )

    st.download_button(
        label="⬇️ Download Complete Payroll DTR Excel",
        data=excel_file,
        file_name="attendance_payroll_dtr.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


# RUN

if __name__ == "__main__":
    run()

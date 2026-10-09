import streamlit as st
import pandas as pd
import re
import json
import os
from io import BytesIO


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Prohibited Item Detection",
    page_icon="📄",
    layout="wide"
)


# ============================================================
# CONFIGURATION
# ============================================================

RULES_FILE = "prohibited_rules.json"

ADMIN_USERNAME = "acbadmin"

TRACKING_COLUMN = "Reliable_tracking"
DESCRIPTION_COLUMN = "Goods_Description"
WEIGHT_COLUMN = "Parcel_item_weight"


# ============================================================
# DEFAULT PROHIBITED RULES
# ============================================================

DEFAULT_RULES = {

    "keywords": [
        "BABY WALKER",
        "MILK",
        "DAIRY",
        "EGG",
        "TREATS",
        "CAT FOOD",
        "DOG FOOD",
        "ANIMAL FOOD",
        "GHEE",
        "ALCOHOL",
        "WINE",
        "ROASTED",
        "MEAT",
        "SAUSAGE",
        "KNIFE",
        "JERKY",
        "BUTTER",
        "FIREARMS",
        "GUNS",
        "WHISKEY",
        "DOG FLEA POWDER",
        "MINIMOOS",
        "MINERAL JUNKIE BITES",
        "UNITED CHEMICALS YELLOWTREAT MUSTARD ALGAECIDE",
        "BEEF CHEWY",
        "PET DENTAL POWDER",
        "PET TARTAR CARE AGENT",
        "PLANT",
        "SEED",
        "ROOSTER BOOSTER",
        "CREAMER",
        "FERRETS",
        "CHEW",

        # APC Prohibited Item List

        "A&E CAGE CO",
        "CAPTAIN CUTTLEBONE NATURAL CUTTLEBONE FOR BIRDS",
        "ALCOHOLIC BEVERAGES",
        "ANIMAL FEED/PET FOOD",
        "BABY WALKERS",
        "BRUSSELS BONSAI",
        "SMALL LIVE BONSAI",
        "BONSAI TREE",
        "CANNABIS AND ILLEGAL DRUGS",
        "CAT-MAN-DOO",
        "BONITO FISH FLAKES",
        "CREAMER",
        "DAIRY PRODUCTS",
        "GHEE",
        "BUTTER",
        "EGGS",
        "DOG FOOD/ PUPGANICS",
        "EXPLOSIVES AND FIREWORKS",
        "FERRETS",
        "FIREARMS AND WEAPONS",
        "HENRYS HEALTHY BLOCKS",
        "FOOD FOR SQUIRRELS",
        "FOOD FOR FLYERS",
        "FOOD FOR RATS",
        "FOOD FOR MICE",
        "KNIFES",
        "LOVE MY GIRLS 5LB CHICKEN SNACKS",
        "MEAT AND JERKY PRODUCTS",
        "MINERAL JUNKIE BITES",
        "MINI MOOSE PRODUCTS",
        "MOLLY MCBUTTER",
        "FAT FREE BUTTER FLAVOR SPRINKLES",
        "PET TARTAR",
        "PET TREATS AND CHEWS",
        "PLANTS",
        "REPASHY SUPERFOODS MORNING WOOD",
        "FOOD FOR DUBIA ROACHES",
        "ROACH GUTLOAD FORMULA",
        "NUTRIENT-RICH PRE-FEEDING DIET",
        "FEEDER INSECTS",
        "ROOSTER BOOSTER B12 LIQUID",
        "SEEDS",
        "THE GERMAN HORSE MUFFIN",
        "VALENTINO VENDETTA ROACH GEL BAIT INSECTICIDE 4",
        "ALL NATURAL HORSE TREATS",
        "TOBACCO AND VAPING PRODUCTS",
        "PULSAR SESH GEAR",
        "UNITED CHEMICALS YELLOWTREAT MUSTARD ALGAECIDE",
        "LEAD PELLETS FOR AIR GUNS",
        "MIRACLE-GRO SHAKE N FEED PALM PLANT FOOD, 4.5 LB",
        "HORSE HEALTH CANINE RED CELL LIQUID VITAMINIRON",
        "SNAPPY BUTTER BURST POPCORN OIL MOVIE THEATER BUTTER OIL FOR MACHINES AND STOVETOPS NATURALLY COL",
        "2 LBS (32 OZ), MYLAR BAG WITH OXYGEN ABSORBER FOR LONG SHELF-LIFE, 70 SERVINGS, CAGE-FREE POWDERED EGGS",
        "REPELSALL ANIMAL REPELLENT READYTOUSE 1 GALLON",
        "MAXFORCE COMPLETE GRANULAR INSECT BAIT 8 OUNCES",
        "SYNGENTA 383920 ADVION COCKROACH GEL BAIT 4 X 30 G",
        "POLYMER ANGLED FORE GRIP FOR FIREARMS",
        "SHEBA PERFECT PORTIONS CUTS WET CAT FOOD ROASTED",
        "OSTRICH FEATHERS FOR DECORATION"
    ],

    "addresses": [
        "1469 WESTCOTT ROAD",
        "WINDSOR, ON",
        "N8Y 4C3"
    ],

    "consignees": [
        "GUILLAUME GAGN",
        "2545 RUE BEAUDRY APP 30",
        "SHERBROOKE, QC",
        "J1J1K9",
        "CANADA",
        "14185647924"
    ]
}


# ============================================================
# RULE STORAGE
# ============================================================

def copy_default_rules():

    return {
        "keywords": DEFAULT_RULES["keywords"].copy(),
        "addresses": DEFAULT_RULES["addresses"].copy(),
        "consignees": DEFAULT_RULES["consignees"].copy()
    }


def save_rules(rules):

    try:

        with open(
            RULES_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                rules,
                file,
                indent=4,
                ensure_ascii=False
            )

        return True

    except Exception as error:

        st.error(
            f"Unable to save prohibited rules: {error}"
        )

        return False


def load_rules():

    if not os.path.exists(RULES_FILE):

        rules = copy_default_rules()

        save_rules(rules)

        return rules

    try:

        with open(
            RULES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            rules = json.load(file)

        rules.setdefault(
            "keywords",
            []
        )

        rules.setdefault(
            "addresses",
            []
        )

        rules.setdefault(
            "consignees",
            []
        )

        return rules

    except Exception as error:

        st.warning(
            f"Could not read rules file. "
            f"Default rules loaded instead. Error: {error}"
        )

        return copy_default_rules()


# ============================================================
# CONVERT RULES TO DATAFRAME
# ============================================================

def rules_to_dataframe(rules):

    rows = []

    counter = 1

    for rule in rules.get(
        "keywords",
        []
    ):

        rows.append({
            "No.": counter,
            "TYPE": "PRODUCT",
            "PROHIBITED RULE": rule
        })

        counter += 1

    for rule in rules.get(
        "addresses",
        []
    ):

        rows.append({
            "No.": counter,
            "TYPE": "ADDRESS",
            "PROHIBITED RULE": rule
        })

        counter += 1

    for rule in rules.get(
        "consignees",
        []
    ):

        rows.append({
            "No.": counter,
            "TYPE": "CONSIGNEE",
            "PROHIBITED RULE": rule
        })

        counter += 1

    return pd.DataFrame(
        rows,
        columns=[
            "No.",
            "TYPE",
            "PROHIBITED RULE"
        ]
    )


# ============================================================
# DATAFRAME TO RULES
# ============================================================

def dataframe_to_rules(df):

    rules = {
        "keywords": [],
        "addresses": [],
        "consignees": []
    }

    for _, row in df.iterrows():

        rule_type = str(
            row.get(
                "TYPE",
                ""
            )
        ).strip().upper()

        rule_value = str(
            row.get(
                "PROHIBITED RULE",
                ""
            )
        ).strip()

        if (
            not rule_value
            or rule_value.lower() == "nan"
        ):

            continue

        rule_value = " ".join(
            rule_value.upper().split()
        )

        if rule_type == "PRODUCT":

            if rule_value not in rules["keywords"]:

                rules["keywords"].append(
                    rule_value
                )

        elif rule_type == "ADDRESS":

            if rule_value not in rules["addresses"]:

                rules["addresses"].append(
                    rule_value
                )

        elif rule_type == "CONSIGNEE":

            if rule_value not in rules["consignees"]:

                rules["consignees"].append(
                    rule_value
                )

    # Keep rules organized

    rules["keywords"] = sorted(
        rules["keywords"]
    )

    rules["addresses"] = sorted(
        rules["addresses"]
    )

    rules["consignees"] = sorted(
        rules["consignees"]
    )

    return rules


# ============================================================
# AUTHENTICATION
# ============================================================

def get_users():

    try:

        return dict(
            st.secrets["credentials"]["users"]
        )

    except Exception:

        st.error(
            "Could not find [credentials.users] "
            "in Streamlit secrets."
        )

        return {}


@st.dialog(
    "🔐 Administrator Authorization"
)
def admin_login_dialog():

    st.write(
        "Administrator permission is required "
        "to modify prohibited rules."
    )

    st.caption(
        "Normal shipment scanning does not require login."
    )

    username = st.text_input(
        "Username",
        key="admin_username"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="admin_password"
    )

    col1, col2 = st.columns(2)

    with col1:

        login_clicked = st.button(
            "🔓 Login",
            use_container_width=True
        )

    with col2:

        cancel_clicked = st.button(
            "Cancel",
            use_container_width=True
        )

    if cancel_clicked:

        st.session_state[
            "show_admin_login"
        ] = False

        st.rerun()

    if login_clicked:

        users = get_users()

        if (
            username == ADMIN_USERNAME
            and username in users
            and password == users[username]
        ):

            st.session_state[
                "admin_authenticated"
            ] = True

            st.session_state[
                "show_admin_login"
            ] = False

            st.session_state[
                "open_admin_panel"
            ] = True

            st.success(
                "✅ Administrator authorization successful."
            )

            st.rerun()

        else:

            st.error(
                "❌ Invalid administrator credentials."
            )


# ============================================================
# ADMIN DATAFRAME EDITOR
# ============================================================

def admin_panel():

    st.header(
        "🛠️ Prohibited Rule Management"
    )

    st.success(
        "🔐 Administrator access is active."
    )

    st.warning(
        "Changes will affect future shipment scans."
    )

    rules = load_rules()

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    total_keywords = len(
        rules["keywords"]
    )

    total_addresses = len(
        rules["addresses"]
    )

    total_consignees = len(
        rules["consignees"]
    )

    total_rules = (
        total_keywords
        + total_addresses
        + total_consignees
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Rules",
            total_rules
        )

    with col2:

        st.metric(
            "Products",
            total_keywords
        )

    with col3:

        st.metric(
            "Addresses",
            total_addresses
        )

    with col4:

        st.metric(
            "Consignees",
            total_consignees
        )

    st.markdown("---")

    # --------------------------------------------------------
    # Search / Filter
    # --------------------------------------------------------

    filter_col1, filter_col2 = st.columns(
        [2, 1]
    )

    with filter_col1:

        search_text = st.text_input(
            "🔍 Search prohibited rules",
            placeholder="Search keyword, address, or consignee..."
        )

    with filter_col2:

        type_filter = st.selectbox(
            "Filter by type",
            [
                "ALL",
                "PRODUCT",
                "ADDRESS",
                "CONSIGNEE"
            ]
        )

    # --------------------------------------------------------
    # Build dataframe
    # --------------------------------------------------------

    df_rules = rules_to_dataframe(
        rules
    )

    # --------------------------------------------------------
    # Filter dataframe for display
    # --------------------------------------------------------

    display_df = df_rules.copy()

    if type_filter != "ALL":

        display_df = display_df[
            display_df["TYPE"] == type_filter
        ]

    if search_text:

        search_upper = search_text.upper()

        display_df = display_df[
            display_df[
                "PROHIBITED RULE"
            ].str.upper().str.contains(
                search_upper,
                na=False,
                regex=False
            )
        ]

    # --------------------------------------------------------
    # Admin editor
    # --------------------------------------------------------

    st.subheader(
        "📋 Prohibited Rules"
    )

    st.caption(
        "Edit the TYPE or PROHIBITED RULE directly in the table. "
        "Use the trash icon to delete a row."
    )

    edited_df = st.data_editor(

        display_df,

        use_container_width=True,

        num_rows="dynamic",

        hide_index=True,

        key="prohibited_rules_editor",

        column_config={

            "No.": st.column_config.NumberColumn(
                "No.",
                disabled=True,
                width="small"
            ),

            "TYPE": st.column_config.SelectboxColumn(
                "TYPE",
                options=[
                    "PRODUCT",
                    "ADDRESS",
                    "CONSIGNEE"
                ],
                required=True,
                width="medium"
            ),

            "PROHIBITED RULE": st.column_config.TextColumn(
                "PROHIBITED RULE",
                required=True,
                width="large"
            )
        }
    )

    st.markdown("---")

    # --------------------------------------------------------
    # SAVE CHANGES
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "💾 Save Changes",
            type="primary",
            use_container_width=True
        ):

            # Important:
            # If a search/filter is active, the editor only
            # contains the filtered rows. We therefore merge
            # the edited rows back into the complete list.

            full_df = df_rules.copy()

            if (
                search_text
                or type_filter != "ALL"
            ):

                edited_keys = set(
                    display_df["No."]
                )

                # Remove old versions of edited rows

                full_df = full_df[
                    ~full_df["No."].isin(
                        edited_keys
                    )
                ]

                # Re-add edited rows

                full_df = pd.concat(
                    [
                        full_df,
                        edited_df
                    ],
                    ignore_index=True
                )

            else:

                full_df = edited_df.copy()

            # Remove numbering before rebuilding

            if "No." in full_df.columns:

                full_df = full_df.drop(
                    columns=["No."]
                )

            # Validate types

            valid_types = [
                "PRODUCT",
                "ADDRESS",
                "CONSIGNEE"
            ]

            invalid_types = full_df[
                ~full_df["TYPE"].isin(
                    valid_types
                )
            ]

            if not invalid_types.empty:

                st.error(
                    "❌ Invalid TYPE detected. "
                    "Use PRODUCT, ADDRESS, or CONSIGNEE."
                )

                return

            # Remove blank rules

            full_df[
                "PROHIBITED RULE"
            ] = full_df[
                "PROHIBITED RULE"
            ].fillna("").astype(str).str.strip()

            full_df = full_df[
                full_df[
                    "PROHIBITED RULE"
                ] != ""
            ]

            # Rebuild rules

            new_rules = dataframe_to_rules(
                full_df
            )

            if save_rules(
                new_rules
            ):

                st.success(
                    "✅ Prohibited rules saved successfully."
                )

                # Clear editor state so the updated
                # dataframe is loaded fresh.

                st.session_state.pop(
                    "prohibited_rules_editor",
                    None
                )

                st.rerun()

    with col2:

        if st.button(
            "🔄 Reload Rules",
            use_container_width=True
        ):

            st.session_state.pop(
                "prohibited_rules_editor",
                None
            )

            st.rerun()

    st.markdown("---")

    # --------------------------------------------------------
    # CLOSE ADMIN
    # --------------------------------------------------------

    if st.button(
        "🔒 Close Administrator Mode",
        use_container_width=True
    ):

        st.session_state[
            "admin_authenticated"
        ] = False

        st.session_state[
            "open_admin_panel"
        ] = False

        st.session_state.pop(
            "prohibited_rules_editor",
            None
        )

        st.rerun()


# ============================================================
# DETECTION
# ============================================================

def detect(
    df,
    rules
):

    results = []

    keywords = rules.get(
        "keywords",
        []
    )

    addresses = rules.get(
        "addresses",
        []
    )

    consignees = rules.get(
        "consignees",
        []
    )

    for _, row in df.iterrows():

        text = " ".join(
            str(value)
            for value in row.tolist()
            if pd.notna(value)
        ).upper()

        # ----------------------------------------------------
        # Product keywords
        # ----------------------------------------------------

        product_found = [

            keyword

            for keyword in keywords

            if re.search(
                r"\b"
                + re.escape(keyword)
                + r"\b",
                text
            )
        ]

        # ----------------------------------------------------
        # Address
        # ----------------------------------------------------

        address_found = [

            address

            for address in addresses

            if re.search(
                r"\b"
                + re.escape(address)
                + r"\b",
                text
            )
        ]

        # ----------------------------------------------------
        # Consignee
        # ----------------------------------------------------

        consignee_found = [

            consignee

            for consignee in consignees

            if re.search(
                r"\b"
                + re.escape(consignee)
                + r"\b",
                text
            )
        ]

        found = (
            product_found
            + address_found
            + consignee_found
        )

        issue = []

        if product_found:

            issue.append(
                "PROHIBITED ITEM - PRODUCT"
            )

        if address_found:

            issue.append(
                "PROHIBITED ADDRESS"
            )

        if consignee_found:

            issue.append(
                "PROHIBITED CONSIGNEE"
            )

        if found:

            results.append({

                TRACKING_COLUMN:
                    row.get(
                        TRACKING_COLUMN,
                        ""
                    ),

                DESCRIPTION_COLUMN:
                    row.get(
                        DESCRIPTION_COLUMN,
                        ""
                    ),

                WEIGHT_COLUMN:
                    row.get(
                        WEIGHT_COLUMN,
                        ""
                    ),

                "Detected_Prohibited":
                    ", ".join(found),

                "Issue":
                    " | ".join(issue)
            })

    return pd.DataFrame(
        results
    )


# ============================================================
# EXCEL EXPORT
# ============================================================

def export_excel(df):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="xlsxwriter"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Validation_Result"
        )

    return output.getvalue()


# ============================================================
# MAIN APPLICATION
# ============================================================

def run():

    # --------------------------------------------------------
    # Session state
    # --------------------------------------------------------

    if "show_admin_login" not in st.session_state:

        st.session_state[
            "show_admin_login"
        ] = False

    if "admin_authenticated" not in st.session_state:

        st.session_state[
            "admin_authenticated"
        ] = False

    if "open_admin_panel" not in st.session_state:

        st.session_state[
            "open_admin_panel"
        ] = False

    # --------------------------------------------------------
    # Main header
    # --------------------------------------------------------

    st.subheader(
        "📄 PROHIBITED ITEM DETECTION"
    )

    st.caption(
        "Upload a shipment file to scan for prohibited "
        "items, addresses, and consignees."
    )

    # --------------------------------------------------------
    # ADMIN BUTTON
    # --------------------------------------------------------

    if not st.session_state.get(
        "admin_authenticated",
        False
    ):

        if st.button(
            "🔐 Manage Prohibited Rules"
        ):

            st.session_state[
                "show_admin_login"
            ] = True

            st.rerun()

    else:

        col1, col2 = st.columns(
            [3, 1]
        )

        with col1:

            st.success(
                "🔐 Administrator Mode Active"
            )

        with col2:

            if st.button(
                "🛠️ Rule Management",
                use_container_width=True
            ):

                st.session_state[
                    "open_admin_panel"
                ] = True

                st.rerun()

    # --------------------------------------------------------
    # ADMIN LOGIN MODAL
    # --------------------------------------------------------

    if st.session_state.get(
        "show_admin_login",
        False
    ):

        admin_login_dialog()

    # --------------------------------------------------------
    # ADMIN PANEL
    # --------------------------------------------------------

    if (
        st.session_state.get(
            "admin_authenticated",
            False
        )
        and st.session_state.get(
            "open_admin_panel",
            False
        )
    ):

        st.markdown("---")

        admin_panel()

        st.markdown("---")

    # --------------------------------------------------------
    # NORMAL SCANNER
    # --------------------------------------------------------

    st.subheader(
        "📤 Upload Shipment File"
    )

    uploaded_file = st.file_uploader(
        "Upload Shipment File",
        type=[
            "xlsx",
            "xls",
            "csv"
        ]
    )

    # --------------------------------------------------------
    # Process file
    # --------------------------------------------------------

    if uploaded_file:

        try:

            if uploaded_file.name.lower().endswith(
                ".csv"
            ):

                df = pd.read_csv(
                    uploaded_file
                )

            else:

                df = pd.read_excel(
                    uploaded_file
                )

        except Exception as error:

            st.error(
                f"Unable to read uploaded file: {error}"
            )

            return

        # ----------------------------------------------------
        # Required columns
        # ----------------------------------------------------

        required_columns = [
            TRACKING_COLUMN,
            DESCRIPTION_COLUMN,
            WEIGHT_COLUMN
        ]

        missing = [

            column

            for column in required_columns

            if column not in df.columns

        ]

        if missing:

            st.error(
                f"Missing columns: {missing}"
            )

            return

        # ----------------------------------------------------
        # Scan
        # ----------------------------------------------------

        with st.spinner(
            "Scanning shipment data..."
        ):

            # Always load the newest rules.

            rules = load_rules()

            result = detect(
                df,
                rules
            )

        # ----------------------------------------------------
        # Results
        # ----------------------------------------------------

        if result.empty:

            st.success(
                "✅ No prohibited items detected"
            )

        else:

            st.error(
                f"🚨 {len(result)} shipment(s) flagged"
            )

            st.dataframe(
                result,
                use_container_width=True
            )

            st.download_button(
                "⬇️ Download Validation Report",

                export_excel(
                    result
                ),

                f"PROHIBITED_ITEMS_"
                f"{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
                f".xlsx",

                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )

    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------

    st.markdown("---")

    st.caption(
        "© 2026 ACB Toolkit | Developed by IT Department"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    run()

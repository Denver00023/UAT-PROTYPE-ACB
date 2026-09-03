import streamlit as st
import pandas as pd
import re
from io import BytesIO

# Keywords
KEYWORDS=[
    "BABY WALKER","MILK","DAIRY","EGG","TREATS","CAT FOOD","DOG FOOD",
    "ANIMAL FOOD","GHEE","ALCOHOL","WINE","ROASTED","MEAT","SAUSAGE",
    "KNIFE","JERKY","BUTTER","FIREARMS","GUNS","WHISKEY",
    "DOG FLEA POWDER","MINIMOOS","MINERAL JUNKIE BITES",
    "UNITED CHEMICALS YELLOWTREAT MUSTARD ALGAECIDE", "BEEF CHEWY", "PET DENTAL POWDER",
    "PET TARTAR CARE AGENT", "PLANT", "SEED", "ROOSTER BOOSTER", "CREAMER", "FERRETS", "CHEW",

    # Newly added keywords
    "A&E CAGE CO","CAPTAIN CUTTLEBONE NATURAL CUTTLEBONE FOR BIRDS",
    "ALCOHOLIC BEVERAGES", "ANIMAL FEED/PET FOOD", "BABY WALKERS", "BRUSSELS BONSAI", "SMALL LIVE BONSAI", "BONSAI TREE", "CANNABIS AND ILLEGAL DRUGS",
    "CAT-MAN-DOO", "BONITO FISH FLAKES", "CREAMER", "DAIRY PRODUCTS", "GHEE", "BUTTER", "EGGS", "DOG FOOD/ PUPGANICS", "EXPLOSIVES AND FIREWORKS",
    "FERRETS", "FIREARMS AND WEAPONS", "HENRYS HEALTHY BLOCKS", "FOOD FOR SQUIRRELS", "FOOD FOR FLYERS", "FOOD FOR RATS", "FOOD FOR MICE",
    "KNIFES", "LOVE MY GIRLS 5LB CHICKEN SNACKS", "MEAT AND JERKY PRODUCTS", "MINERAL JUNKIE BITES", "MINI MOOSE PRODUCTS", "MOLLY MCBUTTER",
    "FAT FREE BUTTER FLAVOR SPRINKLES", "PET TARTAR", "PET TREATS AND CHEWS", "PLANTS", "REPASHY SUPERFOODS MORNING WOOD",
    "FOOD FOR DUBIA ROACHES", "ROACH GUTLOAD FORMULA", "NUTRIENT-RICH PRE-FEEDING DIET", "FEEDER INSECTS",
    "ROOSTER BOOSTER B12 LIQUID", "SEEDS", "THE GERMAN HORSE MUFFIN",
    "ALL NATURAL HORSE TREATS", "TOBACCO AND VAPING PRODUCTS", "PULSAR SESH GEAR", "UNITED CHEMICALS YELLOWTREAT MUSTARD ALGAECIDE"
]

PROHIBITED_ADDRESSES=[
    "1469 WESTCOTT ROAD",
    "WINDSOR, ON",
    "N8Y 4C3"
]

PROHIBITED_CONSIGNEES=[
    "GUILLAUME GAGN",
    "2545 RUE BEAUDRY APP 30",
    "SHERBROOKE, QC",
    "J1J1K9",
    "CANADA",
    "14185647924"
]

# Columns
TRACKING_COLUMN="Reliable_tracking"
DESCRIPTION_COLUMN="Goods_Description"
WEIGHT_COLUMN="Parcel_item_weight"

# Detection
def detect(df):

    results=[]

    for _,row in df.iterrows():

        text=" ".join(
            str(value)
            for value in row.tolist()
            if pd.notna(value)
        ).upper()

        # Product keywords
        product_found=[
            keyword
            for keyword in KEYWORDS
            if re.search(
                r"\b"+re.escape(keyword)+r"\b",
                text
            )
        ]

        # Address keywords
        address_found=[
            address
            for address in PROHIBITED_ADDRESSES
            if re.search(
                r"\b"+re.escape(address)+r"\b",
                text
            )
        ]

        # Consignee keywords
        consignee_found=[
            consignee
            for consignee in PROHIBITED_CONSIGNEES
            if re.search(
                r"\b"+re.escape(consignee)+r"\b",
                text
            )
        ]

        found=product_found+address_found+consignee_found

        issue=[]

        if product_found:
            issue.append("PROHIBITED ITEM - PRODUCT")

        if address_found:
            issue.append("PROHIBITED ADDRESS")

        if consignee_found:
            issue.append("PROHIBITED CONSIGNEE")

        if found:

            results.append({

                "Reliable_tracking": row.get(TRACKING_COLUMN, ""),

                "Goods_Description": row.get(DESCRIPTION_COLUMN, ""),

                "Parcel_item_weight": row.get(WEIGHT_COLUMN, ""),

                "Detected_Prohibited": ", ".join(found),

                "Issue":" | ".join(issue)
            })

    return pd.DataFrame(results)

# Export
def export_excel(df):

    output=BytesIO()

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

# App

def run():

    st.subheader("📄 **PROHIBITED ITEM DETECTION**")

    uploaded_file=st.file_uploader(
        "**Upload Shipment File**",
        type=[
            "xlsx",
            "xls",
            "csv"
        ]
    )

    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")

    if uploaded_file:

        if uploaded_file.name.endswith(".csv"):

            df=pd.read_csv(
                uploaded_file
            )

        else:

            df=pd.read_excel(
                uploaded_file
            )

        required_columns=[
            TRACKING_COLUMN,
            DESCRIPTION_COLUMN,
            WEIGHT_COLUMN
        ]

        missing=[
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing:

            st.error(f"Missing columns: {missing}")

            return

        with st.spinner("Scanning shipment data..."):

            result=detect(df)

        if result.empty:

            st.success("**No prohibited items detected**")

        else:

            st.error(f"{len(result)} shipment(s) flagged")

            st.dataframe(result,use_container_width=True)

            st.download_button(
                "Download Validation Report",
                export_excel(result),
                f"PROHIBITED_ITEMS_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__=="__main__":

    run()
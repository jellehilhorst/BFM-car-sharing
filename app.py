import streamlit as st
import pandas as pd
import datetime
import os
import gspread
import google.auth
from google.oauth2.service_account import Credentials


import json

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]



creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
)
client = gspread.authorize(creds)


# Open sheet (insert your sheet ID here)
sheet = client.open_by_key(st.secrets["sheet_id"]).sheet1

names = ["Anelle", "Carlo", "Amber", "Romain", "Tjark", "Other"]

# Load trip data
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Pricing (you can update these)
member_rate = 0.20
non_member_rate = 0.30
non_member_fee = 5.00

# UI
st.title("🚗 Car Sharing Log")

submitted = False
total = 'something went wrong...'

if "step" not in st.session_state:
    st.session_state.step = 1

if st.session_state.step == 1:
    with st.form("name_form"):
        selected_name = st.selectbox("Name", names)
        next_step = st.form_submit_button("Next")
        if next_step:
            if selected_name == "Other":
                st.session_state.step = 2
                st.session_state.is_member = "No"
            else:
                st.session_state.name = selected_name
                st.session_state.is_member = "Yes"
                st.session_state.step = 3
            st.rerun()

elif st.session_state.step == 2:
    with st.form("other_name_form"):
        name = st.text_input("Enter a different name")
        next_step = st.form_submit_button("Next")
        if next_step and name:
            st.session_state.name = name
            st.session_state.step = 3
            st.rerun()


elif st.session_state.step == 3:
    with st.form("trip_form"):
        #   message with cost for memeber
        is_member = st.session_state.is_member
        km_rate = member_rate if is_member == "Yes" else non_member_rate
        extra_fee = 0 if is_member == "Yes" else non_member_fee
        st.info(f"KM cost: €{km_rate:.2f} per km. Extra fee: €{extra_fee:.2f}")
        
        name = st.session_state.name
        trip_date = st.date_input("Date of trip", value=datetime.date.today())
        driven_km = st.number_input("Driven km", step=1)
        refuel = st.number_input("Refuel cost (€)", step=0.5)
        note = st.text_area("Note (optional)")
        submitted = st.form_submit_button("Submit Trip")

        if submitted:
            is_member = st.session_state.is_member
            km_rate = member_rate if is_member == "Yes" else non_member_rate
            extra_fee = 0 if is_member == "Yes" else non_member_fee
            total = round(driven_km * km_rate + refuel + extra_fee, 2)

            new_entry = {
                "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Trip Date": trip_date.strftime("%Y-%m-%d"),
                "Name": name,
                "Driven km": driven_km,
                "Refuel": refuel,
                "Member": is_member,
                "KM Rate": km_rate,
                "Extra Fee": extra_fee,
                "Total": total,
                "Note": note
            }
            sheet.append_row(list(new_entry.values()))
            
            st.session_state.step = 4
            st.rerun()
            


        

elif st.session_state.step == 4:
    st.success(f"Trip saved! Total cost: €{total}")
    st.info("What would you like to do next?")
    show_delete = True
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add another trip"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if show_delete:
            if st.button("Delete previous entry"):
                # Find the last row (assuming the new entry is last)
                last_row = len(sheet.get_all_values())
                sheet.delete_rows(last_row)
                st.success("Previous entry deleted.")
                show_delete = False  # Hide the button after deletion
                st.rerun()

if not df.empty:
    # overview
    st.subheader("🔎 Member Overview")
    

    overview = (
        df.groupby("Name")
        .agg(
        Total_KM=("Driven km", "sum"),
        Driving_Cost=("Driven km", lambda x: round((df.loc[x.index, "KM Rate"] * x).sum(), 2)),
        Refuel_Cost=("Refuel", "sum"),
        Extra_Fees=("Extra Fee", "sum"),
        Total_Balance=("Total", "sum"),
        )
        .reset_index()
    )

    # Format columns: Total_KM as integer, costs/fees as money
    styled_overview = overview.style.format({
        "Total_KM": "{:.0f}",
        "Driving_Cost": "€{:.2f}",
        "Refuel_Cost": "€{:.2f}",
        "Extra_Fees": "€{:.2f}",
        "Total_Balance": "€{:.2f}"
    }).highlight_between(
        subset=["Total_Balance"], left=0, right=None, color="#F0F2F6"
    )

    # Show dataframe with Name column pinned (Streamlit 1.29+)
    st.dataframe(styled_overview, column_config={"Name": st.column_config.Column("Name", pinned=True)})

    # history
    st.subheader("📋 Trip History")
    df = df.sort_values(by="Date", ascending=False)
    st.dataframe(df)

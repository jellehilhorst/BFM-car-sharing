import streamlit as st
import pandas as pd
import datetime
import os
import gspread
import google.auth
from google.oauth2.service_account import Credentials


import json
import pytz

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

st.subheader("Fill in your trip details below")

submitted = False
total = 'something went wrong...'

if "step" not in st.session_state:
    st.session_state.step = 1

if st.session_state.step == 1:
    with st.form("name_form"):
        selected_name = st.selectbox("Name", names)
        col1, col2 = st.columns([1, 1])
        with col1:
            next_step = st.form_submit_button("Next", type="primary")
        with col2:
            transfer_money = st.form_submit_button("Transfer Money")
        if transfer_money:
            st.session_state.step = "transfer_money"
            st.rerun()
        if next_step:
            if selected_name == "Other":
                st.session_state.is_member = "No"
                st.session_state.step = 2
            else:
                st.session_state.name = selected_name
                st.session_state.is_member = "Yes"
                st.session_state.step = 3
            st.rerun()

# transfer money
elif st.session_state.step == "transfer_money":
    with st.form("transfer_form"):
        st.write("Transfer money from one member to another")
        names_in_df = sorted(df["Name"].unique())
        amount = st.number_input("Amount (€)", min_value=0.00, step=1.0, format="%.2f", key="transfer_amount")
        # driven_km = st.number_input("Driven km", step=1)
        col1, col2 = st.columns([1, 1])
        with col1:
            from_name = st.selectbox("From", names_in_df, key="from_name")
        with col2:
            to_name = st.selectbox("To", names_in_df, key="to_name")
            
        submit_transfer = st.form_submit_button("Submit Transfer", type="primary")
        back = st.form_submit_button("Back")
        
        if back:
            st.session_state.step = 1
            st.rerun()
        if submit_transfer and from_name and to_name and amount > 0 and from_name != to_name:
            amsterdam_tz = pytz.timezone("Europe/Amsterdam")
            now_amsterdam = datetime.datetime.now(amsterdam_tz)
            transfer_entry = {
                "Date": now_amsterdam.strftime("%Y-%m-%d %H:%M"),
                "Trip Date": "",
                "Name": from_name,
                "Driven km": 0,
                "Refuel": 0,
                "Member": "",
                "KM Rate": 0,
                "Extra Fee": 0,
                "Total": -amount,
                "Note": f"Transfer to {to_name}"
            }
            sheet.append_row(list(transfer_entry.values()))
            transfer_entry["Name"] = to_name
            transfer_entry["Total"] = amount
            transfer_entry["Note"] = f"Transfer from {from_name}"
            sheet.append_row(list(transfer_entry.values()))
            st.success(f"Transferred €{amount:.2f} from {from_name} to {to_name}.")
            st.session_state.step = 1
            st.rerun()

# other name
elif st.session_state.step == 2:
    with st.form("other_name_form"):
        name = st.text_input("Enter a different name")
        col1, col2 = st.columns([1, 1])
        with col1:
            next_step = st.form_submit_button("Next")
        with col2:
            back = st.form_submit_button("Back")
        if back:
            st.session_state.step = 1
            st.rerun()
        if next_step and name:
            clean_name = name.strip().replace(" ", "").lower().capitalize()
            st.session_state.name = clean_name
            st.session_state.step = 3
            st.rerun()


elif st.session_state.step == 3:
    with st.form("trip_form"):
        #   message with cost for memeber
        is_member = st.session_state.is_member
        km_rate = member_rate if is_member == "Yes" else non_member_rate
        extra_fee = 0 if is_member == "Yes" else non_member_fee
        if extra_fee > 0:
            st.info(f"KM cost: €{km_rate:.2f} per km. Extra fee: €{extra_fee:.2f}")
        else:
            st.info(f"KM cost: €{km_rate:.2f} per km.")
        
        name = st.session_state.name
        trip_date = st.date_input("Date of trip", value=datetime.date.today())
        driven_km = st.number_input("Driven km", step=1)
        
        refuel = st.number_input("Refuel cost (€)", step=0.5)
        note = st.text_area("Note (optional)")
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Submit Trip", type="primary")
        with col2:
            back = st.form_submit_button("Back")
        if back:
            st.session_state.step = 1
            st.rerun()
        
        
        if submitted:
            is_member = st.session_state.is_member
            km_rate = member_rate if is_member == "Yes" else non_member_rate
            extra_fee = 0 if is_member == "Yes" else non_member_fee
            total = round(driven_km * -km_rate + refuel + -extra_fee, 2)

            amsterdam_tz = pytz.timezone("Europe/Amsterdam")
            now_amsterdam = datetime.datetime.now(amsterdam_tz)
            new_entry = {
                "Date": now_amsterdam.strftime("%Y-%m-%d %H:%M"),
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
    st.info("What would you like to do next?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add another trip"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        
        if st.button("Delete previous entry"):
            # Find the last row (assuming the new entry is last)
            last_row = len(sheet.get_all_values())
            sheet.delete_rows(last_row)
            st.success("Previous entry deleted.")
            st.session_state.step = 1
            st.rerun()

if not df.empty:
    # overview
    st.subheader("🔎 Member Overview")
    

    overview = (
        df.groupby("Name")
        .agg(
            **{
                "Driven km": ("Driven km", "sum"),
                "Driving cost": ("Driven km", lambda x: round((df.loc[x.index, "KM Rate"] * x).sum(), 2)),
                "Refuel cost": ("Refuel", "sum"),
                "Extra fees": ("Extra Fee", "sum"),
                "Total balance": ("Total", "sum"),
            }
        )
        .reset_index()
    )

    # Format columns: Driven km as integer, costs/fees as money
    def color_total_balance(val):
        color = "#006400" if val >= 0 else "#8B0000"  # dark green or dark red
        return f"color: {color}"

    styled_overview = overview.style.format({
        "Driven km": "{:.0f}",
        "Driving cost": "€{:.2f}",
        "Refuel cost": "€{:.2f}",
        "Extra fees": "€{:.2f}",
        "Total balance": "€{:.2f}"
    }).applymap(color_total_balance, subset=["Total balance"])
    
    # Show dataframe with Name column pinned (Streamlit 1.29+)
    st.dataframe(styled_overview, column_config={"Name": st.column_config.Column("Name", pinned=True)})

    # history
    st.subheader("📋 Trip History")
    df = df.sort_values(by="Date", ascending=False)
    st.dataframe(df)

    # Maintenance pot: sum of all members' balances
    maintenance_pot = -overview["Total balance"].sum()
    st.subheader("🛠️ Maintenance Pot")
    st.info(f"Total maintenance pot: €{maintenance_pot:.2f}")

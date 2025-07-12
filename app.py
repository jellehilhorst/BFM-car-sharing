import streamlit as st
import pandas as pd
import datetime
import os

names = ["Anelle", "Carlo", "Amber", "Romain", "Tjark", "Other"]

# Load trip data
file_path = "trips.csv"
if os.path.exists(file_path):
    df = pd.read_csv(file_path)
else:
    df = pd.DataFrame(columns=[
        "Date", "Trip Date", "Name", "Driven km", "Refuel", "Member", 
        "KM Rate", "Extra Fee", "Total", "Note"
    ])

# Pricing (you can update these)
member_rate = 0.20
non_member_rate = 0.30
non_member_fee = 5.00

# UI
st.title("🚗 Car Sharing Log")

submitted = False

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

elif st.session_state.step == 2:
    with st.form("other_name_form"):
        name = st.text_input("Enter a different name")
        next_step = st.form_submit_button("Next")
        if next_step and name:
            st.session_state.name = name
            st.session_state.step = 3

elif st.session_state.step == 3:
    with st.form("trip_form"):
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
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(file_path, index=False)
    st.success(f"Trip saved! Total cost: €{total}")

if not df.empty:
    st.subheader("📋 Trip History")
    st.dataframe(df)

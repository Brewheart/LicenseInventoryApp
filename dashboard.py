import streamlit as st
import pandas as pd
import os

# 🧱 Make the layout wide
st.set_page_config(layout="wide")

st.title("📊 Microsoft 365 License Overview")

# 📂 Load all CSVs into one DataFrame
data_folder = "data"
csv_files = [f for f in os.listdir(data_folder) if f.endswith(".csv")]

if not csv_files:
    st.warning("No license files found in 'data/'")
else:
    # 🔁 Merge all CSVs with tenant tracking
    all_data = []
    for file in csv_files:
        df = pd.read_csv(os.path.join(data_folder, file))
        df["Tenant"] = os.path.splitext(file)[0]  # Strip ".csv" for clean name
        all_data.append(df)

    full_df = pd.concat(all_data, ignore_index=True)

    # 🧹 Drop TenantID column if it exists
    if "TenantId" in full_df.columns:
        full_df = full_df.drop(columns=["TenantId"])


    # 🔍 Search filter
    search = st.text_input("Search by user or display name")

    df = full_df.copy()


    if search:
        df = df[df.apply(
            lambda row: search.lower() in str(row["UserPrincipalName"]).lower()
            or search.lower() in str(row["DisplayName"]).lower(), axis=1)]

    # 🏢 Tenant filter
    tenants = sorted(df["Tenant"].unique())
    selected_tenants = st.multiselect("Filter by tenant:", tenants)

    if selected_tenants:
        df = df[df["Tenant"].isin(selected_tenants)]


    # 🧮 License type filter
    all_licenses = sorted(set(
        lic.strip()
        for sublist in df["Licenses"].dropna()
        for lic in str(sublist).split(", ")
    ))
    selected_licenses = st.multiselect("Filter by license type:", all_licenses)

    if selected_licenses:
        df = df[df["Licenses"].apply(
            lambda x: any(lic in str(x).split(", ") for lic in selected_licenses)
        )]

    # 🧼 Checkbox to hide users with no licenses
    hide_unlicensed = st.checkbox("Hide users with no licenses")

    if hide_unlicensed:
        df = df[df["Licenses"].notna() & (df["Licenses"].str.strip() != "")]

    # 🔢 Reset index to start at 1
    df.index = range(1, len(df) + 1)

    # 🔢 User count
    st.markdown(f"### 👥 Displaying **{len(df)}** users")

    # 📊 Show table
    st.dataframe(df, use_container_width=True)

    # 💾 Download
    csv = df.to_csv(index_label="No.").encode('utf-8')
    st.download_button("📥 Download CSV", data=csv, file_name="filtered_users.csv", mime="text/csv")

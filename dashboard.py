import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

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

    from collections import Counter
    license_list = []
    for lic_string in full_df["Licenses"].dropna():
        license_list.extend([lic.strip() for lic in str(lic_string).split(",")])
    license_counts = Counter(license_list)

    # Convert to DataFrame
    import pandas as pd
    df_licenses = pd.DataFrame.from_dict(license_counts, orient='index', columns=['Count'])
    df_licenses = df_licenses.sort_values('Count', ascending=False)

    # 🧠 Group licenses that are less than 3% of total into "Other"
    total = df_licenses["Count"].sum()
    df_licenses["Percent"] = df_licenses["Count"] / total
    df_major = df_licenses[df_licenses["Percent"] >= 0.03]  # Show 3%+ individually
    df_minor = df_licenses[df_licenses["Percent"] < 0.03]

    if not df_minor.empty:
        other_row = pd.DataFrame([{
            "Count": df_minor["Count"].sum(),
            "Percent": df_minor["Percent"].sum()
        }], index=["Other"])
        df_licenses_cleaned = pd.concat([df_major, other_row])
    else:
        df_licenses_cleaned = df_major

    # 🥧 Draw pie chart
    st.markdown("## 📊 License Usage Breakdown")

    def autopct_format(values):
        def format_func(pct):
            total = sum(values)
            count = int(round(pct * total / 100.0))
            return f"{pct:.1f}%\n({count})"
        return format_func

    fig, ax = plt.subplots()
    ax.pie(
        df_licenses_cleaned["Count"],
        labels=df_licenses_cleaned.index,
        autopct=autopct_format(df_licenses_cleaned["Count"]),
        startangle=90,
        textprops={'fontsize': 10}
    )
    ax.axis("equal")
    st.pyplot(fig)

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

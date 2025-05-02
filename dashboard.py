import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from collections import Counter
from parse_data import FRIENDLY_NAMES

# 🧱 Set layout wide
st.set_page_config(layout="wide")

st.title("📊 Microsoft 365 License Overview")

# 📂 Define data folders
data_folder = "data"
capacity_folder = "license_capacity"

# 📂 Load user CSVs
user_csv_files = [f for f in os.listdir(data_folder) if f.endswith(".csv")]
capacity_csv_files = [f for f in os.listdir(capacity_folder) if f.endswith(".csv")]

if not user_csv_files or not capacity_csv_files:
    st.warning("⚠️ No user or license capacity files found.")
    st.stop()

# 🔁 Merge all user CSVs
all_user_data = []
for file in user_csv_files:
    df = pd.read_csv(os.path.join(data_folder, file))
    df["Tenant"] = os.path.splitext(file)[0]
    all_user_data.append(df)

full_users_df = pd.concat(all_user_data, ignore_index=True)

# 🔁 Merge all capacity CSVs
all_capacity_data = []
for file in capacity_csv_files:
    df = pd.read_csv(os.path.join(capacity_folder, file))
    all_capacity_data.append(df)

full_capacity_df = pd.concat(all_capacity_data, ignore_index=True)

# 🧹 Apply Friendly Name Mapping to LicenseName column
full_capacity_df["LicenseName"] = full_capacity_df["LicenseName"].apply(
    lambda x: FRIENDLY_NAMES.get(x, x)
)

# 🎯 Tenant filter
tenant_options = sorted(full_users_df["Tenant"].unique())
selected_tenants = st.multiselect("Filter by Tenant:", tenant_options)

filtered_users_df = full_users_df.copy()
filtered_capacity_df = full_capacity_df.copy()

if selected_tenants:
    filtered_users_df = filtered_users_df[filtered_users_df["Tenant"].isin(selected_tenants)]
    filtered_capacity_df = filtered_capacity_df[filtered_capacity_df["Tenant"].isin(selected_tenants)]

# 📊 License Usage Overview Section
st.markdown("---")
st.header("📈 Global License Summary")

# 🔢 Summarize license usage
summary = filtered_capacity_df.groupby("LicenseName").agg(
    Assigned=("Assigned", "sum"),
    Available=("Available", "sum")
).reset_index()

# 🧹 Exclude unwanted licenses from summary
excluded_licenses = [
    "Microsoft Store Services",
    "Microsoft 365 Lighthouse Partner Plan",
    "Azure Rights Management"
]

summary = summary[~summary["LicenseName"].isin(excluded_licenses)]


# 🧮 Global metrics
total_assigned = summary["Assigned"].sum()
total_available = summary["Available"].sum()
overall_utilization = (total_assigned / total_available) * 100 if total_available else 0

# 🎯 Calculate individual Utilization % (now only real licenses exist)
summary["Utilization (%)"] = (summary["Assigned"] / summary["Available"]) * 100
summary = summary.fillna(0)

# 📈 Define Colored Progress Bar
def render_progress_bar(value):
    capped_value = min(value, 100)  # Never above 100% visually

    if value > 100:
        color = "red"
    elif value == 100:
        color = "green"
    else:
        color = "#3399FF"

    st.markdown(f"""
        <div style="max-width: 400px;">
            <div style="height: 24px; width: 100%; background-color: #e0e0e0; border-radius: 4px;">
                <div style="
                    height: 100%;
                    width: {capped_value}%;
                    background-color: {color};
                    border-radius: 4px;">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# 🎯 Split into two columns: Left (metrics), Right (pie chart)
left_col, right_col = st.columns(2)

with left_col:
    # 📋 Licenses Heading
    st.markdown(
        f"""
        <div style='text-align: left;'>
            <h3 style='margin-bottom: 10px;'>📋 Licenses</h3>
            <div style='font-size: 36px; font-weight: bold; margin-bottom: 30px;'>
                {total_assigned} / {total_available}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 📈 Utilization % and Progress Bar
    st.markdown(
        f"""
        <div style='font-size: 24px; font-weight: bold; margin-top: 10px; margin-bottom: 5px;'>
            Utilization: {overall_utilization:.1f}%
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_progress_bar(overall_utilization)

    # 🚨 Overdraft Section
    overdrafted_licenses = filtered_capacity_df[
        filtered_capacity_df["Assigned"] > filtered_capacity_df["Available"]
    ]

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    if not overdrafted_licenses.empty:
        st.markdown("### 🚨 Overdrafted Licenses")

        overdrafted_licenses["Overdraft"] = overdrafted_licenses["Assigned"] - overdrafted_licenses["Available"]

        overdraft_display = overdrafted_licenses[["Tenant", "LicenseName", "Overdraft", "Assigned", "Available"]]
        overdraft_display = overdraft_display.sort_values(by=["LicenseName", "Tenant"])

        st.dataframe(
            overdraft_display.style.format(na_rep="-"),
            use_container_width=True,
            hide_index=True
        )
    else:
        # ⬅️ Left-aligned, vertically centered
        st.markdown(
            """
            <div style="
                margin-top: 40px;
                width: 100%;
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                justify-content: center;
                height: 200px;
                background-color: #1E2B38;
                border-radius: 8px;
                padding: 1rem 2rem;
                color: white;
                box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.3);
            ">
                ✅ No overdrafted licenses found.
            </div>
            """,
            unsafe_allow_html=True
        )



with right_col:
    st.markdown("### 📈 License Assignment Distribution")

    license_list = []
    for lic_string in filtered_users_df["Licenses"].dropna():
        license_list.extend([lic.strip() for lic in str(lic_string).split(",")])

    license_counts = Counter(license_list)

    if license_counts:
        # 📊 Combine small licenses into 'Other'
        total = sum(license_counts.values())
        grouped_counts = {}
        other_count = 0

        for lic, count in license_counts.items():
            percentage = (count / total) * 100
            if percentage < 3:
                other_count += count
            else:
                grouped_counts[lic] = count

        if other_count > 0:
            grouped_counts["Other"] = other_count

        fig, ax = plt.subplots(figsize=(3.5, 3.5))  # Smaller Pie Chart!

        ax.pie(
            grouped_counts.values(),
            labels=grouped_counts.keys(),
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 7}
        )
        ax.axis("equal")
        st.pyplot(fig)

    else:
        st.info("No license assignment data available for pie chart.")

# 📋 License Breakdown Table
st.markdown("## 📋 License Breakdown Table")

# Apply styling to right-align numeric columns
styled_summary = summary.style.format({"Utilization (%)": "{:.1f}%"}).set_properties(
    subset=["Assigned", "Available", "Utilization (%)"],
    **{"text-align": "right"}
)

st.dataframe(
    styled_summary,
    use_container_width=True,
    hide_index=True
)

# 👤 User License Assignment Section
st.markdown("---")
st.header("🧑‍💻 User License Assignment Table")

# 🔎 Search box
search = st.text_input("Search by user or display name")

# 👥 Prepare df
df = filtered_users_df.copy()

# 🪪 Prepare license multiselect filter
# Step 1: Split Licenses into individual items
license_list = []
for lic_string in df["Licenses"].dropna():
    license_list.extend([lic.strip() for lic in str(lic_string).split(",")])

unique_licenses = sorted(set(license_list))

# Step 2: Show multiselect box
selected_licenses = st.multiselect("Filter by License(s):", options=unique_licenses)

# Step 3: Apply text search filter
if search:
    df = df[df.apply(
        lambda row: search.lower() in str(row["UserPrincipalName"]).lower()
        or search.lower() in str(row["DisplayName"]).lower(), axis=1
    )]

# Step 4: Apply license filter (match any)
if selected_licenses:
    df = df[df["Licenses"].apply(
        lambda x: any(lic in str(x) for lic in selected_licenses)
    )]

# 🏢 Apply tenant filter
if selected_tenants:
    df = df[df["Tenant"].isin(selected_tenants)]

# 🧼 Hide users with no licenses
hide_unlicensed = st.checkbox("Hide users with no licenses")
if hide_unlicensed:
    df = df[df["Licenses"].notna() & (df["Licenses"].str.strip() != "")]

# 🧹 Remove TenantId column if present
if "TenantId" in df.columns:
    df = df.drop(columns=["TenantId"])

# 🔢 Reset index for table
df.index = range(1, len(df) + 1)

# 📊 Show final user table
st.markdown(f"### 👥 Displaying **{len(df)}** users")
st.dataframe(df, use_container_width=True)


import os
import sys
import json
import pandas as pd
from graph_api import get_access_token, query_graph
from parse_data import build_license_lookup, map_users_to_licenses, save_to_csv, FRIENDLY_NAMES

# 📁 Handle relative paths for PyInstaller / normal runs
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# 📄 Load tenants.json from correct location
tenants_path = os.path.join(base_path, "tenants.json")
with open(tenants_path) as f:
    tenants = json.load(f)

# 🛠️ Ensure output folders exist
os.makedirs("data", exist_ok=True)
os.makedirs("license_capacity", exist_ok=True)

# 🔄 Process each tenant
for tenant in tenants:
    tenant_id = tenant["tenant_id"]
    tenant_name = tenant["tenant_name"]
    print(f"\n🔄 Fetching data for tenant: {tenant_name}")

    token = get_access_token(tenant_id)

    # Fetch user license assignments
    users_data = query_graph("users?$select=id,displayName,userPrincipalName,assignedLicenses", token)
    licenses_data = query_graph("subscribedSkus", token)

    # 💾 Save user license mapping
    license_lookup = build_license_lookup(licenses_data)
    users_with_licenses = map_users_to_licenses(users_data, license_lookup)
    filename = f"data/{tenant_name}.csv"
    save_to_csv(users_with_licenses, filename)

    # 💾 Save license capacity (assigned vs available)
    license_capacity_list = []
    for sku in licenses_data.get("value", []):
        raw_license_name = sku.get("skuPartNumber", "Unknown SKU")

        # 🔥 Skip unwanted licenses early using the raw name
        excluded_keywords = ["POWER", "FLOW", "FREE", "TRIAL", "WINDOWS_STORE"]
        if any(word in raw_license_name.upper() for word in excluded_keywords):
            continue

        # 🧹 Map to friendly name AFTER exclusion
        license_name = FRIENDLY_NAMES.get(raw_license_name, raw_license_name)

        license_capacity_list.append({
            "Tenant": tenant_name,
            "LicenseName": license_name,
            "Assigned": sku.get("consumedUnits", 0),
            "Available": sku.get("prepaidUnits", {}).get("enabled", 0)
        })


    if license_capacity_list:
        license_capacity_df = pd.DataFrame(license_capacity_list)
        capacity_filename = f"license_capacity/{tenant_name}_capacity.csv"
        license_capacity_df.to_csv(capacity_filename, index=False)
        print(f"✅ Exported license capacity for {tenant_name} to {capacity_filename}")
    else:
        print(f"⚠️ No license data found for tenant {tenant_name}")

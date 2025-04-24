import pandas as pd

# Create License Lookup Table
def build_license_lookup(subscribed_skus_data):
    sku_dict = {}
    for sku in subscribed_skus_data['value']:
        #print(f"{sku['skuId']} ➝ {sku['skuPartNumber']}")
        sku_id = sku.get("skuId")
        part_number = sku.get("skuPartNumber") or sku_id
        friendly = FRIENDLY_NAMES.get(part_number, FRIENDLY_NAMES.get(sku_id, part_number))
        sku_dict[sku_id] = friendly
        #print(f"🔍 Mapped {sku_id} ({part_number}) ➝ {friendly}")  # Add this
    return sku_dict


FRIENDLY_NAMES = {
    "ENTERPRISEPACK": "Microsoft 365 E3",
    "cbdc14ab-d96c-4c30-b9f4-6ada7cdc1d46": "Microsoft 365 Business Premium",
    "O365_BUSINESS_ESSENTIALS": "Microsoft 365 Business Basic",
    "Microsoft_365_Copilot": "Microsoft 365 Copilot",
    "POWER_BI_STANDARD": "Power BI (free)",
    "f245ecc8-75af-4f8e-b61f-27d8114de5f3": "Microsoft 365 Business Standard",
    "4b9405b0-7788-4568-add1-99614e613b69": "Exchange Online (Plan 1)",
    "FLOW_FREE": "Power Automate Free",
    "WACONEDRIVEENTERPRISE": "OneDrive for Business (Plan 2)",
    "19ec0d23-8335-4cbd-94ac-6050e30712fa": "Exchange Online (Plan 2)",
    "PROJECT_P1": "Project Plan 1",
    "05e9a617-0261-4cee-bb44-138d3ef5d965": "Microsoft 365 E3",
    "18181a46-0d4e-45cd-891e-60aabd171b4e": "Office 365 Enterprise E1",
    # Add more as needed — you'll see them in the exported CSV
}


# Match Users to Licenses
def map_users_to_licenses(users_data, license_lookup, tenant_id=None):
    user_list = []
    for user in users_data['value']:
        assigned = user.get('assignedLicenses', [])
        readable_licenses = [
            license_lookup.get(lic['skuId'], FRIENDLY_NAMES.get(lic['skuId'], lic['skuId']))
            for lic in assigned
        ]
        user_list.append({
            "TenantId": tenant_id,
            "UserPrincipalName": user.get("userPrincipalName", ""),
            "DisplayName": user.get("displayName", ""),
            "Licenses": ", ".join(readable_licenses)
        })
    return user_list




# Save as CSV
def save_to_csv(data, filename="data/users_with_licenses.csv"):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"✅ Exported {len(df)} users to {filename}")

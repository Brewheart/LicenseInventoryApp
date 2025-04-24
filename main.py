import json
from graph_api import get_access_token, query_graph
from parse_data import build_license_lookup, map_users_to_licenses, save_to_csv

# Load tenants
with open("tenants.json") as f:
    tenants = json.load(f)

for tenant in tenants:
    tenant_id = tenant["tenant_id"]
    tenant_name = tenant["tenant_name"]
    print(f"\n🔄 Fetching data for tenant: {tenant_name}")

    token = get_access_token(tenant_id)

    users_data = query_graph("users?$select=id,displayName,userPrincipalName,assignedLicenses", token)
    licenses_data = query_graph("subscribedSkus", token)

    license_lookup = build_license_lookup(licenses_data)
    users_with_licenses = map_users_to_licenses(users_data, license_lookup)

    filename = f"data/{tenant_name}.csv"
    save_to_csv(users_with_licenses, filename)

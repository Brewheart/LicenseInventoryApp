from dotenv import load_dotenv
import os
import msal
import requests

load_dotenv()

# TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


def get_access_token(tenant_id):
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scope = ["https://graph.microsoft.com/.default"]

    app = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=authority
    )

    token_response = app.acquire_token_for_client(scopes=scope)

    if "access_token" in token_response:
        return token_response["access_token"]
    else:
        raise Exception(f"Token request failed: {token_response}")

def query_graph(endpoint, token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = f"https://graph.microsoft.com/v1.0/{endpoint}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Graph API error {response.status_code}: {response.text}")

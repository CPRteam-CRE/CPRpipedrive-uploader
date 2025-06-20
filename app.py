
import streamlit as st
import requests
import pandas as pd
from PIL import Image
import pytesseract
from io import BytesIO

# === CONFIGURATION ===
API_TOKEN = "65789ea069112a92c574c5a475910792005a08de"
BASE_URL = "https://api.pipedrive.com/v1"

# === FUNCTIONS ===
def get_user_id():
    url = f"{BASE_URL}/users/me?api_token={API_TOKEN}"
    res = requests.get(url)
    res.raise_for_status()
    return res.json()["data"]["id"]

def create_organization(org, owner_id):
    payload = {
        "name": org["name"],
        "owner_id": owner_id,
        "visible_to": 3
    }
    if "address" in org:
        payload["address"] = org["address"]
    if "website" in org:
        payload["website"] = org["website"]

    url = f"{BASE_URL}/organizations?api_token={API_TOKEN}"
    res = requests.post(url, json=payload)
    res.raise_for_status()
    return res.json()["data"]["id"]

def create_person(person, org_id, owner_id):
    payload = {
        "name": person["name"],
        "email": person["email"],
        "phone": person["phone"],
        "org_id": org_id,
        "owner_id": owner_id,
        "visible_to": 3,
        "label": person.get("label", "Business Card Import")
    }
    url = f"{BASE_URL}/persons?api_token={API_TOKEN}"
    res = requests.post(url, json=payload)
    res.raise_for_status()
    return res.json()["data"]["id"]

def extract_text_from_image(image_data):
    image = Image.open(BytesIO(image_data))
    return pytesseract.image_to_string(image)

# === INTERFACE ===
st.title("📇 Pipedrive Contact Uploader with OCR")
st.markdown("Upload contact CSVs or business card images to auto-populate Pipedrive.")

st.header("Upload CSV of Contacts")
csv_file = st.file_uploader("Upload CSV", type=["csv"])

if csv_file:
    df = pd.read_csv(csv_file)
    st.write("CSV Preview:", df.head())

    if st.button("Upload CSV to Pipedrive"):
        user_id = get_user_id()
        for _, row in df.iterrows():
            org = {"name": row["org_name"], "address": row.get("org_address", ""), "website": row.get("org_website", "")}
            person = {"name": row["name"], "email": row["email"], "phone": row["phone"]}
            org_id = create_organization(org, user_id)
            create_person(person, org_id, user_id)
        st.success("CSV contacts uploaded to Pipedrive.")

st.header("Upload Scanned Business Cards")
images = st.file_uploader("Upload images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if images:
    extracted = []
    for img in images:
        text = extract_text_from_image(img.read())
        st.subheader(f"{img.name}")
        st.text(text)
        extracted.append({
            "name": "",
            "email": "",
            "phone": "",
            "org_name": "",
            "org_address": "",
            "org_website": "",
            "raw_text": text
        })

    df_edit = pd.DataFrame(extracted)
    edited_df = st.experimental_data_editor(df_edit, num_rows="dynamic")

    if st.button("Upload Card Data to Pipedrive"):
        user_id = get_user_id()
        for _, row in edited_df.iterrows():
            org = {"name": row["org_name"], "address": row.get("org_address", ""), "website": row.get("org_website", "")}
            person = {"name": row["name"], "email": row["email"], "phone": row["phone"]}
            org_id = create_organization(org, user_id)
            create_person(person, org_id, user_id)
        st.success("Business card data uploaded to Pipedrive.")

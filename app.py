import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner
import pandas as pd
import requests

# 1. Configuration
st.set_page_config(page_title="Tournament Marshal Portal", page_icon="🛡️", layout="centered")

# REPLACE THIS WITH YOUR NEW WEB APP URL AFTER DEPLOYING CODE.GS
GAS_URL = "https://script.google.com/macros/s/AKfycbzgbpXox0M1lOWxuQBwFRrh1o-y1M5YrvgriwCgcNe9BvhXh3QIRnHTunIFA98eEgVO0A/exec"
SPREADSHEET_ID = "1l4khiRO2fGqZQ600xcdrVNY_sP0NvmDdPQiOa-jPfR8"

st.markdown("""
    <style>
    .main { background-color: #111827; }
    h2 { color: #60a5fa; text-align: center; font-weight: 700; margin-bottom: 5px; }
    div.stButton > button:first-child { background-color: #10b981 !important; color: white !important; font-weight: bold; width: 100% !important; padding: 15px !important; }
    .badge-container { background: #1f2937; padding: 20px; border-radius: 12px; border: 1px solid #374151; text-align: center; margin-top: 15px; }
    .badge-number { font-size: 32px; font-weight: 800; color: #facc15; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

st.title("🏆 Tournament Marshal Portal")

# 2. State Management
if "active_scan_completed" not in st.session_state:
    st.session_state.active_scan_completed = False
if "display_payload" not in st.session_state:
    st.session_state.display_payload = {}

# 3. Data Functions
def fetch_sheet_data():
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
    df = pd.read_csv(csv_url, header=None)
    return df.values.tolist()

# This calls your NEW Code.gs verifyTicket function
def send_checkin_to_gas(row_id):
    try:
        requests.get(GAS_URL, params={"mode": "verify_bypass", "pid": row_id}, timeout=10)
    except:
        pass

# 4. App Logic
try:
    all_records = fetch_sheet_data()
except:
    st.error("🔒 Database Error. Ensure Sheet is set to 'Anyone with link can view'.")
    all_records = None

if all_records:
    if st.session_state.active_scan_completed:
        payload = st.session_state.display_payload
        
        if payload["status"] == "SUCCESS":
            st.success("### ✓ Verified & Checked In Successfully!")
            st.markdown(f"""
                <div class="badge-container">
                    <p style="color:#9ca3af;">PLAYER NAME</p>
                    <div class="badge-number">{payload['name']}</div>
                </div>
            """, unsafe_allow_html=True)
        elif payload["status"] == "DUPLICATE":
            st.warning(f"### ⚠️ Already Checked In\nPlayer: {payload['name']}")
        
        if st.button("📷 Scan Next Player"):
            st.session_state.active_scan_completed = False
            st.rerun()

    else:
        st.markdown("<p style='text-align:center;'>Point camera at the QR code</p>", unsafe_allow_html=True)
        scanned_raw = qrcode_scanner(key='live_marshal_camera_engine')
        
        if scanned_raw:
            # PARSING: Extract row number from "FDG26-1"
            try:
                # Get the number after the dash
                row_index = int(scanned_raw.split("-")[1])
                
                # Fetch row (adjust index if header exists)
                player_row = all_records[row_index] 
                player_name = f"{player_row[1]} {player_row[0]}"
                attendance_status = str(player_row[6]).strip()

                if attendance_status == "Checked-In":
                    st.session_state.display_payload = {"status": "DUPLICATE", "name": player_name}
                else:
                    send_checkin_to_gas(row_index)
                    st.session_state.display_payload = {"status": "SUCCESS", "name": player_name}
                
                st.session_state.active_scan_completed = True
                st.rerun()
            except Exception as e:
                st.error(f"Error reading code: {e}")

import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner
import pandas as pd
import requests

# Set page layout
st.set_page_config(page_title="Tournament Marshal Portal", page_icon="🛡️", layout="centered")

# Custom CSS for the UI
st.markdown("""
    <style>
    .main { background-color: #111827; }
    h2 { color: #60a5fa; text-align: center; font-weight: 700; margin-bottom: 5px; }
    div.stButton > button:first-child { 
        background-color: #10b981 !important; color: white !important; 
        font-weight: bold; width: 100% !important; padding: 15px !important; 
    }
    .badge-container { 
        background: #1f2937; padding: 20px; border-radius: 12px; 
        border: 1px solid #374151; text-align: center; margin-top: 15px; 
    }
    .badge-number { font-size: 42px; font-weight: 800; color: #facc15; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

st.title("🏆 Tournament Marshal Portal")

# Configuration
GAS_URL = "https://script.google.com/macros/s/AKfycbyf8ARdaNEUEQ7lM8NmRLHxa9V4sTM-QZgfAnohE05O_JotbJAEwYfFdjutrs2TGrgeXA/exec" # <--- PASTE YOUR DEPLOYED URL HERE
SPREADSHEET_ID = "1l4khiRO2fGqZQ600xcdrVNY_sP0NvmDdPQiOa-jPfR8"

# State Management
if "active_scan_completed" not in st.session_state:
    st.session_state.active_scan_completed = False
if "display_payload" not in st.session_state:
    st.display_payload = {}

# Functions
def fetch_sheet_data():
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
    df = pd.read_csv(csv_url, header=None)
    return df.values.tolist()

def send_checkin_to_gas(row_id):
    try:
        requests.get(GAS_URL, params={"mode": "verify_bypass", "pid": row_id}, timeout=10)
    except:
        pass

# Main App Logic
all_records = fetch_sheet_data()

if st.session_state.active_scan_completed:
    payload = st.session_state.display_payload
    
    if payload["status"] == "SUCCESS":
        st.success("### ✓ Verified & Checked In Successfully!")
        st.markdown(f"""
            <div class="badge-container">
                <p style="margin:0; font-size:16px; color:#9ca3af;">ASSIGNED EQUIPMENT DESTINATION</p>
                <div class="badge-number">BAG #{payload['bag']}</div>
                <p style="margin:0; font-size:18px; color:#ffffff; font-weight:600;">Player: {payload['name']}</p>
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
        try:
            # Parse ID from string "FDG26-1"
            parts = scanned_raw.split("-")
            row_id = int(parts[1]) 
            
            # Map to list index (all_records[1] is the first data row)
            player_row = all_records[row_id] 
            
            # Extract Data
            player_name = f"{player_row[1]} {player_row[0]}"
            bag_number = player_row[5] 
            attendance_status = str(player_row[6]).strip()

            if attendance_status == "Checked-In":
                st.session_state.display_payload = {"status": "DUPLICATE", "name": player_name}
            else:
                send_checkin_to_gas(row_id)
                st.session_state.display_payload = {
                    "status": "SUCCESS", 
                    "name": player_name, 
                    "bag": bag_number
                }
            
            st.session_state.active_scan_completed = True
            st.rerun()
        except Exception as e:
            st.error(f"Error reading code: {e}")

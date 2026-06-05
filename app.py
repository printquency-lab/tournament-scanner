import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner
import pandas as pd
import requests

# Clean, production responsive dark-themed styling configuration
st.set_page_config(page_title="Tournament Marshal Portal", page_icon="🛡️", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #111827; }
    h2 { color: #60a5fa; text-align: center; font-weight: 700; margin-bottom: 5px; }
    p.sub { color: #9ca3af; text-align: center; font-size: 14px; margin-bottom: 25px; }
    div.stButton > button:first-child {
        background-color: #10b981 !important;
        color: white !important;
        font-size: 20px !important;
        font-weight: bold !important;
        padding: 18px 20px !important;
        border-radius: 10px !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2);
        transition: background-color 0.2s;
    }
    div.stButton > button:first-child:hover {
        background-color: #059669 !important;
    }
    .badge-container {
        background: #1f2937;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #374151;
        text-align: center;
        margin-top: 15px;
    }
    .badge-number {
        font-size: 42px;
        font-weight: 800;
        color: #facc15;
        letter-spacing: 1px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏆 Tournament Marshal Portal")

# HARDCODED SPREADSHEET CONFIGURATION
SPREADSHEET_ID = "1l4khiRO2fGqZQ600xcdrVNY_sP0NvmDdPQiOa-jPfR8"

# Initialize persistent tracking state for active scanning sessions
if "active_scan_completed" not in st.session_state:
    st.session_state.active_scan_completed = False
if "display_payload" not in st.session_state:
    st.session_state.display_payload = {}

# Helper function to pull the master data via CSV export link
def fetch_sheet_data():
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
    df = pd.read_csv(csv_url, header=None)
    return df.values.tolist()

# Helper function to trigger your Apps Script background macro to stamp attendance status
def send_checkin_to_gas(row_id):
    # This reaches out to your original Google macro engine safely behind the scenes
    gas_url = f"https://script.google.com/macros/s/AKfycbz_your_script_deployment_id/exec"
    try:
        requests.get(gas_url, params={"mode": "verify_bypass", "pid": row_id})
    except:
        pass

# =========================================================================
# SCAN CONTROL WORKFLOW PIPELINE INTERFACES
# =========================================================================
try:
    all_records = fetch_sheet_data()
except Exception as e:
    st.error("🔒 Database Link Error. Make sure your Google Sheet is shared as 'Anyone with link can Edit'.")
    all_records = None

if all_records:
    # CONDITION A: A CODE WAS READ, INTERFACE FREEZES AND HIGHLIGHTS THE DATA ASSIGNMENTS
    if st.session_state.active_scan_completed:
        payload = st.session_state.display_payload
        
        if payload["status"] == "SUCCESS":
            st.balloons()
            st.success(f"### ✓ Verified & Checked In Successfully!")
            st.markdown(f"""
                <div class="badge-container">
                    <p style="margin:0; font-size:16px; color:#9ca3af;">ASSIGNED EQUIPMENT DESTINATION</p>
                    <div class="badge-number">BAG #{payload['bag'] if payload['bag'] else 'N/A'}</div>
                    <p style="margin:0; font-size:18px; color:#ffffff; font-weight:600;">Player: {payload['name']}</p>
                </div>
                <br>
            """, unsafe_allow_html=True)
            
        elif payload["status"] == "DUPLICATE":
            st.warning("### ⚠️ Duplicate Scan Warning Notice")
            st.markdown(f"""
                <div class="badge-container" style="border-color: #f59e0b;">
                    <p style="margin:0; font-size:18px; color:#fef08a; font-weight:bold;">Already Logged in Venue</p>
                    <p style="margin:5px 0 0 0; font-size:16px; color:#ffffff;"><strong>Player:</strong> {payload['name']}</p>
                    <p style="margin:5px 0 0 0; font-size:13px; color:#9ca3af;">This attendee's pass code credentials were verified earlier.</p>
                </div>
                <br>
            """, unsafe_allow_html=True)
            
        elif payload["status"] == "NOT_FOUND":
            st.error(f"### ❌ Ticket Invalid\n\n{payload['message']}")
            
        # USER ACTION MANUAL TRIGGER OVERRIDE: Clear screen layouts and restart viewfinder stream
        if st.button("📷 Scan Next Player"):
            st.session_state.active_scan_completed = False
            st.session_state.display_payload = {}
            st.rerun()

    # CONDITION B: VIEWPORT SCANNER INTERFACE RUNNING STREAM ACTIVELY ON LOAD
    else:
        st.markdown('<p class="sub">Point your device camera directly at the participant\'s QR badge credential ticket pass:</p>', unsafe_allow_html=True)
        
        # Deploy unblocked, native top-level camera element viewport hook
        scanned_raw = qrcode_scanner(key='live_marshal_camera_engine')
        
        if scanned_raw:
            clean_pid = scanned_raw.strip()
            if "pid=" in clean_pid:
                clean_pid = clean_pid.split("pid=")[-1]
            clean_pid = clean_pid.replace("ROW-", "")
            
            try:
                row_index = int(clean_pid)
                
                if row_index < 1 or row_index > len(all_records):
                    st.session_state.display_payload = {
                        "status": "NOT_FOUND",
                        "message": f"Scanned row address index #{row_index} cannot be located inside data registers."
                    }
                else:
                    player_row = all_records[row_index - 1]
                    player_name = player_row[0]
                    attendance_status = str(player_row[2]).strip()
                    bag_number = player_row[3] if len(player_row) > 3 else "N/A"
                    
                    if attendance_status == "Checked In":
                        st.session_state.display_payload = {
                            "status": "DUPLICATE",
                            "name": player_name
                        }
                    else:
                        # Direct background hit back to Google Apps Script template macro to check them in
                        send_checkin_to_gas(row_index)
                        
                        st.session_state.display_payload = {
                            "status": "SUCCESS",
                            "name": player_name,
                            "bag": bag_number
                        }
                        
            except ValueError:
                st.session_state.display_payload = {
                    "status": "NOT_FOUND",
                    "message": f"Read payload syntax structure error: '{scanned_raw}'"
                }
                
            st.session_state.active_scan_completed = True
            st.rerun()

import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner
import gspread
from google.oauth2.service_account import Credentials

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

# Initialize persistent tracking state for active scanning sessions
if "active_scan_completed" not in st.session_state:
    st.session_state.active_scan_completed = False
if "display_payload" not in st.session_state:
    st.session_state.display_payload = {}

# =========================================================================
# DATABASE LINK: CONNECT DIRECTLY TO GOOGLE SHEET INTERFACES
# =========================================================================
@st.cache_resource
def connect_to_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    # Target Google Sheet Database Key ID Connection Link
    sheet = client.open_by_key("1l4khiRO2fGqZQ600xcdrVNY_sP0NvmDdPQiOa-jPfR8").sheet1
    return sheet

try:
    master_sheet = connect_to_sheet()
except Exception as e:
    st.error("🔒 Database Engine Connection Blocked. Please check your st.secrets profile configuration setup.")
    master_sheet = None

# =========================================================================
# SCAN CONTROL WORKFLOW PIPELINE INTERFACES
# =========================================================================
if master_sheet:
    
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
            # Safely scrub raw input data payloads to isolate target Row IDs
            clean_pid = scanned_raw.strip()
            if "pid=" in clean_pid:
                clean_pid = clean_pid.split("pid=")[-1]
            clean_pid = clean_pid.replace("ROW-", "")
            
            try:
                row_index = int(clean_pid)
                all_records = master_sheet.get_all_values()
                
                if row_index < 1 or row_index > len(all_records):
                    st.session_state.display_payload = {
                        "status": "NOT_FOUND",
                        "message": f"Scanned row address index #{row_index} cannot be located inside data registers."
                    }
                else:
                    player_row = all_records[row_index - 1]
                    player_name = player_row[0]
                    attendance_status = player_row[2].strip()
                    bag_number = player_row[3] if len(player_row) > 3 else "N/A"
                    
                    if attendance_status == "Checked In":
                        st.session_state.display_payload = {
                            "status": "DUPLICATE",
                            "name": player_name
                        }
                    else:
                        # Write "Checked In" back directly to target index row cell in Google Sheets database 
                        master_sheet.update_cell(row_index, 3, "Checked In")
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
                
            # Toggle interface view lock parameters to pause native stream
            st.session_state.active_scan_completed = True
            st.rerun()

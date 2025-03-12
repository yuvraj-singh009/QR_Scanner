import streamlit as st
import pandas as pd
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

# Load attendance data
@st.cache(allow_output_mutation=True)
def load_data():
    df = pd.read_csv('Kavyamanch 2024 – Hindi Club (Responses) - Form Responses 1.csv')
    if 'ATTENDANCE' not in df.columns:
        df['ATTENDANCE'] = False
    return df

df = load_data()

# Function to mark attendance
def mark_attendance(reg_number):
    mask = df['Reg. No.'] == reg_number
    if not mask.any():
        return False, "Registration number not found."

    if df.loc[mask, 'ATTENDANCE'].iloc[0]:
        return False, f"Attendance already marked for {df.loc[mask, 'Name'].iloc[0]}"

    df.loc[mask, 'ATTENDANCE'] = True
    df.to_csv('Kavyamanch 2024 – Hindi Club (Responses) - Form Responses 1.csv', index=False)
    return True, f"Welcome {df.loc[mask, 'Name'].iloc[0]}! Attendance marked."

# WebRTC-based QR Scanner
class QRProcessor(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        qr_codes = decode(img)
        for qr in qr_codes:
            qr_data = qr.data.decode('utf-8')
            st.session_state.qr_code = qr_data
            pts = np.array(qr.polygon, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(img, [pts], True, (0, 255, 0), 3)
        return frame

def scan_qr_from_camera():
    st.write("📷 **Scanning... Please show a QR code to the camera**")
    webrtc_streamer(key="qr-scanner", video_processor_factory=QRProcessor)
    return st.session_state.get("qr_code", None)

def main():
    st.title("Kavyamanch Attendance Scanner")
    qr_data = scan_qr_from_camera()
    
    if qr_data:
        success, message = mark_attendance(qr_data)
        if success:
            st.success(message)
            st.balloons()
        else:
            st.error(message)

    # Show attendance statistics
    if st.checkbox("Show Attendance Statistics"):
        total = len(df)
        present = int(df['ATTENDANCE'].sum())
        absent = total - present
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Participants", total)
        col2.metric("Present", present)
        col3.metric("Absent", absent)

        if st.checkbox("Show Detailed List"):
            attendance_df = df[['Name', 'Reg. No.', 'ATTENDANCE']].copy()
            attendance_df['ATTENDANCE'] = attendance_df['ATTENDANCE'].map({True: 'Present', False: 'Absent'})
            st.dataframe(attendance_df)

if __name__ == "__main__":
    main()

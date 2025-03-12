import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import cv2
import numpy as np
from pyzbar.pyzbar import decode

# Set page config
st.set_page_config(
    page_title="Kavyamanch QR Scanner",
    page_icon="📷",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('attendance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load CSV file and keep in memory
@st.cache(allow_output_mutation=True)
def load_data():
    df = pd.read_csv('Kavyamanch 2024 – Hindi Club (Responses) - Form Responses 1.csv')
    if 'ATTENDANCE' not in df.columns:
        df['ATTENDANCE'] = False
    return df

df = load_data()

def mark_attendance(reg_number):
    """Mark attendance for a given registration number."""
    try:
        mask = df['Reg. No.'] == reg_number
        if not mask.any():
            return False, "Registration number not found."
        
        if df.loc[mask, 'ATTENDANCE'].iloc[0] == True:
            return False, f"Attendance already marked for {df.loc[mask, 'Name'].iloc[0]}"
        
        df.loc[mask, 'ATTENDANCE'] = True
        df.to_csv('Kavyamanch 2024 – Hindi Club (Responses) - Form Responses 1.csv', index=False)
        return True, f"Welcome {df.loc[mask, 'Name'].iloc[0]}! Attendance marked."
    except Exception as e:
        logger.error(f"Error marking attendance: {str(e)}")
        return False, "Error marking attendance."

def scan_qr_from_camera():
    """Continuously scans QR codes from the camera."""
    cap = cv2.VideoCapture(0)
    st_frame = st.empty()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        st_frame.image(frame, channels="BGR", use_container_width=True)
        qr_codes = decode(frame)
        
        if qr_codes:
            qr_data = qr_codes[0].data.decode('utf-8')
            cap.release()
            cv2.destroyAllWindows()
            return qr_data
    
    cap.release()
    cv2.destroyAllWindows()
    return None

def main():
    st.title("Kavyamanch Attendance Scanner")
    
    if st.button("Start Scanning"):
        qr_data = scan_qr_from_camera()
        if qr_data:
            success, message = mark_attendance(qr_data)
            if success:
                st.success(message)
                st.balloons()
            else:
                st.error(message)
        else:
            st.error("No QR code detected.")

    # Attendance statistics
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

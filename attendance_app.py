import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import av
import numpy as np
from pyzbar.pyzbar import decode
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase

# Set page config (MUST BE FIRST STREAMLIT COMMAND)
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

# Initialize session state
if 'last_scan' not in st.session_state:
    st.session_state.last_scan = None
if 'scan_count' not in st.session_state:
    st.session_state.scan_count = 0

# Load the CSV file once and keep it in memory
@st.cache
def load_data():
    df = pd.read_csv('Kavyamanch 2024 – Hindi Club (Responses) - Form Responses 1.csv')
    if 'ATTENDANCE' not in df.columns:
        df['ATTENDANCE'] = False
    return df

df = load_data()

def mark_attendance(reg_number):
    """Mark attendance for a given registration number in the CSV file."""
    try:
        # Check if registration number exists
        mask = df['Reg. No.'] == reg_number
        if not mask.any():
            return False, "Registration number not found in the database"
        
        # Check if attendance is already marked
        if df.loc[mask, 'ATTENDANCE'].iloc[0] == True:
            student_name = df.loc[mask, 'Name'].iloc[0]
            return False, f"Attendance already marked for {student_name}"
        
        # Mark attendance as True (explicitly boolean)
        df.loc[mask, 'ATTENDANCE'] = True
        
        # Save the updated CSV
        df.to_csv('Kavyamanch 2024 – Hindi Club (Responses) - Form Responses 1.csv', index=False)
        
        # Get student name
        student_name = df.loc[mask, 'Name'].iloc[0]
        
        return True, f"Welcome {student_name}! Attendance marked successfully."
        
    except Exception as e:
        logger.error(f"Error marking attendance: {str(e)}")
        return False, f"Error marking attendance: {str(e)}"

class QRCodeProcessor(VideoProcessorBase):
    """Custom video processor to detect QR codes in the video stream."""
    def __init__(self):
        self.qr_data = None

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # Convert the frame to a numpy array
        img = frame.to_ndarray(format="bgr24")
        
        # Decode QR codes
        qr_codes = decode(img)
        
        if qr_codes:
            self.qr_data = qr_codes[0].data.decode('utf-8')
            st.success(f"QR Code detected: {self.qr_data}")
            mark_attendance(self.qr_data)
        
        return frame

def main():
    # Add Hindi Club logo
    try:
        st.image("hindi.jpg", width=200)
    except:
        pass

    st.title("Kavyamanch Attendance Scanner")
    
    # Add statistics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Scans", st.session_state.scan_count)
    with col2:
        if st.session_state.last_scan:
            st.metric("Last Scan", st.session_state.last_scan)

    st.markdown("""
    ### 📱 Scan QR Code
    Point your camera at the QR code to mark attendance.
    """)
    
    # WebRTC streamer for camera access
    webrtc_ctx = webrtc_streamer(
        key="qr-scanner",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=QRCodeProcessor,
        async_processing=True,
    )

    if webrtc_ctx.video_processor:
        if webrtc_ctx.video_processor.qr_data:
            qr_data = webrtc_ctx.video_processor.qr_data
            success, message = mark_attendance(qr_data)
            if success:
                st.success(message)
                st.session_state.scan_count += 1
                st.session_state.last_scan = datetime.now().strftime("%H:%M:%S")
                st.balloons()
            else:
                st.error(message)

    # Show attendance statistics
    if st.checkbox("Show Attendance Statistics"):
        try:
            total = len(df)
            present = int(df['ATTENDANCE'].sum())
            absent = total - present
            
            st.write("### Attendance Summary")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Participants", total)
            col2.metric("Present", present)
            col3.metric("Absent", absent)
            
            # Show detailed attendance list
            if st.checkbox("Show Detailed List"):
                st.write("### Attendance List")
                attendance_df = df[['Name', 'Reg. No.', 'ATTENDANCE']].copy()
                attendance_df['ATTENDANCE'] = attendance_df['ATTENDANCE'].map({True: 'Present', False: 'Absent'})
                st.dataframe(attendance_df)
                
        except Exception as e:
            logger.error(f"Error loading attendance data: {str(e)}")
            st.error(f"Error loading attendance data: {str(e)}")

if __name__ == "__main__":
    main()

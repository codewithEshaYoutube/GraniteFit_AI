import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
import cv2
import mediapipe as mp

# ✅ Set up the dashboard
st.set_page_config(page_title="Employee Health Dashboard", layout="wide")
st.title("📊 Employee Health & Workload Dashboard")

# ✅ Generate Fake Data for One Employee
employee_data = {
    "Name": "Ashar Khan",
    "Role": "Software Engineer",
    "Age": 30,
    "Workload Level": np.random.choice(["Easy", "Medium", "Difficult"]),
    "Task Completion (%)": np.random.randint(50, 100),
    "Stress Level (%)": np.random.randint(20, 80),
    "Screen Time (Hours)": np.random.randint(4, 12),
    "Health Score (%)": np.random.randint(60, 100)
}

# ✅ Layout for better UI
col1, col2 = st.columns([1, 2])

with col1:
    # ✅ Employee Profile
    st.subheader("👤 Employee Profile")
    st.image("https://via.placeholder.com/150", width=150)
    st.write(f"**Name:** {employee_data['Name']}")
    st.write(f"**Role:** {employee_data['Role']}")
    st.write(f"**Age:** {employee_data['Age']}")
    st.write(f"**Workload Level:** {employee_data['Workload Level']}")
    
with col2:
    # ✅ Workload Level Pie Chart
    st.subheader("📌 Workload Level")
    workload_counts = {"Easy": 30, "Medium": 40, "Difficult": 30}
    fig, ax = plt.subplots()
    ax.pie(workload_counts.values(), labels=workload_counts.keys(), autopct='%1.1f%%', startangle=90, colors=["#66B2FF", "#FFCC99", "#FF6666"])
    ax.axis("equal")
    st.pyplot(fig)
    
    # ✅ Task Completion Bar Chart
    st.subheader("✅ Task Completion Progress")
    st.progress(employee_data["Task Completion (%)"] / 100)
    st.write(f"Current Task Completion: {employee_data['Task Completion (%)']}%")

# ✅ Stress Level and Screen Time
col3, col4 = st.columns(2)

with col3:
    st.subheader("⚠ Stress Level")
    st.metric(label="Stress Level (%)", value=employee_data["Stress Level (%)"])

with col4:
    st.subheader("🖥 Screen Time Monitoring")
    st.bar_chart([employee_data["Screen Time (Hours)"]])
    st.write(f"Current Screen Time: {employee_data['Screen Time (Hours)']} hours")

# ✅ Health Score Display
st.subheader("💚 Overall Health Score")
st.metric(label="Health Score (%)", value=employee_data["Health Score (%)"])

# ✅ Reminder Section (Non-blocking)
def show_reminder():
    st.toast("⏰ Time for a break! Take water, do eye exercises, and stretch!")

if st.button("Start Reminders"):
    show_reminder()
    st.write("🔔 Reminders activated! They will pop up periodically.")

# ✅ Interactive Cat Game
st.subheader("😺 Smiley Cat Game")
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

def face_detection_game():
    cap = cv2.VideoCapture(0)
    face_detector = mp_face_detection.FaceDetection()
    st.write("🎮 Game Started: Move your face to jump over hurdles!")
    stframe = st.empty()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert frame to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detector.process(frame_rgb)
        
        if results.detections:
            for detection in results.detections:
                mp_drawing.draw_detection(frame, detection)
                stframe.image(frame, channels="RGB")
                st.write("😺 Jump!")  # Logic for jumping cat (to be implemented with animation)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    st.write("🎮 Game Over")

if st.button("Start Game"):
    face_detection_game()

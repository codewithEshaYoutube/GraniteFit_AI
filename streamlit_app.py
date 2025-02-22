import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime

# Load dummy dataset
data = {
    "Employee ID": [101, 102, 103, 104, 105],
    "Name": ["Alice", "Bob", "Charlie", "David", "Emma"],
    "Work Hours": [8, 7, 9, 6, 10],
    "Breaks Taken": [2, 3, 1, 4, 2],
    "Screen Time (hrs)": [6, 5, 7, 4, 8],
    "Tasks Completed": [5, 6, 4, 7, 3],
    "Stress Level": ["Low", "Medium", "High", "Low", "High"]
}
df = pd.DataFrame(data)

# App title
st.title("GraniteFit AI 🏋️‍♂️🤖 - Employee Health & Wellness Dashboard")

# Sidebar Navigation
st.sidebar.header("Navigation")
option = st.sidebar.radio("Go to", ["Home", "Employee Dashboard", "Break Reminders", "Screen Time Tracker", "Task Prioritization", "Mental Wellness Bot"])

# Employee Dashboard
if option == "Employee Dashboard":
    st.header("📊 Employee Health Dashboard")
    selected_employee = st.selectbox("Select an Employee", df["Name"].unique())
    emp_data = df[df["Name"] == selected_employee]
    
    st.write(emp_data)
    
    fig, ax = plt.subplots()
    ax.bar(emp_data.columns[2:6], emp_data.iloc[0, 2:6])
    plt.xticks(rotation=45)
    st.pyplot(fig)

# 1️⃣ Break Reminders
elif option == "Break Reminders":
    st.header("⏰ Sitting Too Long? Get a Reminder!")
    duration = st.number_input("Set work duration before a reminder (minutes)", min_value=10, max_value=120, value=60)
    if st.button("Start Timer"):
        st.success(f"Reminder set! You will be notified every {duration} minutes.")
        time.sleep(duration * 60)
        st.warning("Time to stand up, stretch, or drink some water! 💦")

# 2️⃣ Screen Time Tracker
elif option == "Screen Time Tracker":
    st.header("👀 Screen Brightness & Time Tracker")
    screen_time = st.number_input("Enter your daily screen time (hours)", min_value=1, max_value=16, value=6)
    if screen_time > 8:
        st.warning("⚠️ High screen time detected! Consider reducing screen exposure.")
    st.success("Try the 20-20-20 rule: Every 20 minutes, look at something 20 feet away for 20 seconds.")

# 3️⃣ AI Task Prioritization
elif option == "Task Prioritization":
    st.header("⚖️ Work-Life Balance - AI Task Manager")
    tasks = st.text_area("Enter your tasks (one per line)")
    if st.button("Prioritize Tasks"):
        task_list = tasks.split("\n")
        sorted_tasks = sorted(task_list, key=len)
        st.success("Here’s your optimized task order:")
        for i, task in enumerate(sorted_tasks, 1):
            st.write(f"{i}. {task}")

# 4️⃣ Mental Wellness Chatbot
elif option == "Mental Wellness Bot":
    st.header("🧘 AI-Powered Mental Wellness Bot")
    st.write("Chat with AI for stress-relief recommendations!")
    user_input = st.text_input("How are you feeling today?")
    if st.button("Get Recommendation"):
        responses = [
            "Try deep breathing exercises for relaxation.",
            "Take a 5-minute break and listen to calming music.",
            "Go for a short walk to clear your mind.",
            "Practice gratitude journaling to boost your mood.",
        ]
        st.success(f"💡 Suggestion: {responses[datetime.now().second % len(responses)]}")

st.sidebar.info("This app is open-source. Contribute on [GitHub](https://github.com/codewithEshaYoutube/GraniteFit-AI)!")

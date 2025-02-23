import os
import requests
import logging
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class IBMAPIClient:
    """Handles authentication and communication with IBM Watson API."""

    def __init__(self):
        self.api_key = os.getenv("IBM_API_KEY")
        self.project_id = os.getenv("IBM_PROJECT_ID")
        self.token_url = os.getenv("IBM_URL_TOKEN")
        self.chat_url = os.getenv("IBM_URL_CHAT")
        self.access_token = None

        if not self.api_key or not self.project_id:
            raise ValueError("Missing IBM credentials. Ensure .env file is correctly set.")

        # Fetch an access token upon initialization
        self.get_token()

    def get_token(self):
        """Fetches and stores the IBM API access token."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": self.api_key}
        
        response = requests.post(self.token_url, headers=headers, data=data)

        if response.status_code == 200:
            self.access_token = response.json().get("access_token", "")
            logging.info("Successfully obtained IBM access token.")
        else:
            logging.error(f"Failed to get token: {response.text}")
            raise Exception(f"Token retrieval failed: {response.text}")

    def send_chat_request(self, messages):
        """Sends a request to IBM Watson's chat API."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        body = {
            "model_id": "ibm/granite-3-8b-instruct",
            "project_id": self.project_id,
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.7,
            "time_limit": 5000,
        }

        response = requests.post(self.chat_url, headers=headers, json=body)

        if response.status_code != 200:
            logging.error(f"Chat API error: {response.text}")
            raise Exception(f"Chat API request failed: {response.text}")

        return response.json()["choices"][0]["message"]["content"]

# Streamlit UI
st.title("Tech Employee Health AI Assistant")
st.write("Get health and wellness advice tailored for tech employees!")

# Initialize session state for chat messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are an AI health assistant specialized in providing health and wellness advice specifically for employees in the tech industry. Focus on ergonomics, mental well-being, posture, screen time management, and healthy work habits."}
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Ask me anything about workplace health...")

if user_input:
    # Display user message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get response from IBM
    with st.spinner("Thinking..."):
        try:
            ibm_client = IBMAPIClient()
            assistant_reply = ibm_client.send_chat_request(st.session_state.messages)
        except Exception as e:
            assistant_reply = f"Error: {str(e)}"
    
    # Display assistant response
    st.chat_message("assistant").markdown(assistant_reply)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

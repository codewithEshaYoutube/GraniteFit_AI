import os
import requests
import logging
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


class HealthRecommendationAgent:
    """An AI agent that provides health and wellness recommendations."""

    def __init__(self, api_client):
        self.api_client = api_client

    def generate_health_recommendation(self):
        """Generates a health-related recommendation based on user input."""
        messages = [
            {"role": "system", "content": "You are a health and wellness expert. Provide a short, practical health tip."},
            {"role": "user", "content": "Suggest a quick exercise for someone working at a desk all day."}
        ]

        return self.api_client.send_chat_request(messages)


if __name__ == "__main__":
    try:
        # Initialize the API client
        ibm_client = IBMAPIClient()
        
        # Create a health recommendation agent
        health_agent = HealthRecommendationAgent(ibm_client)
        
        # Get a health tip
        recommendation = health_agent.generate_health_recommendation()
        
        print("\nHealth Recommendation:\n", recommendation)

    except Exception as e:
        logging.error(f"Error occurred: {e}")

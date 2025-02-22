import os
import requests
import streamlit as st

# Get API key from https://cloud.ibm.com/iam/apikeys
IBM_API_KEY = 'hk1pI-U1QEFcfzYCUPr0NBQc2NZ8mlb_8U85sbLIbrMB'

# Get Project ID from https://dataplatform.cloud.ibm.com/projects/?context=wx   (it is in your project url)
IBM_PROJECT_ID = "3dc2e3bb-0d91-4d9f-8083-eeb91ea52f94"

IBM_URL_TOKEN = "https://iam.cloud.ibm.com/identity/token"
IBM_URL_CHAT = "https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-10-25"

##############################################
##
##   IBM API
##
##############################################
def IBM_token():
    # Define the headers
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Define the data payload
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": IBM_API_KEY
    }
    
    # Make the POST request
    response = requests.post(IBM_URL_TOKEN, headers=headers, data=data)
    st.session_state.IBM_ACCESS_TOKEN = response.json().get("access_token", "")


def IBM_chat (messages):
    body = {
        "model_id": "ibm/granite-3-8b-instruct",
        "project_id": IBM_PROJECT_ID,
        "messages": messages,
        "max_tokens": 2000,
        "temperature": 0.7,
        "time_limit": 5000
    }
    headers = {
    	"Accept": "application/json",
    	"Content-Type": "application/json",
    	"Authorization": "Bearer " + st.session_state.IBM_ACCESS_TOKEN
    }    
    response = requests.post(
    	IBM_URL_CHAT,
    	headers=headers,
    	json=body
    )
    
    if response.status_code != 200:
    	raise Exception("Non-200 response: " + str(response.text))
    
    response = response.json()
    return response["choices"][0]["message"]["content"]


#################################
##
##   Streamlit App UI
##
#################################

# Initialize
if "messages" not in st.session_state:
    st.session_state.messages = []
IBM_token();

# UI
st.title("💬 Simple IBM AI Chatbot")
st.write("Ask me anything!")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Type your message...")

if user_input:
    # Display user message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get response from IBM
    with st.spinner("Thinking..."):
        assistant_reply = IBM_chat(st.session_state.messages)
    
    # Display assistant message
    st.chat_message("assistant").markdown(assistant_reply)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
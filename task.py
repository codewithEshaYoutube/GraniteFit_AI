#!/usr/bin/env python3
import os
import requests
import numpy as np
from typing import List, Dict, Tuple, Union
from pathlib import Path
import PyPDF2
import logging
from dotenv import load_dotenv

IBM_ACCESS_TOKEN = ""  # Global variable to store the Chat API token

def IBM_token():
    """Obtain the IBM access token for the Chat API."""
    global IBM_ACCESS_TOKEN
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": IBM_API_KEY
    }
    response = requests.post(IBM_URL_TOKEN, headers=headers, data=data)
    if response.status_code == 200:
        IBM_ACCESS_TOKEN = response.json().get("access_token", "")
    else:
        raise Exception(f"Failed to get token: {response.text}")

def IBM_chat(messages):
    """
    Call the IBM Chat API with the given messages using the provided configuration.
    """
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
        "Authorization": f"Bearer {IBM_ACCESS_TOKEN}"
    }
    
    response = requests.post(IBM_URL_CHAT, headers=headers, json=body)
    
    if response.status_code != 200:
        raise Exception(f"Non-200 response: {response.text}")
    else:
        response = response.json()
        return response["choices"][0]["message"]["content"]

# ---------------- Load Environment Variables for Embedding API ----------------
load_dotenv()

# ---------------- Logging Configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------- IBM Embedding API Configuration ----------------
class IBMAPIConfig:
    """IBM API Configuration and Authentication for embeddings."""
    def __init__(self):
        self.api_key = os.getenv('IBM_API_KEY')  # For embeddings, these should be in your .env file
        self.project_id = os.getenv('IBM_PROJECT_ID')
        self.url_token = os.getenv('IBM_URL_TOKEN', 'https://iam.cloud.ibm.com/identity/token')
        self.url_embeddings = os.getenv('IBM_URL_EMBEDDINGS', 
            'https://us-south.ml.cloud.ibm.com/ml/v1/text/embeddings?version=2023-10-25')
        self.access_token = None
        
        if not all([self.api_key, self.project_id]):
            raise ValueError("Missing required environment variables for embeddings. Please check your .env file.")

    def get_token(self) -> str:
        """Get IBM API token for embeddings with error handling."""
        try:
            response = requests.post(
                self.url_token,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": self.api_key
                },
                timeout=10
            )
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
            return self.access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get IBM token: {str(e)}")
            raise

# ---------------- PDF Reading Utility ----------------
class PDFReader:
    """Handle PDF file reading and text extraction."""
    @staticmethod
    def read_pdf(file_path: Union[str, Path]) -> str:
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = []
                for page in reader.pages:
                    text.append(page.extract_text())
                return '\n'.join(text)
        except Exception as e:
            logger.error(f"Error reading PDF file {file_path}: {str(e)}")
            raise

# ---------------- Task Matching Functionality ----------------
class TaskMatcher:
    """Main class for task matching functionality."""
    def __init__(self):
        self.ibm_config = IBMAPIConfig()
        
    def get_embedding(self, text: str) -> List[float]:
        """Generate embeddings using IBM Granite model with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} to get embedding")
                if not self.ibm_config.access_token:
                    logger.info("Getting new IBM token for embeddings...")
                    self.ibm_config.get_token()
                    
                logger.info("Making API request for embedding...")
                response = requests.post(
                    self.ibm_config.url_embeddings,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.ibm_config.access_token}"
                    },
                    json={
                        "model_id": "ibm/granite-embedding-107m-multilingual",
                        "project_id": self.ibm_config.project_id,
                        "inputs": [text]
                    },
                    timeout=15
                )
                
                if response.status_code != 200:
                    logger.error(f"API returned status code {response.status_code}")
                    logger.error(f"API response: {response.text}")
                    raise Exception(f"API error: {response.text}")
                    
                return response.json()["results"][0]["embedding"]
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                self.ibm_config.access_token = None  # Reset token for retry
                continue

    def extract_tasks(self, text: str) -> List[str]:
        """Extract tasks from text using bullet indicators and keywords."""
        tasks = []
        lines = text.split('\n')
        task_indicators = [
            '- ', '• ', '* ', '→ ', '» ',
        ] + [f"{i}." for i in range(1, 10)] + [f"{i})" for i in range(1, 10)]
        task_keywords = [
            'task:', 'implement', 'develop', 'create', 'build', 'design',
            'configure', 'setup', 'integrate', 'optimize', 'test'
        ]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            indicator_found = False
            for indicator in task_indicators:
                if line.startswith(indicator):
                    tasks.append(line[len(indicator):].strip())
                    indicator_found = True
                    break
            if indicator_found:
                continue
            if any(keyword in line.lower() for keyword in task_keywords):
                tasks.append(line)
        return tasks

    def parse_team_skills(self, text: str) -> Dict[str, str]:
        """Parse team skills from text."""
        teams = {}
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            if ':' in line or '-' in line:
                parts = line.replace('-', ':').split(':', 1)
                if len(parts) == 2:
                    team_name, skills = parts
                    teams[team_name.strip()] = skills.strip()
            elif not teams and line:
                teams["General Team"] = line
        return teams

    def match_tasks_to_teams(
        self,
        project_input: Union[str, Path],
        team_input: Union[str, Path],
        similarity_threshold: float = 0.7
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Match tasks to teams by computing cosine similarities between task and team embeddings.
        """
        try:
            logger.info("Processing inputs...")
            project_text = (PDFReader.read_pdf(project_input) 
                            if isinstance(project_input, (str, Path)) and str(project_input).lower().endswith('.pdf')
                            else project_input)
            team_text = (PDFReader.read_pdf(team_input)
                         if isinstance(team_input, (str, Path)) and str(team_input).lower().endswith('.pdf')
                         else team_input)
        
            tasks = self.extract_tasks(project_text)
            teams = self.parse_team_skills(team_text)
        
            if not tasks:
                logger.error("No tasks found in the project description")
                return {}
            if not teams:
                logger.error("No team information found")
                return {}
        
            logger.info("Generating embeddings for tasks...")
            task_embeddings = {}
            for task in tasks:
                logger.info(f"Getting embedding for task: {task}")
                task_embeddings[task] = self.get_embedding(task)
        
            logger.info("Generating embeddings for teams...")
            team_embeddings = {}
            for team, skills in teams.items():
                logger.info(f"Getting embedding for team: {team}")
                team_embeddings[team] = self.get_embedding(skills)
        
            assignments = {team: [] for team in teams.keys()}
            logger.info("Calculating similarities...")
            for task, task_emb in task_embeddings.items():
                for team, team_emb in team_embeddings.items():
                    similarity = self.calculate_similarity(task_emb, team_emb)
                    logger.info(f"Similarity between '{task}' and '{team}': {similarity:.2%}")
                    if similarity >= similarity_threshold:
                        assignments[team].append((task, similarity))
        
            return assignments
            
        except Exception as e:
            logger.error(f"Error in task matching: {str(e)}", exc_info=True)
            print(f"Error occurred while matching tasks: {str(e)}")
            return {}

    @staticmethod
    def calculate_similarity(emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        emb1_np = np.array(emb1)
        emb2_np = np.array(emb2)
        return float(np.dot(emb1_np, emb2_np) / (np.linalg.norm(emb1_np) * np.linalg.norm(emb2_np)))

    def format_results(self, assignments: Dict[str, List[Tuple[str, float]]]) -> str:
        """Format the matching results as a structured list."""
        if not assignments:
            return "No matches found."
        output = []
        for team, tasks in assignments.items():
            if tasks:
                output.append(f"\nTeam: {team}")
                output.append("Matched Tasks:")
                for task, score in sorted(tasks, key=lambda x: x[1], reverse=True):
                    output.append(f"- {task}")
                    output.append(f"  Confidence: {score:.2%}")
        return "\n".join(output)

    def format_results_natural(self, assignments: Dict[str, List[Tuple[str, float]]]) -> str:
        """
        Format the matching results into a natural language summary.
        """
        if not assignments:
            return "No task assignments could be determined."
        sentences = []
        for team, tasks in assignments.items():
            if tasks:
                task_descriptions = []
                for task, score in sorted(tasks, key=lambda x: x[1], reverse=True):
                    task_descriptions.append(f"'{task}' (confidence: {score:.2%})")
                sentence = f"The {team} is best suited for the tasks: " + ", ".join(task_descriptions) + "."
                sentences.append(sentence)
        return " ".join(sentences)

# ---------------- IBM Chat Summary Function ----------------
def generate_natural_summary_via_chat(assignments: Dict[str, List[Tuple[str, float]]], retry_attempts: int = 2) -> str:
    """
    Generate a natural language summary of the task assignments by leveraging IBM's Chat API.
    This function builds a prompt based on the assignments and gets a refined summary.
    If the Chat API call fails (e.g., due to a gateway timeout), it will retry a few times.
    """
    if not assignments:
        return "No task assignments available to summarize."
    
    # Build a summary text from the assignments dictionary
    summary_lines = []
    for team, tasks in assignments.items():
        if tasks:
            tasks_text = "; ".join([f"{task} ({score:.2%})" for task, score in tasks])
            summary_lines.append(f"{team}: {tasks_text}")
    assignments_text = "\n".join(summary_lines)
    
    prompt = (
        "Based on the following task assignments between teams and tasks with their confidence scores:\n\n"
        f"{assignments_text}\n\n"
        "Please provide a detailed, natural language summary explaining which teams are best suited for which tasks, "
        "including any context or recommendations you deem useful."
    )
    
    for attempt in range(retry_attempts):
        try:
            IBM_token()  # Refresh token for the Chat API
            messages = [{"role": "user", "content": prompt}]
            chat_response = IBM_chat(messages)
            return chat_response
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}: Error generating chat summary: {e}")
            if "504" in str(e) and attempt < retry_attempts - 1:
                continue  # Try again
            else:
                break
    
    # Fallback to local natural language formatting
    fallback = TaskMatcher().format_results_natural(assignments)
    return f"Local Summary: {fallback if fallback else 'No matches reached the required threshold.'}"

# ---------------- Main Function ----------------
def main():
    matcher = TaskMatcher()
    try:
        logger.info("Starting task matching process...")
        
        # Example project tasks (plain text or a PDF file path)
        project_text = """
        Project Tasks:
        - Develop user authentication system
        - Create responsive dashboard
        - Implement database schema
        - Design API endpoints
        """
        # Example team skills (plain text or a PDF file path)
        teams_text = """
        Frontend Team: React, TypeScript, UI/UX, responsive design
        Backend Team: Python, Django, databases, API development
        """
        
        logger.info("Extracting tasks...")
        tasks = matcher.extract_tasks(project_text)
        logger.info(f"Found {len(tasks)} tasks")
        
        logger.info("Parsing team skills...")
        teams = matcher.parse_team_skills(teams_text)
        logger.info(f"Found {len(teams)} teams")
        
        logger.info("Attempting to match tasks to teams...")
        # Optionally adjust the similarity threshold if needed
        matches = matcher.match_tasks_to_teams(project_text, teams_text, similarity_threshold=0.5)
        
        if matches:
            print("Results (Structured):")
            print(matcher.format_results(matches))
            print("\nResults (Local Natural Language Summary):")
            print(matcher.format_results_natural(matches))
            
            print("\nResults (Refined via IBM Chat API):")
            chat_summary = generate_natural_summary_via_chat(matches)
            print(chat_summary)
        else:
            print("No matches were found or an error occurred")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        print(f"An error occurred: {str(e)}")

def test_basic_functionality():
    matcher = TaskMatcher()
    # Test task extraction
    project_text = """
    - Task 1
    - Task 2
    """
    tasks = matcher.extract_tasks(project_text)
    print("Extracted tasks:", tasks)
    # Test team parsing
    team_text = "Team A: Skill 1, Skill 2"
    teams = matcher.parse_team_skills(team_text)
    print("Parsed teams:", teams)

if __name__ == "__main__":
    print("Running basic functionality test...")
    test_basic_functionality()
    print("\nRunning main process...")
    main()

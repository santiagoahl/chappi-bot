import os
import gradio as gr
import requests
import inspect
import pandas as pd
import sys
import asyncio
import time
import openai
from openai.error import RateLimitError
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# Add local files
SRC_DIR = "src/"
AGENT_DIR = "src/agents"
TOOLS_DIR = "src/tools"
SYS_MSG_DIR = "prompts/agent"
sys.path.append(SRC_DIR)
sys.path.append(AGENT_DIR)
sys.path.append(TOOLS_DIR)
sys.path.append(SYS_MSG_DIR)

import tools
import react

# (Keep Constants as is)
# --- Constants ---
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"

# --- Basic Agent Definition ---
# ----- THIS IS WERE YOU CAN BUILD WHAT YOU WANT ------
class ReactAgent:
    def __init__(self):
        self._max_retries = 3
        logging.info("ReactAgent initialized.")

    def __call__(self, question: str) -> str:
        logging.info(f"Agent received question (first 50 chars): {question[:50]}...")
        
        for attempt in range(self._max_retries):
            try:
                agent_response = asyncio.run(
                    react.run_agent(user_query=question)
                )
                logging.info(f"Agent returning fixed answer: {agent_response}")
                return agent_response
            except RateLimitError as e:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                logging.info(f"[RateLimitError] Attempt {attempt+1}/{self._max_retries} - Sleeping {wait_time}s...")
                raise e
        return "Agent testing phase not successful."


def run_and_submit_all( profile: gr.OAuthProfile | None):
    """
    Fetches all questions, runs the ReactAgent on them, submits all answers,
    and displays the results.
    """
    # --- Determine HF Space Runtime URL and Repo URL ---
    space_id = os.getenv("SPACE_ID") # Get the SPACE_ID for sending link to the code

    if profile:
        username= f"{profile.username}"
        logging.info(f"User logged in: {username}")
    else:
        logging.info("User not logged in.")
        return "Please Login to Hugging Face with the button.", None

    api_url = DEFAULT_API_URL
    questions_url = f"{api_url}/questions"
    submit_url = f"{api_url}/submit"

    # 1. Instantiate Agent ( modify this part to create your agent)
    try:
        agent = ReactAgent()
    except Exception as e:
        logging.info(f"Error instantiating agent: {e}")
        return f"Error initializing agent: {e}", None
    # In the case of an app running as a hugging Face space, this link points toward your codebase ( usefull for others so please keep it public)
    agent_code = f"https://huggingface.co/spaces/{space_id}/tree/main"
    logging.info(agent_code)

    # 2. Fetch Questions
    logging.info(f"Fetching questions from: {questions_url}")
    try:
        response = requests.get(questions_url, timeout=15)
        response.raise_for_status()
        questions_data = response.json()
        if not questions_data:
             logging.info("Fetched questions list is empty.")
             return "Fetched questions list is empty or invalid format.", None
        logging.info(f"Fetched {len(questions_data)} questions.")
    except requests.exceptions.RequestException as e:
        logging.info(f"Error fetching questions: {e}")
        return f"Error fetching questions: {e}", None
    except requests.exceptions.JSONDecodeError as e:
         logging.info(f"Error decoding JSON response from questions endpoint: {e}")
         logging.info(f"Response text: {response.text[:500]}")
         return f"Error decoding server response for questions: {e}", None
    except Exception as e:
        logging.info(f"An unexpected error occurred fetching questions: {e}")
        return f"An unexpected error occurred fetching questions: {e}", None

    # 3. Run your Agent
    results_log = []
    answers_payload = []
    logging.info(f"Running agent on {len(questions_data)} questions...")
    for item in questions_data:
        task_id = item.get("task_id")
        question_text = item.get("question")
        if not task_id or question_text is None:
            logging.info(f"Skipping item with missing task_id or question: {item}")
            continue
        try:
            submitted_answer = agent(question_text)
            answers_payload.append({"task_id": task_id, "submitted_answer": submitted_answer})
            results_log.append({"Task ID": task_id, "Question": question_text, "Submitted Answer": submitted_answer})
        except Exception as e:
             logging.info(f"Error running agent on task {task_id}: {e}")
             results_log.append({"Task ID": task_id, "Question": question_text, "Submitted Answer": f"AGENT ERROR: {e}"})

    if not answers_payload:
        logging.info("Agent did not produce any answers to submit.")
        return "Agent did not produce any answers to submit.", pd.DataFrame(results_log)

    # 4. Prepare Submission 
    submission_data = {"username": username.strip(), "agent_code": agent_code, "answers": answers_payload}
    status_update = f"Agent finished. Submitting {len(answers_payload)} answers for user '{username}'..."
    logging.info(status_update)

    # 5. Submit
    logging.info(f"Submitting {len(answers_payload)} answers to: {submit_url}")
    try:
        response = requests.post(submit_url, json=submission_data, timeout=60)
        response.raise_for_status()
        result_data = response.json()
        final_status = (
            f"Submission Successful!\n"
            f"User: {result_data.get('username')}\n"
            f"Overall Score: {result_data.get('score', 'N/A')}% "
            f"({result_data.get('correct_count', '?')}/{result_data.get('total_attempted', '?')} correct)\n"
            f"Message: {result_data.get('message', 'No message received.')}"
        )
        logging.info("Submission successful.")
        results_df = pd.DataFrame(results_log)
        return final_status, results_df
    except requests.exceptions.HTTPError as e:
        error_detail = f"Server responded with status {e.response.status_code}."
        try:
            error_json = e.response.json()
            error_detail += f" Detail: {error_json.get('detail', e.response.text)}"
        except requests.exceptions.JSONDecodeError:
            error_detail += f" Response: {e.response.text[:500]}"
        status_message = f"Submission Failed: {error_detail}"
        logging.info(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except requests.exceptions.Timeout:
        status_message = "Submission Failed: The request timed out."
        logging.info(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except requests.exceptions.RequestException as e:
        status_message = f"Submission Failed: Network error - {e}"
        logging.info(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except Exception as e:
        status_message = f"An unexpected error occurred during submission: {e}"
        logging.info(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df


# --- Build Gradio Interface using Blocks ---
with gr.Blocks() as demo:
    gr.Markdown("# Basic Agent Evaluation Runner")
    gr.Markdown(
        """
        **Instructions:**

        1.  Please clone this space, then modify the code to define your agent's logic, the tools, the necessary packages, etc ...
        2.  Log in to your Hugging Face account using the button below. This uses your HF username for submission.
        3.  Click 'Run Evaluation & Submit All Answers' to fetch questions, run your agent, submit answers, and see the score.

        ---
        **Disclaimers:**
        Once clicking on the "submit button, it can take quite some time ( this is the time for the agent to go through all the questions).
        This space provides a basic setup and is intentionally sub-optimal to encourage you to develop your own, more robust solution. For instance for the delay process of the submit button, a solution could be to cache the answers and submit in a seperate action or even to answer the questions in async.
        """
    )

    gr.LoginButton()

    run_button = gr.Button("Run Evaluation & Submit All Answers")

    status_output = gr.Textbox(label="Run Status / Submission Result", lines=5, interactive=False)
    # Removed max_rows=10 from DataFrame constructor
    results_table = gr.DataFrame(label="Questions and Agent Answers", wrap=True)

    run_button.click(
        fn=run_and_submit_all,
        outputs=[status_output, results_table]
    )

if __name__ == "__main__":
    logging.info("\n" + "-"*30 + " App Starting " + "-"*30)
    # Check for SPACE_HOST and SPACE_ID at startup for information
    space_host_startup = os.getenv("SPACE_HOST")
    space_id_startup = os.getenv("SPACE_ID") # Get SPACE_ID at startup

    if space_host_startup:
        logging.info(f"✅ SPACE_HOST found: {space_host_startup}")
        logging.info(f"   Runtime URL should be: https://{space_host_startup}.hf.space")
    else:
        logging.info("ℹ️  SPACE_HOST environment variable not found (running locally?).")

    if space_id_startup: # logging.info repo URLs if SPACE_ID is found
        logging.info(f"✅ SPACE_ID found: {space_id_startup}")
        logging.info(f"   Repo URL: https://huggingface.co/spaces/{space_id_startup}")
        logging.info(f"   Repo Tree URL: https://huggingface.co/spaces/{space_id_startup}/tree/main")
    else:
        logging.info("ℹ️  SPACE_ID environment variable not found (running locally?). Repo URL cannot be determined.")

    logging.info("-"*(60 + len(" App Starting ")) + "\n")

    logging.info("Launching Gradio Interface for Basic Agent Evaluation...")
    demo.launch(debug=True, share=False)
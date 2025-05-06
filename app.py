import os
import gradio as gr
import requests
import inspect
import pandas as pd
import re
import logging
from logging.handlers import RotatingFileHandler
import datetime
from dotenv import load_dotenv
from smolagents import (
    CodeAgent, 
    HfApiModel,
    DuckDuckGoSearchTool, 
    WikipediaSearchTool,
    SpeechToTextTool,
    LogLevel, 
    load_tool,
    PythonInterpreterTool
)
from tools import *


# Logging setup
def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Create log filename with timestamp
    log_filename = f"logs/agent_run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File output handler
    file_handler = RotatingFileHandler(log_filename, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    # Console output handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

# Load environment variables
load_dotenv()

# Prompt for HF_TOKEN if not present in environment
if not os.getenv("HF_TOKEN"):
    print("\n" + "="*80)
    print("HF_TOKEN not found in environment variables.")
    print("You need a Hugging Face token to use DeepSeek-R1 model via Together API.")
    print("Please enter your HF_TOKEN below (it will only be stored for this session):")
    token = input("HF_TOKEN: ").strip()
    if token:
        os.environ["HF_TOKEN"] = token
        print("HF_TOKEN set for this session.")
    else:
        print("No token provided. The application may not work correctly.")
    print("="*80 + "\n")

# Check if HF_TOKEN is available
logger.info(f"HF_TOKEN detected: {'Yes' if os.getenv('HF_TOKEN') else 'No'}")

# --- Constants ---
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"

# --- Basic Agent Definition ---
class BasicAgent:
    def __init__(self):
        logger.info("Initializing Agent with tools...")
        
        # Use DeepSeek-R1 model
        self.model = HfApiModel(
            model_id="deepseek-ai/DeepSeek-R1",
            token=os.getenv("HF_TOKEN"),
            provider="together",
            max_tokens=8096,
            temperature=0.2  # Setting low temperature globally for more accurate answers
        )

        # Creating basic tools
        self.tools = [
            WikipediaSearchTool(),
            DuckDuckGoSearchTool(),
            TaskFileDownloaderTool(),
            SpeechToTextTool(),
            FileOpenerTool(),
            ImageAnalysisTool(),
            YouTubeTranscriptTool(),
            ExcelAnalysisTool(),
            TextProcessingTool(),
            MathematicalReasoningTool(),
            PythonInterpreterTool()
        ]

        # Initialize the agent with debugging enabled
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            verbosity_level=LogLevel.DEBUG,
            additional_authorized_imports=[
                "pandas", "re", "json", "os", "sys", "datetime"
            ]
        )

        logger.info("Agent initialized successfully with DeepSeek-R1 model via Together API")

    def __call__(self, question: str, task_id: str, file_name: str = "") -> str:
        """
        Process a question with associated task_id, matching the example interface.
        
        Args:
            question: The question text to answer
            task_id: The task ID associated with the question
            file_name: Name of file associated with the task, if any
            
        Returns:
            Answer to the question
        """
        logger.info(f"Agent received question: {question[:100]}...")
        
        try:
            # Automatically download the file if filename is specified
            if file_name and file_name.strip():
                try:
                    logger.info(f"Downloading file: {file_name} for task: {task_id}")
                    for tool in self.tools:
                        if tool.name == "TaskFileDownloaderTool":
                            download_result = tool.forward(task_id=task_id, file_name=file_name)
                            logger.info(f"Download result: {download_result}")
                            break
                except Exception as download_error:
                    logger.error(f"Error downloading file: {download_error}")
            
            # Create a direct universal prompt
            prompt = f"""Answer the following question with precision and accuracy. Use the available tools to find the needed information.

Question: {question}
Task ID: {task_id}

Instructions:
1. For questions about facts, dates, or historical information, use DuckDuckGo or Wikipedia search.
2. For questions that require counting or numerical analysis, be extremely careful and double-check your work.
3. For questions involving files:
   - If it's an image, use ImageAnalysisTool to interpret it
   - If it's an audio file, use SpeechToTextTool to transcribe it
   - If it's an Excel file, use ExcelAnalysisTool to examine it
   - If it's a Python file, use PythonInterpreterTool to execute it
   - If it's any other file type, use FileOpenerTool to read it
4. For questions about YouTube videos, use YouTubeTranscriptTool.
5. For code-related questions, use PythonInterpreterTool.

If the question asks for a specific number or value, just provide that exact number or value as your answer, nothing more.
If you're counting items, double-check your count by listing all items that match the criteria.
For code output questions, execute the code and provide exactly what the code outputs.

Your answer:"""
            
            # Run agent with the prompt
            logger.info("Running agent with prompt...")
            
            try:
                response = self.agent.run(prompt)
                
            except Exception as e:
                # Check if error is related to context length
                if "context_length_exceeded" in str(e) or "maximum context length" in str(e):
                    logger.warning(f"Context length exceeded. Trying with simplified prompt...")
                    # Use an even simpler prompt
                    simplified_prompt = f"""Question: {question}
                    Answer concisely:"""
                    
                    response = self.agent.run(simplified_prompt)
                else:
                    # Re-raise if not a context length error
                    raise
            
            # Basic post-processing
            if not isinstance(response, str):
                logger.info(f"Converting non-string response to string")
                response = str(response)
                
            response = response.strip()
            
            # Clean up numerical answers for consistency
            if response and response[0].isdigit():
                # If starts with a digit, try to extract just the number
                import re
                number_match = re.match(r'^(\d+\.\d+|\d+)', response)
                if number_match:
                    cleaned_response = number_match.group(1)
                    logger.info(f"Cleaned numerical response from '{response}' to '{cleaned_response}'")
                    response = cleaned_response
            
            # Enhanced logging
            logger.info(f"\n{'*' * 100}")
            logger.info(f"RAW AGENT RESPONSE: {response}")
            logger.info(f"{'*' * 100}\n")
            
            logger.info(f"\n{'=' * 100}")
            logger.info(f"FINAL ANSWER: {response}")
            logger.info(f"{'=' * 100}\n")
            
            return response

        except Exception as e:
            error_msg = f"Error generating answer: {str(e)}"
            logger.error(error_msg)
            return error_msg

def run_and_submit_all(profile: gr.OAuthProfile | None):
    """
    Fetches all questions, runs the BasicAgent on them, submits all answers,
    and displays the results.
    """
    # --- Determine HF Space Runtime URL and Repo URL ---
    space_id = os.getenv("SPACE_ID") # Get the SPACE_ID for sending link to the code

    if profile:
        username= f"{profile.username}"
        logger.info(f"User logged in: {username}")
    else:
        logger.info("User not logged in.")
        return "Please Login to Hugging Face with the button.", None

    api_url = DEFAULT_API_URL
    questions_url = f"{api_url}/questions"
    submit_url = f"{api_url}/submit"

    # 1. Instantiate Agent ( modify this part to create your agent)
    try:
        agent = BasicAgent()
    except Exception as e:
        logger.error(f"Error instantiating agent: {e}")
        return f"Error initializing agent: {e}", None
    # In the case of an app running as a hugging Face space, this link points toward your codebase ( usefull for others so please keep it public)
    agent_code = f"https://huggingface.co/spaces/{space_id}/tree/main"
    logger.info(agent_code)

    # 2. Fetch Questions
    logger.info(f"Fetching questions from: {questions_url}")
    try:
        response = requests.get(questions_url, timeout=15)
        response.raise_for_status()
        questions_data = response.json()
        if not questions_data:
             logger.warning("Fetched questions list is empty.")
             return "Fetched questions list is empty or invalid format.", None
        logger.info(f"Fetched {len(questions_data)} questions.")
        # Print example question format for debugging
        if questions_data:
            logger.info(f"Example question format: {questions_data[0]}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching questions: {e}")
        return f"Error fetching questions: {e}", None
    except requests.exceptions.JSONDecodeError as e:
         logger.error(f"Error decoding JSON response from questions endpoint: {e}")
         logger.error(f"Response text: {response.text[:500]}")
         return f"Error decoding server response for questions: {e}", None
    except Exception as e:
        logger.error(f"An unexpected error occurred fetching questions: {e}")
        return f"An unexpected error occurred fetching questions: {e}", None

    # 3. Run Agent
    results_log = []
    answers_payload = []
    logger.info(f"Running agent on {len(questions_data)} questions...")
    
    # Processing all questions
    for item in questions_data:
        task_id = item.get("task_id")
        question_text = item.get("question")
        file_name = item.get("file_name", "")  # Get file_name if it exists
        
        if not task_id or question_text is None:
            logger.warning(f"Skipping item with missing task_id or question: {item}")
            continue

        try:
            logger.info(f"Processing task_id: {task_id}, file_name: {file_name}")
            
            # Pre-download the file if file_name is provided
            if file_name:
                try:
                    logger.info(f"Pre-downloading file: {file_name} for task: {task_id}")
                    for tool in agent.tools:
                        if tool.name == "TaskFileDownloaderTool":
                            download_result = tool.forward(task_id=task_id)
                            logger.info(f"Download result: {download_result}")
                            break
                except Exception as download_error:
                    logger.error(f"Error pre-downloading file: {download_error}")
            
            # Call the agent with question, task_id and file_name
            submitted_answer = agent(question_text, task_id, file_name)
            
            answers_payload.append({"task_id": task_id, "submitted_answer": submitted_answer})
            results_log.append({
                "Task ID": task_id, 
                "File Name": file_name,
                "Question": question_text, 
                "Submitted Answer": submitted_answer
            })
            
            # Visual separator between questions
            separator = "="*80
            logger.info(f"\n{separator}")
            
            # For console - with color
            print(f"\033[1;36mQUESTION {len(answers_payload)}:\033[0m {question_text}")
            print(f"\033[1;31mFINAL ANSWER for task {task_id}:\033[0m")
            print(f"\033[1;31m{submitted_answer}\033[0m")
            
            # For log file - plain text with special formatting to make it stand out
            logger.info(f"\n{'=' * 80}")
            logger.info(f"QUESTION {len(answers_payload)}: {question_text}")
            logger.info(f"\n{'*' * 50} FINAL ANSWER {'*' * 50}")
            logger.info(f"TASK ID: {task_id}")
            logger.info(f"{'=' * 120}")
            logger.info(f"{submitted_answer}")
            logger.info(f"{'=' * 120}")
            logger.info(f"{'*' * 120}\n")
            
            logger.info(f"{separator}\n")
            
        except Exception as e:
            logger.error(f"Error running agent on task {task_id}: {e}")
            results_log.append({
                "Task ID": task_id,
                "File Name": file_name,
                "Question": question_text, 
                "Submitted Answer": f"AGENT ERROR: {e}"
            })

    if not answers_payload:
        logger.warning("Agent did not produce any answers to submit.")
        return "Agent did not produce any answers to submit.", pd.DataFrame(results_log)

    # 4. Prepare Submission
    submission_data = {"username": username.strip(), "agent_code": agent_code, "answers": answers_payload}
    status_update = f"Agent finished. Submitting {len(answers_payload)} answers for user '{username}'..."
    logger.info(status_update)

    # 5. Submit
    logger.info(f"Submitting {len(answers_payload)} answers to: {submit_url}")
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
        logger.info("Submission successful.")
        logger.info(final_status)
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
        logger.error(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except requests.exceptions.Timeout:
        status_message = "Submission Failed: The request timed out."
        logger.error(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except requests.exceptions.RequestException as e:
        status_message = f"Submission Failed: Network error - {e}"
        logger.error(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except Exception as e:
        status_message = f"An unexpected error occurred during submission: {e}"
        logger.error(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df


with gr.Blocks() as demo:
    gr.Markdown("# Advanced Agent Evaluation Runner")
    gr.Markdown(
        """
        **Instructions:**
        1. Make sure you have set up your environment variables:
           - HF_TOKEN: Your Hugging Face token for accessing the model
           - YOUTUBE_API_KEY: Your YouTube API key (optional)
        2. Log in to your Hugging Face account using the button below
        3. Click 'Run Evaluation & Submit All Answers' to process all questions
        
        The agent will use:
        - DeepSeek-R1 LLM via Together API
        - Web search (DuckDuckGo)
        - Wikipedia search (enhanced implementation)
        - YouTube transcript analysis
        - Image, speech, and Excel file analysis
        - Code interpretation and mathematical reasoning
        - Text and file processing capabilities
        """
    )

    gr.LoginButton()
    run_button = gr.Button("Run Evaluation & Submit All Answers")
    status_output = gr.Textbox(label="Run Status / Submission Result", lines=5, interactive=False)
    results_table = gr.DataFrame(label="Questions and Agent Answers", wrap=True)

    run_button.click(
        fn=run_and_submit_all,
        outputs=[status_output, results_table]
    )


if __name__ == "__main__":
    print("\n" + "-"*30 + " App Starting " + "-"*30)
    # Check for SPACE_HOST and SPACE_ID at startup for information
    space_host_startup = os.getenv("SPACE_HOST")
    space_id_startup = os.getenv("SPACE_ID") # Get SPACE_ID at startup

    if space_host_startup:
        print(f"✅ SPACE_HOST found: {space_host_startup}")
        print(f"   Runtime URL should be: https://{space_host_startup}.hf.space")
    else:
        print("ℹ️  SPACE_HOST environment variable not found (running locally?).")

    if space_id_startup: # Print repo URLs if SPACE_ID is found
        print(f"✅ SPACE_ID found: {space_id_startup}")
        print(f"   Repo URL: https://huggingface.co/spaces/{space_id_startup}")
        print(f"   Repo Tree URL: https://huggingface.co/spaces/{space_id_startup}/tree/main")
    else:
        print("ℹ️  SPACE_ID environment variable not found (running locally?). Repo URL cannot be determined.")

    print("-"*(60 + len(" App Starting ")) + "\n")

    print("Launching Gradio Interface for Basic Agent Evaluation...")
    demo.launch(debug=True, share=False)

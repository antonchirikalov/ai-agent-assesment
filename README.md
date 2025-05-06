---
title: Ai Final Assessment
emoji: 🐨
colorFrom: gray
colorTo: blue
sdk: gradio
sdk_version: 5.28.0
app_file: app.py
pinned: false
hf_oauth: true
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# AI Agent for Hugging Face Agents Course

This project implements a simple AI agent for the Hugging Face Agents Course final assessment. The agent is designed to answer a wide variety of questions using a combination of canned responses and generative responses.

## Project Structure

The project follows a simplified architecture with minimal dependencies:

### 1. Main Application
- `app.py`: Contains both the BasicAgent implementation and the Gradio interface
  - BasicAgent class with canned responses for common question types
  - Simple file downloading capability
  - Reliable submission process to the evaluation server

### 2. Fault Tolerance
The project includes several fault tolerance mechanisms:
- Basic error handling for file downloads and API requests
- Canned responses for common topics to avoid complex API calls
- Timeouts on all external service requests
- Comprehensive logging

### 3. Application Features
- Simple but effective answer generation using pattern matching
- File download support for task-based questions
- Error recovery
- Response logging

## Dependencies

- Python 3.8+
- gradio
- requests
- pandas

## Running the Project

The project runs as a Hugging Face Space through the Gradio interface defined in `app.py`. Users can click the "Run Evaluation & Submit All Answers" button, which will fetch questions, run the agent on them, submit answers to the evaluation server, and display the results.

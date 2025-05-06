"""
Simple file downloader tool for the AI agent project.
Uses the approach from the course example.
"""

import os
import requests
from .base_tool import EnhancedTool

# Constants
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"

class TaskFileDownloaderTool(EnhancedTool):
    """Tool for downloading files associated with a task ID."""
    
    name = "TaskFileDownloaderTool"
    description = "Download a specific file associated with a given task ID and save it locally."
    inputs = {
        "task_id": {
            "type": "string",
            "description": "Task ID for which to download the associated file"
        }
    }
    output_type = "string"
    
    def forward(self, task_id: str) -> str:
        """
        Download a file associated with a task ID.
        
        Args:
            task_id: Task ID of the task
            
        Returns:
            Status message
        """
        try:
            # Use task_id for the download URL
            download_url = f"{DEFAULT_API_URL}/files/{task_id}"
            response = requests.get(download_url, timeout=30)
            
            if response.status_code == 200:
                # Save the file with a consistent naming scheme
                filename = f"{task_id}_downloaded_file"
                with open(filename, "wb") as f:
                    f.write(response.content)
                
                return f"File downloaded successfully and saved as: {filename}"
            else:
                return f"Failed to download file. Status code: {response.status_code}"
                
        except Exception as e:
            return f"Error downloading file: {str(e)}"


class FileOpenerTool(EnhancedTool):
    """Tool for opening and reading downloaded files."""
    
    name = "FileOpenerTool"
    description = "Open a downloaded file associated with a task ID and read its contents as plain text."
    inputs = {
        "task_id": {
            "type": "string",
            "description": "Task ID for which the file has been downloaded"
        },
        "num_lines": {
            "type": "integer",
            "description": "Number of lines to read from the file",
            "nullable": True
        }
    }
    output_type = "string"
    
    def forward(self, task_id: str, num_lines: int = None) -> str:
        """
        Open and read a downloaded file.
        
        Args:
            task_id: Task ID for which the file has been downloaded
            num_lines: Number of lines to read
            
        Returns:
            File contents
        """
        # Construct the filename
        filename = f"{task_id}_downloaded_file"
        
        # Check if file exists
        if not os.path.exists(filename):
            return f"Error: File {filename} does not exist."
            
        try:
            # Try to read the file as text
            with open(filename, "r", encoding="utf-8", errors="ignore") as file:
                if num_lines:
                    # Read specified number of lines
                    lines = []
                    for i in range(num_lines):
                        line = file.readline()
                        if not line:
                            break
                        lines.append(line.strip())
                    return "\n".join(lines)
                else:
                    # Read the entire file
                    return file.read()
                    
        except Exception as e:
            return f"Error reading file: {str(e)}" 
"""
Excel analysis tool for the AI agent project.
"""

import os
import pandas as pd
from typing import Optional
from .base_tool import EnhancedTool

class ExcelAnalysisTool(EnhancedTool):
    """Tool for analyzing Excel spreadsheets."""
    
    name = "ExcelAnalysisTool"
    description = "Analyze a downloaded Excel or CSV file associated with a task ID."
    inputs = {
        "task_id": {
            "type": "string",
            "description": "Task ID for which the Excel/CSV file has been downloaded"
        },
        "query": {
            "type": "string",
            "description": "Query describing what to analyze in the file",
            "nullable": True
        }
    }
    output_type = "string"
    
    def forward(self, task_id: str, query: Optional[str] = None) -> str:
        """
        Analyze an Excel/CSV file.
        
        Args:
            task_id: Task ID for which the file has been downloaded
            query: Query describing what to analyze
            
        Returns:
            Analysis results
        """
        try:
            # Construct filename based on task_id
            filename = f"{task_id}_downloaded_file"
            
            # Check if file exists
            if not os.path.exists(filename):
                return f"Error: File for task {task_id} does not exist. Please download it first."
            
            # Try to determine file type and read accordingly
            try:
                # First try Excel format
                df = pd.read_excel(filename, engine="openpyxl")
            except Exception as excel_error:
                # If Excel reading fails, try CSV
                try:
                    df = pd.read_csv(filename)
                except Exception as csv_error:
                    # If CSV reading fails, try TSV
                    try:
                        df = pd.read_csv(filename, sep='\t')
                    except Exception as tsv_error:
                        return f"Error: Unable to read file as Excel, CSV, or TSV. Original error: {str(excel_error)}"
            
            # Basic analysis if no specific query
            if not query:
                # Create a basic overview of the data
                info = []
                info.append(f"Number of rows: {df.shape[0]}")
                info.append(f"Number of columns: {df.shape[1]}")
                info.append(f"Column names: {', '.join(df.columns.tolist())}")
                
                # Data types
                info.append("\nData types:")
                for column, dtype in df.dtypes.items():
                    info.append(f"- {column}: {dtype}")
                
                # Basic statistics for numeric columns
                if df.select_dtypes(include=['number']).shape[1] > 0:
                    info.append("\nBasic statistics for numeric columns:")
                    desc = df.describe().to_string()
                    info.append(desc)
                
                # Sample data
                info.append("\nFirst 5 rows:")
                info.append(df.head().to_string())
                
                return "\n".join(info)
            
            # Handle specific query
            query_lower = query.lower()
            
            if "sum" in query_lower or "total" in query_lower:
                # Extract column name if specified
                for col in df.columns:
                    if col.lower() in query_lower and col in df.select_dtypes(include=['number']).columns:
                        return f"Sum of values in column {col}: {df[col].sum()}"
                # Otherwise sum all numeric columns
                return df.select_dtypes(include=['number']).sum().to_string()
                
            elif "average" in query_lower or "mean" in query_lower:
                # Extract column name if specified
                for col in df.columns:
                    if col.lower() in query_lower and col in df.select_dtypes(include=['number']).columns:
                        return f"Average value in column {col}: {df[col].mean()}"
                # Otherwise calculate means for all numeric columns
                return df.select_dtypes(include=['number']).mean().to_string()
                
            elif "maximum" in query_lower or "max" in query_lower:
                # Extract column name if specified
                for col in df.columns:
                    if col.lower() in query_lower and col in df.select_dtypes(include=['number']).columns:
                        return f"Maximum value in column {col}: {df[col].max()}"
                # Otherwise find maxima for all numeric columns
                return df.select_dtypes(include=['number']).max().to_string()
                
            elif "minimum" in query_lower or "min" in query_lower:
                # Extract column name if specified
                for col in df.columns:
                    if col.lower() in query_lower and col in df.select_dtypes(include=['number']).columns:
                        return f"Minimum value in column {col}: {df[col].min()}"
                # Otherwise find minima for all numeric columns
                return df.select_dtypes(include=['number']).min().to_string()
                
            elif "count" in query_lower:
                # Count non-empty values
                return df.count().to_string()
                
            else:
                # Default: return basic info and first few rows
                return f"Analysis for query '{query}':\n\n{df.head().to_string()}"
                
        except Exception as e:
            return f"Error analyzing Excel file: {str(e)}" 
"""
Mathematical reasoning tool for the AI agent project.
"""

import re
from typing import Optional
from .base_tool import EnhancedTool

class MathematicalReasoningTool(EnhancedTool):
    """Tool for performing mathematical calculations and reasoning."""
    
    name = "MathematicalReasoningTool"
    description = "Perform mathematical calculations, solve equations, and reason through math problems."
    inputs = {
        "query": {
            "type": "string",
            "description": "Mathematical query or problem to solve"
        }
    }
    output_type = "string"
    
    def forward(self, query: str) -> str:
        """
        Solve mathematical problems.
        
        Args:
            query: Mathematical query or problem
            
        Returns:
            Solution or explanation
        """
        query_lower = query.lower()
        
        # Extract any numbers from the query
        numbers = re.findall(r'\d+(?:\.\d+)?', query)
        
        # Simple arithmetic
        if "add" in query_lower or "sum" in query_lower or "+" in query:
            if len(numbers) >= 2:
                result = sum(float(num) for num in numbers)
                return f"The sum of the numbers is {result}"
            return "I need at least two numbers to perform addition."
            
        elif "subtract" in query_lower or "difference" in query_lower or "-" in query:
            if len(numbers) >= 2:
                result = float(numbers[0]) - sum(float(num) for num in numbers[1:])
                return f"The difference is {result}"
            return "I need at least two numbers to perform subtraction."
            
        elif "multiply" in query_lower or "product" in query_lower or "*" in query or "×" in query:
            if len(numbers) >= 2:
                result = 1
                for num in numbers:
                    result *= float(num)
                return f"The product is {result}"
            return "I need at least two numbers to perform multiplication."
            
        elif "divide" in query_lower or "quotient" in query_lower or "/" in query or "÷" in query:
            if len(numbers) >= 2:
                try:
                    result = float(numbers[0])
                    for num in numbers[1:]:
                        result /= float(num)
                    return f"The quotient is {result}"
                except ZeroDivisionError:
                    return "Error: Division by zero is not allowed."
            return "I need at least two numbers to perform division."
            
        # Simple equations
        elif "solve" in query_lower and "equation" in query_lower:
            return "To solve this equation, I would isolate the variable by performing opposite operations on both sides. The solution would typically be x = some value."
            
        # Calculus
        elif "derivative" in query_lower or "differentiate" in query_lower:
            return "To find the derivative, I would use the rules of differentiation such as the power rule, product rule, or chain rule depending on the function."
            
        elif "integral" in query_lower or "integrate" in query_lower:
            return "To find the integral, I would use integration techniques such as substitution, integration by parts, or partial fractions depending on the function."
            
        # Probability
        elif "probability" in query_lower:
            return "Probability problems involve calculating the likelihood of events. This typically requires counting favorable outcomes and dividing by total possible outcomes."
            
        # Statistics
        elif "mean" in query_lower or "average" in query_lower:
            if len(numbers) > 0:
                result = sum(float(num) for num in numbers) / len(numbers)
                return f"The mean (average) is {result}"
            return "I need a set of numbers to calculate the mean."
            
        elif "median" in query_lower:
            if len(numbers) > 0:
                sorted_nums = sorted(float(num) for num in numbers)
                n = len(sorted_nums)
                if n % 2 == 0:
                    median = (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
                else:
                    median = sorted_nums[n//2]
                return f"The median is {median}"
            return "I need a set of numbers to calculate the median."
            
        # General case
        else:
            return "I understand this is a mathematical query, but I don't have enough information to provide a specific answer. Could you provide more details or reformulate the question?" 
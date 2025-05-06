"""
Base tool class with enhanced error handling and logging.
"""

import logging
from typing import Any
from smolagents import Tool

logger = logging.getLogger("ai_agent.tools")

class EnhancedTool(Tool):
    """
    Base class for all tools with enhanced error handling and logging.
    Extends the smolagents Tool class with additional capabilities.
    """
    
    def __init__(self):
        """Initialize the tool with enhanced capabilities"""
        super().__init__()
        self.metadata = {"successes": 0, "failures": 0}
    
    def forward(self, **kwargs: Any) -> str:
        """
        Abstract method to be implemented by child classes.
        All tools should implement this method.
        
        Args:
            **kwargs: Keyword arguments for the tool
            
        Returns:
            Tool output as string
        """
        raise NotImplementedError("Subclasses must implement this method")
        
    def __call__(self, *args, **kwargs):
        """
        Override the __call__ method to ensure we always return a string
        and handle common errors.
        """
        try:
            # Call the parent class method which will eventually call our forward method
            result = super().__call__(*args, **kwargs)
            
            # Make sure we never return non-string values
            if not isinstance(result, str):
                logger.warning(f"Tool {self.__class__.__name__} returned a non-string value: {type(result)}. Converting to string.")
                if result is None:
                    return "No result available."
                else:
                    # Always convert to string for safety
                    return str(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in tool {self.__class__.__name__}: {str(e)}")
            return f"Error executing {self.__class__.__name__}: {str(e)}"
        
    def get_success_rate(self) -> float:
        """
        Get the success rate of this tool
        
        Returns:
            Success rate as a float between 0 and 1
        """
        total = self.metadata["successes"] + self.metadata["failures"]
        if total == 0:
            return 0.0
        return self.metadata["successes"] / total
        
    def reset_metrics(self) -> None:
        """Reset the success/failure metrics"""
        self.metadata["successes"] = 0
        self.metadata["failures"] = 0 
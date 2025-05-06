"""
Error handling utilities for the AI agent project.
"""

import functools
import time
import logging
from typing import Callable, Dict, Any, TypeVar, Optional

# Type variables for function signature
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

class ToolExecutionError(Exception):
    """Exception raised when a tool execution fails."""
    
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        self.message = message
        super().__init__(f"Error executing {tool_name}: {message}")

def log_exceptions(func: F) -> F:
    """
    Decorator to log exceptions raised by functions.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get the logger for the module where the function is defined
            logger = logging.getLogger(func.__module__)
            logger.error(f"Exception in {func.__name__}: {e}")
            # Re-raise the exception
            raise
    
    return wrapper

def retry(tries: int = 3, delay: float = 1, backoff: float = 2, logger_func: Callable = print) -> Callable:
    """
    Retry decorator with exponential backoff.
    
    Args:
        tries: Number of times to try before giving up
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier
        logger_func: Function to use for logging
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    msg = f"{func.__name__} - Retrying in {mdelay}s... ({mtries-1} tries left). Error: {e}"
                    if logger_func:
                        logger_func(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            
            # If we get here, we've exhausted all retries
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

class FallbackRegistry:
    """Registry for tool fallbacks."""
    
    _fallbacks = {}
    
    @classmethod
    def register_fallback(cls, tool_name: str, fallback_func: Callable) -> None:
        """
        Register a fallback function for a tool.
        
        Args:
            tool_name: Name of the tool
            fallback_func: Fallback function to use
        """
        cls._fallbacks[tool_name] = fallback_func
    
    @classmethod
    def get_fallback(cls, tool_name: str) -> Optional[Callable]:
        """
        Get the fallback function for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Fallback function or None if not found
        """
        return cls._fallbacks.get(tool_name) 
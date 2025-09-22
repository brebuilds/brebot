"""
Logging configuration for Brebot.
Provides structured logging with different levels and outputs.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json

from loguru import logger
from rich.console import Console
from rich.logging import RichHandler

from config.settings import settings


class BrebotLogger:
    """Custom logger for Brebot with structured logging capabilities."""
    
    def __init__(self, name: str = "brebot", log_level: str = None):
        """
        Initialize the Brebot logger.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.name = name
        self.log_level = log_level or settings.log_level
        self.console = Console()
        
        # Remove default loguru handler
        logger.remove()
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        # Create logs directory if it doesn't exist
        log_file_path = Path(settings.log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Console handler with Rich formatting
        logger.add(
            sys.stdout,
            level=self.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # File handler with JSON formatting
        logger.add(
            log_file_path,
            level=self.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=settings.log_max_size,
            retention=f"{settings.log_retention} days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
        
        # Error file handler
        error_log_path = log_file_path.parent / "brebot_errors.log"
        logger.add(
            error_log_path,
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
    
    def log_agent_action(self, agent_name: str, action: str, details: dict = None):
        """
        Log agent actions with structured format.
        
        Args:
            agent_name: Name of the agent performing the action
            action: Action being performed
            details: Additional details about the action
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action": action,
            "details": details or {}
        }
        
        logger.info(f"🤖 Agent Action: {agent_name} - {action}", extra=log_data)
    
    def log_tool_usage(self, tool_name: str, input_data: dict, output: str, success: bool = True):
        """
        Log tool usage with input/output data.
        
        Args:
            tool_name: Name of the tool being used
            input_data: Input parameters to the tool
            output: Output from the tool
            success: Whether the tool execution was successful
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "input": input_data,
            "output": output,
            "success": success
        }
        
        level = "INFO" if success else "ERROR"
        logger.log(level, f"🔧 Tool Usage: {tool_name}", extra=log_data)
    
    def log_crew_activity(self, crew_name: str, activity: str, details: dict = None):
        """
        Log crew-level activities.
        
        Args:
            crew_name: Name of the crew
            activity: Activity being performed
            details: Additional details
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "crew": crew_name,
            "activity": activity,
            "details": details or {}
        }
        
        logger.info(f"👥 Crew Activity: {crew_name} - {activity}", extra=log_data)
    
    def log_error(self, error: Exception, context: str = None):
        """
        Log errors with full context.
        
        Args:
            error: Exception that occurred
            context: Additional context about where the error occurred
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        
        logger.error(f"❌ Error: {type(error).__name__}: {str(error)}", extra=log_data)
    
    def log_performance(self, operation: str, duration: float, details: dict = None):
        """
        Log performance metrics.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
            details: Additional performance details
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration_seconds": duration,
            "details": details or {}
        }
        
        logger.info(f"⏱️  Performance: {operation} took {duration:.2f}s", extra=log_data)


# Global logger instance
brebot_logger = BrebotLogger()


def get_logger(name: str = "brebot") -> BrebotLogger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        BrebotLogger: Logger instance
    """
    return BrebotLogger(name)


def log_function_call(func):
    """
    Decorator to log function calls.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            brebot_logger.log_performance(
                operation=f"{func.__module__}.{func.__name__}",
                duration=duration,
                details={
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            
            brebot_logger.log_error(
                error=e,
                context=f"Function call: {func.__module__}.{func.__name__}"
            )
            
            brebot_logger.log_performance(
                operation=f"{func.__module__}.{func.__name__}",
                duration=duration,
                details={
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                    "success": False,
                    "error": str(e)
                }
            )
            
            raise
    
    return wrapper


# Export the main logger
__all__ = ["BrebotLogger", "brebot_logger", "get_logger", "log_function_call"]

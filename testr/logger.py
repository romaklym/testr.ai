import json
import logging
import datetime
import functools
import os
from pathlib import Path

class TestLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_test_logs = []
        
        # Set up file handler for JSON logs
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.json_log_file = self.log_dir / f"test_run_{timestamp}.json"
        
        # Set up console logger
        self.console_logger = logging.getLogger("testr")
        if not self.console_logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.console_logger.addHandler(console_handler)
            self.console_logger.setLevel(logging.INFO)

    def log(self, level, message, **extra):
        # Log to console
        self.console_logger.log(level, message)
        
        # Store log entry for JSON
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": logging.getLevelName(level),
            "message": message,
            **extra
        }
        self.current_test_logs.append(log_entry)
        
        # Write to JSON file
        self._write_json_log()

    def _write_json_log(self):
        with open(self.json_log_file, 'w') as f:
            json.dump({"logs": self.current_test_logs}, f, indent=2)

def log_action(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        logger = self.parent.logger if hasattr(self, 'parent') else self.logger
        
        # Log the start of the action
        action_name = func.__name__
        logger.log(logging.INFO, f"Starting action: {action_name}", 
                  action=action_name, 
                  args=str(args), 
                  kwargs=str(kwargs))
        
        try:
            result = func(self, *args, **kwargs)
            # Log successful completion
            logger.log(logging.INFO, f"Successfully completed: {action_name}",
                      action=action_name,
                      status="success")
            return result
        except Exception as e:
            # Log error
            logger.log(logging.ERROR, f"Error in {action_name}: {str(e)}",
                      action=action_name,
                      status="error",
                      error=str(e),
                      error_type=type(e).__name__)
            raise
    
    return wrapper
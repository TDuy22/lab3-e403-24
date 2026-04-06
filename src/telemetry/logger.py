import logging
import json
import os
from datetime import datetime
from typing import Any, Dict

class IndustryLogger:
    """
    Structured logger that simulates industry practices.
    Logs to both console and a file in JSON format.
    """
    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        # Resolve log directory to an absolute path so logs are written inside the repo
        # regardless of the current working directory (Streamlit/CLI can differ).
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        resolved_dir = os.getenv("LOG_DIR", log_dir).strip() or "logs"
        if not os.path.isabs(resolved_dir):
            resolved_dir = os.path.join(repo_root, resolved_dir)

        os.makedirs(resolved_dir, exist_ok=True)

        # Avoid duplicate handlers if this module is imported multiple times.
        if self.logger.handlers:
            return

        # File Handler (JSON lines)
        log_file = os.path.join(resolved_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Keep raw JSON on both sinks (one line per event)
        formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Logs an event with a timestamp and type."""
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        }
        self.logger.info(json.dumps(payload))

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str, exc_info=True):
        self.logger.error(msg, exc_info=exc_info)

# Global logger instance
logger = IndustryLogger()

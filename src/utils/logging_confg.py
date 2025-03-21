import logging
import os
from dotenv import load_dotenv

load_dotenv()
LOG_FILE = os.getenv('LOG_FILE', 'websearchbuddy.log')


def configure_logging():
    """Configure logging for the application with UTF-8 encoding."""
    handlers = [
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s[%(levelname)s]%(name)s - %(message)s',
        handlers=handlers,
    )
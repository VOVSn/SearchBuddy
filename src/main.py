import logging
import os
import sys

from telegram.ext import Application

from constants import TELEGRAM_BOT_TOKEN, CHAT_DIR
from handlers.message_handler import message_handler
from handlers.start_handler import start_handler
from handlers.delete_handler import delete_handler
from handlers.model_handler import model_handler
from handlers.error_handler import error_handler
from handlers.research_handler import research_handler
from utils.logging_confg import configure_logging


HANDLERS = [
    start_handler,
    delete_handler,
    model_handler,
    message_handler,
    research_handler,
]


def main():
    """Initialize and run the Telegram bot application."""
    try:
        configure_logging()
        logging.info('Starting the Telegram bot application')
        # if not os.path.exists(CHAT_DIR):
        #     os.makedirs(CHAT_DIR)
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handlers(HANDLERS)
        app.add_error_handler(error_handler)
        print('WEBsearch Buddy is ready...')

        app.run_polling()
        return 0  # Success
    except Exception as e:
        logging.error(f'Failed to start bot: {e}', exc_info=True)
        return 1  # Failure


if __name__ == '__main__':
    sys.exit(main())
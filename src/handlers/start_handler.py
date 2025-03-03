from telegram import Update
from telegram.ext import ContextTypes, CommandHandler


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command with a welcome message."""
    welcome_message = (
        'Hey! I’m WebSearchBuddy, your assistant for answering '
        'questions and searching the web.\n\n'
        'What I can do:\n'
        '- Answer your questions directly\n'
        '- Search the web and summarize the results\n\n'
        'Available commands:\n'
        '/start - Show this message\n'
        '/delete - Clear your local chat history\n'
        '/model - Check the current Ollama model\n\n'
        'Just ask me anything to get started!'
    )
    await update.message.reply_text(welcome_message)


start_handler = CommandHandler('start', start)
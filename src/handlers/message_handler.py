import json
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from constants import (
    MAX_HISTORY, AGENT_PRECONTEXT, CHAT_DIR,
    SUMMARIZE_SEARCH_PROMPT_TEMPLATE, TELEGRAM_MAX_MESSAGE_LENGTH
)
from utils.ollama_utils import ollama_generate, analyze_prompt
from utils.search_utils import perform_search


def save_conversation(conversation, chat_file, max_history=MAX_HISTORY):
    """Save conversation to JSON file, truncating if over max_history."""
    if len(conversation) > max_history:
        conversation = conversation[-max_history:]
    with open(chat_file, 'w') as f:
        json.dump(conversation, f, indent=2)


async def send_in_chunks(reply_func, text, chunk_size=TELEGRAM_MAX_MESSAGE_LENGTH):
    """Send long text in chunks smaller than chunk_size."""
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        await reply_func(chunk)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages from users."""
    user_id = update.message.from_user.id
    chat_file = os.path.join(CHAT_DIR, f'{user_id}.json')
    if os.path.exists(chat_file):
        with open(chat_file, 'r') as f:
            conversation = json.load(f)
    else:
        conversation = []
    user_message = update.message.text
    category = analyze_prompt(user_message)

    async def reply_and_log(message):
        conversation.append(f'agent: {message}')
        save_conversation(conversation, chat_file)
        await send_in_chunks(update.message.reply_text, message)

    if category == 1:
        conversation.append(f'user: {user_message}')
        save_conversation(conversation, chat_file)
        try:
            history_str = '\n'.join(conversation)
            prompt = f'{AGENT_PRECONTEXT}\n{history_str}\nagent:'
            response = ollama_generate(prompt)
            agent_response = response.get('response', '').strip()
            await reply_and_log(agent_response)
        except Exception as e:
            logging.error(f'Failed to process with Ollama: {str(e)}')
            await reply_and_log('Sorry, I couldn’t process that due to an error.')
    elif category == 2:
        try:
            await reply_and_log('Need to search the web')
            search_results = perform_search(user_message)
            if search_results and search_results != 'Failed to retrieve search results.':
                prompt = SUMMARIZE_SEARCH_PROMPT_TEMPLATE.format(
                    user_query=user_message,
                    search_results=search_results
                )
                response = ollama_generate(prompt)
                summary = response.get('response', '').strip()
                await reply_and_log(summary)
            else:
                await reply_and_log('No search results found.')
        except Exception as e:
            logging.error(f'Failed to perform search or summarize: {str(e)}')
            await reply_and_log('Sorry, I couldn’t perform the search right now.')
    else:
        await reply_and_log('Sorry, I don’t understand that request.')


message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
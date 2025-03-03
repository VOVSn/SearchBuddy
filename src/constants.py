import os

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAT_DIR = os.path.join(BASE_DIR, 'chats/')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your-telegram-bot-token')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'granite3.2:2b')
OLLAMA_API_URL = f'{OLLAMA_HOST}/api/generate'
SEARCH_API_URL = os.getenv('SEARCH_API_URL', 'https://google.com')
NUM_SEARCH_RESULTS = 15

MAX_HISTORY = 20
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


AGENT_PRECONTEXT = (
    'You are AI agent WebSearchBuddy, an intelligent agent '
    'that can answer questions directly or search the web.'
)

ANALYZE_PROMPT_TEMPLATE = (
    'Analyze the user\'s prompt:\n"{prompt}"\n'
    '1. Can be answered directly by AI, like small talk or theoretical discussion\n'
    '2. Requires searching the web for information'
    'If the question refers to some current events or "сейчас, недавно", '
    'Or the user is asking something you dont know\n'
    'This is definitely 2 - we need to search\n'
    'Return only a single digit, no explanation, choose: (1 or 2)'
)

REFINE_SEARCH_QUERY_TEMPLATE = (
    'Based on the conversation context and the user\'s latest query, '
    'generate a concise and accurate web search query (max 10 words). '
    'Correct any errors in the user\'s query and make it clear and precise. '
    'Conversation context:\n{context}\n'
    'User\'s latest query:\n{user_query}\n'
    'Output only the refined search query, no explanations, just search query.'
)


SUMMARIZE_SEARCH_PROMPT_TEMPLATE = (
    'Based on the following search results, provide a detailed '
    'summary answering the user\'s query: "{user_query}"\n\n'
    'Search Results:\n{search_results}\n\n'
    'If user\'s query is in russian, make summary in russian'
    'Summary:'
)
import os

from dotenv import load_dotenv


load_dotenv()

# Directories and filenames
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAT_DIR = os.path.join(BASE_DIR, 'chats/')
os.makedirs(CHAT_DIR, exist_ok=True)
RESEARCH_DIR = os.path.join(BASE_DIR, 'research/')
os.makedirs(RESEARCH_DIR, exist_ok=True)
RESEARCH_LOG_DIR = os.path.join(RESEARCH_DIR, 'logs/')
os.makedirs(RESEARCH_LOG_DIR, exist_ok=True)
RESEARCH_TXT_DIR = os.path.join(RESEARCH_DIR, 'txt/')
os.makedirs(RESEARCH_TXT_DIR, exist_ok=True)
RESEARCH_JSON_FILE = os.path.join(RESEARCH_DIR, 'research_task.json')

# Environment:
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your-telegram-bot-token')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'granite3.2:2b')
POWER_USERS = os.getenv('POWER_USERS','1234567890')
OLLAMA_API_URL = f'{OLLAMA_HOST}/api/generate'
SEARCH_API_URL = os.getenv('SEARCH_API_URL', 'https://yourdomain.com/search')

# Text and chat constants:
MAX_HISTORY = 20
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'Arial.ttf')
GENERATE_TXT = True
GENERATE_PDF = True

# Search constants:
NUM_SEARCH_RESULTS = 15

# Research-specific constants:
MAX_BATCH_ITERATIONS = 5
MAX_RESEARCH_STEPS = 2
MAX_QUERIES_PER_BATCH = 5
NUM_RESEARCH_URLS = 3  # Number of URLs to scrape per iteration
MAX_SCRAPED_CONTENT_LENGTH = 20000  # Max characters per page
SCRAPE_DELAY = 1000  # Delay between scrapes in ms
RESPECT_ROBOTS_TXT = True  # Respect robots.txt by default
SUMMARY_LENGTH = 1500  # Max characters per page summary
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
]




# NLP prompts
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
    'If user\'s query is in Russian, make summary in Russian'
    'Summary:'
)

EXPAND_USER_TASK_PROMPT_TEMPLATE = (
    'Current date: {current_date}\n'
    'User query: "{user_input}"\n'
    'Generate a concise research plan as a numbered list of steps (e.g., "1. Do X\n2. Do Y") '
    'to address the query through web searches. '
    # 'Focus on actionable steps, ending with "Summarize findings". '
    'Keep it in the same language as the input.'
)

NEXT_QUERY_PROMPT_TEMPLATE = (
    'Current date: {current_date}\n'
    'Based on the research task:\n'
    'Plan: {plan}\n'
    'Previous steps and results: {steps}\n'
    'Current position: Step {step_number}\n'
    'Generate a concise web search query (max 10 words) in quotes (e.g., "search term").\n'
    'Focus on missing data and prioritize recent info (last 1-2 years) if relevant to {current_date}.\n'
    'If the task is complete, return "complete" in quotes.\n'
    'Return only the quoted query, no explanations.'
)

REFINE_QUERY_PROMPT_TEMPLATE = (
    'Previous query "{query}" yielded no results.\n'
    'Generate a refined query to address the same step (max 10 words).'
)

SUMMARIZE_STEP_PROMPT_TEMPLATE = (
    'Summarize the following full webpage content for the query "{query}":\n'
    '{raw_content}\n'
    'Provide a concise summary (max {summary_length} characters) in the same '
    'language as the query, focusing on key insights relevant to the query.'
)

SUMMARIZE_RESEARCH_PROMPT_TEMPLATE = (
    'Summarize the following research task:\n'
    'Initial query: {initial_query}\n'
    'Plan: {plan}\n'  # Replace expanded_query with plan
    'Iterations: {steps}\n'
    'Provide a comprehensive summary in the same language as the query.'
)

INITIAL_BATCH_QUERIES_PROMPT_TEMPLATE = (
    'Current date: {current_date}\n'
    'Initial query: "{initial_query}"\n'
    'Plan: "{plan}"\n'
    'Generate a list of up to {max_queries} web search queries in JSON format '
    '(e.g., ["query1", "query2"]) based on the plan to gather relevant information.'
)

NEXT_BATCH_QUERIES_PROMPT_TEMPLATE = (
    'Current date: {current_date}\n'
    'Initial query: "{initial_query}"\n'
    'Plan: "{plan}"\n'
    'Previous iterations: {iterations_json}\n'
    'Generate a list of up to {max_queries} web search queries in JSON format '
    '(e.g., ["query1", "query2"]) based on the plan and previous results to continue the research.'
)

COMPLETION_CHECK_PROMPT_TEMPLATE = (
    'Current date: {current_date}\n'
    'Initial query: "{initial_query}"\n'
    'Plan: "{plan}"\n'
    'Iterations: {iterations_json}\n'
    'Is the task complete? Return "1" or "2" followed by a brief reason '
    '(e.g., "1. More data needed" or "2. Sufficient info gathered").'
)

CONCLUSION_PROMPT_TEMPLATE = (
    'Current date: {current_date}\n'
    'Initial query: "{initial_query}"\n'
    'Plan: "{plan}"\n'
    'Iterations: {iterations_json}\n'
    'Final summary: "{final_summary}"\n'
    'Write a concise, scientific conclusion addressing the query. Highlight key '
    'insights, implications, and potential further research. Include your '
    'analytical thoughts on the topic.'
)
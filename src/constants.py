import os

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAT_DIR = os.path.join(BASE_DIR, 'chats/')
RESEARCH_DIR = os.path.join(BASE_DIR, 'research/')
RESEARCH_JSON_FILE = os.path.join(RESEARCH_DIR, 'research_task.json')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your-telegram-bot-token')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'granite3.2:2b')
POWER_USERS = os.getenv('POWER_USERS','1234567890')
OLLAMA_API_URL = f'{OLLAMA_HOST}/api/generate'
SEARCH_API_URL = os.getenv('SEARCH_API_URL', 'https://google.com')
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'Arial.ttf')

NUM_SEARCH_RESULTS = 15
MAX_RESEARCH_STEPS = 5
MAX_BATCH_ITERATIONS = 5
MAX_QUERIES_PER_BATCH = 10

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

EXPAND_USER_TASK_PROMPT_TEMPLATE = (
    'Current date: {current_date}\n'
    'User query: "{user_input}"\n'
    'Generate a concise research plan as a numbered list of steps (e.g., "1. Do X\n2. Do Y") '
    'to address the query through web searches. '
    'Focus on actionable steps, ending with "Summarize findings". '
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
    'Summarize the following search results for the query "{query}":\n'
    '{raw_results}\n'
    'Provide a concise summary in the same language as the query.'
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
    'Write a concise conclusion (not a summary) addressing the query, '
    'highlighting key insights, implications, or final judgments based on the research.'
)
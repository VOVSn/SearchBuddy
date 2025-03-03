import requests
import logging
from constants import OLLAMA_API_URL, OLLAMA_MODEL, ANALYZE_PROMPT_TEMPLATE, REFINE_SEARCH_QUERY_TEMPLATE


def ollama_generate(prompt):
    """Generate a response using the Ollama API."""
    logging.info(f'Ollama Prompt: {prompt}')
    payload = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False,
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        logging.info(f'Ollama Response: {result}')
        return result
    except requests.RequestException as e:
        logging.error(f'Ollama API error: {str(e)}')
        raise


def analyze_prompt(prompt, conversation=None):
    """Analyze the user's prompt to determine its category, including conversation context."""
    # Prepare conversation context (last 3 messages or fewer if not available)
    context = ""
    if conversation:
        # Filter to last 3 messages, prioritizing most recent
        recent_messages = conversation[-3:] if len(conversation) > 3 else conversation
        context = "\n".join(recent_messages)
    full_prompt = f"Conversation context:\n{context}\n\nUser's latest prompt:\n{prompt}"
    analysis_prompt = ANALYZE_PROMPT_TEMPLATE.format(prompt=full_prompt)
    response = ollama_generate(analysis_prompt)
    response_text = response.get('response', '2').strip()
    if response_text and response_text[0].isdigit():
        return int(response_text[0])
    logging.error(f'Unexpected response format: {response_text}')
    return 2  # Default to search if unclear


def refine_search_query(user_query, conversation=None):
    """Use Ollama to refine the user's query into an effective web search query."""
    # Prepare conversation context (last 3 messages or fewer if not available)
    context = ""
    if conversation:
        recent_messages = conversation[-3:] if len(conversation) > 3 else conversation
        context = "\n".join(recent_messages)
    prompt = REFINE_SEARCH_QUERY_TEMPLATE.format(context=context, user_query=user_query)
    response = ollama_generate(prompt)
    refined_query = response.get('response', user_query).strip()
    return refined_query if refined_query else user_query
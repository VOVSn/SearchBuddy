import requests
import logging
from constants import OLLAMA_API_URL, OLLAMA_MODEL, ANALYZE_PROMPT_TEMPLATE


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


def analyze_prompt(prompt):
    """Analyze the user's prompt to determine its category."""
    analysis_prompt = ANALYZE_PROMPT_TEMPLATE.format(prompt=prompt)
    response = ollama_generate(analysis_prompt)
    response_text = response.get('response', '2').strip()
    if response_text and response_text[0].isdigit():
        return int(response_text[0])
    logging.error(f'Unexpected response format: {response_text}')
    return 2  # Default to search if unclear
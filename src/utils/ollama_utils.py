import json
import re
import requests
import logging

from constants import (
    MAX_QUERIES_PER_BATCH,
    OLLAMA_API_URL,
    OLLAMA_MODEL,
)
from utils.prompts import (
    ANALYZE_PROMPT_TEMPLATE,
    EXPAND_USER_TASK_PROMPT_TEMPLATE,
    NEXT_QUERY_PROMPT_TEMPLATE,
    REFINE_QUERY_PROMPT_TEMPLATE,
    REFINE_SEARCH_QUERY_TEMPLATE,
    SUMMARIZE_RESEARCH_PROMPT_TEMPLATE,
    SUMMARIZE_STEP_PROMPT_TEMPLATE,
)

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

def generate_plan(user_input, current_date):
    """Generate a research plan using Ollama."""
    prompt = EXPAND_USER_TASK_PROMPT_TEMPLATE.format(user_input=user_input, current_date=current_date)
    response = ollama_generate(prompt)
    plan = response.get('response', '').strip()
    return plan

def generate_next_query(plan, steps, step_number, current_date):
    """Generate the next web search query using Ollama."""
    steps_json = json.dumps(steps, indent=2)
    prompt = NEXT_QUERY_PROMPT_TEMPLATE.format(
        plan=plan, steps=steps_json, step_number=step_number, current_date=current_date
    )
    response = ollama_generate(prompt)
    next_query = response.get('response', '').strip()
    match = re.search(r'"([^"]*)"', next_query)
    return match.group(1) if match else next_query

def refine_query(query):
    """Refine the query if no results were found."""
    prompt = REFINE_QUERY_PROMPT_TEMPLATE.format(query=query)
    response = ollama_generate(prompt)
    refined_query = response.get('response', '').strip()
    return refined_query

def summarize_step(query, raw_results):
    """Summarize the raw search results for a step."""
    prompt = SUMMARIZE_STEP_PROMPT_TEMPLATE.format(query=query, raw_results=raw_results)
    response = ollama_generate(prompt)
    summary = response.get('response', '').strip()
    return summary

def summarize_research(initial_query, expanded_query, steps):
    """Summarize the entire research task."""
    steps_json = json.dumps(steps, indent=2)
    prompt = SUMMARIZE_RESEARCH_PROMPT_TEMPLATE.format(
        initial_query=initial_query, expanded_query=expanded_query, steps=steps_json
    )
    response = ollama_generate(prompt)
    summary = response.get('response', '').strip()
    return summary


def generate_batch_queries(prompt):
    """Generate batch queries from prompt, extracting valid queries from mixed output."""
    response = ollama_generate(prompt)
    raw_queries = response.get('response', '').strip()
    logger = logging.getLogger(__name__)

    if not raw_queries:
        logger.warning('No queries returned from Ollama.')
        return []

    # Try to extract a JSON-like block if present
    json_match = re.search(r'$$ .*? $$', raw_queries, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        try:
            queries = json.loads(json_str)
            # Clean each query: remove quotes, commas, and whitespace
            valid_queries = [
                re.sub(r'["\',]', '', str(q)).strip()
                for q in queries
                if q and str(q).strip() and str(q).strip() not in ('\\', '') and not str(q).strip().startswith('site:')
            ]
            if len(valid_queries) < len(queries):
                logger.warning(f'Filtered invalid JSON queries: {set(queries) - set(valid_queries)}')
            return valid_queries[:MAX_QUERIES_PER_BATCH]
        except json.JSONDecodeError as e:
            logger.warning(f'Failed to parse JSON block: {e}, falling back to line-by-line parsing. Raw: {json_str}')

    # Fallback to line-by-line parsing if no valid JSON block
    lines = raw_queries.split('\n')
    valid_queries = []
    in_query_block = False

    for line in lines:
        line = line.strip()
        # Detect start of query block (JSON or list-like structure)
        if line.startswith('```json'):
            in_query_block = True
            continue
        if line.startswith('```') and in_query_block:
            in_query_block = False
            continue
        if line in ('[', ']') or not line:
            continue
        # Skip preamble text before queries
        if not in_query_block and any(keyword in line.lower() for keyword in [
            'to gather', 'follow these', 'search queries', 'based on', 'suggested', 'here are'
        ]):
            continue
        # Clean and validate query
        cleaned_query = re.sub(r'["\',]', '', line).strip()
        if (cleaned_query and cleaned_query not in ('\\', '') and
                not cleaned_query.startswith('site:') and not cleaned_query.startswith('`')):
            valid_queries.append(cleaned_query)

    if not valid_queries:
        logger.error(f'No valid queries parsed from response: {raw_queries}')
    elif len(valid_queries) < len(lines):
        logger.warning(f'Filtered invalid queries from lines: {set(lines) - set(valid_queries)}')

    return valid_queries[:MAX_QUERIES_PER_BATCH]

def check_completion(prompt):
    """Check if research is complete, fallback to 2 if parsing fails."""
    response = ollama_generate(prompt)
    complete_response = response.get('response', '2').strip()
    try:
        decision = int(complete_response[0])
        return complete_response
    except (ValueError, IndexError):
        logger = logging.getLogger(__name__)
        logger.warning(f'Failed to parse completion: {complete_response}, defaulting to 2')
        return '2. Assumed complete due to parsing failure.'
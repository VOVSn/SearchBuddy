import json
import re
import requests
import logging

from constants import (
    ANALYZE_PROMPT_TEMPLATE, REFINE_SEARCH_QUERY_TEMPLATE,
    OLLAMA_API_URL, OLLAMA_MODEL, EXPAND_USER_TASK_PROMPT_TEMPLATE,
    NEXT_QUERY_PROMPT_TEMPLATE, REFINE_QUERY_PROMPT_TEMPLATE,
    SUMMARIZE_STEP_PROMPT_TEMPLATE, SUMMARIZE_RESEARCH_PROMPT_TEMPLATE,
    MAX_QUERIES_PER_BATCH
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
    """Generate a batch of web search queries using Ollama."""
    response = ollama_generate(prompt)
    query_text = response.get('response', '').strip()
    try:
        queries = json.loads(query_text)
        if isinstance(queries, list):
            return queries[:MAX_QUERIES_PER_BATCH]  # Cap at 10
    except json.JSONDecodeError:
        queries = re.findall(r'"([^"]*)"', query_text)
        return queries[:MAX_QUERIES_PER_BATCH] if queries else []  # Cap at 10
    return []

def check_completion(prompt):
    """Check if the research task is complete using Ollama."""
    response = ollama_generate(prompt)
    complete_text = response.get('response', '2. Unknown reason').strip()
    return complete_text
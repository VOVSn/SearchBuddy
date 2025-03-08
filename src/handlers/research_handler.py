import os
import json
import uuid
import asyncio
import logging
import re
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from transliterate import translit

from constants import (
    RESEARCH_JSON_FILE,
    MAX_BATCH_ITERATIONS,
    POWER_USERS,
    RESEARCH_LOG_DIR,
    MAX_QUERIES_PER_BATCH,
    SUMMARY_LENGTH,
)
from utils.ollama_utils import (
    generate_plan,
    generate_batch_queries,
    check_completion,
    ollama_generate,
)
from utils.pdf_utils import generate_pdf
from utils.prompts import (
    INITIAL_BATCH_QUERIES_PROMPT_TEMPLATE,
    NEXT_BATCH_QUERIES_PROMPT_TEMPLATE,
    COMPLETION_CHECK_PROMPT_TEMPLATE,
    SUMMARIZE_STEP_PROMPT_TEMPLATE,
    SUMMARIZE_RESEARCH_PROMPT_TEMPLATE,
)
from utils.search_utils import perform_research_search


def sanitize_filename(query):
    """Convert query to snake_case filename with transliteration."""
    try:
        # Transliterate non-Latin (e.g., Cyrillic) to Latin
        sanitized = translit(query, 'ru', reversed=True).lower()
    except Exception:
        # Fallback if transliteration fails
        sanitized = query.lower()
    # Keep only alphanumeric chars and spaces, replace spaces with underscores
    sanitized = re.sub(r'[^a-z0-9\s]', '', sanitized).strip()
    return '_'.join(word for word in sanitized.split() if word)

def get_unique_filename(base_name, directory, extension):
    """Generate a unique filename with counter if needed."""
    filename = f'research_{base_name}{extension}'
    filepath = os.path.join(directory, filename)
    counter = 1
    while os.path.exists(filepath):
        filename = f'research_{base_name}_{counter:03d}{extension}'
        filepath = os.path.join(directory, filename)
        counter += 1
    return filepath


async def research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /research command."""
    user_id = str(update.message.from_user.id)
    if user_id not in POWER_USERS.split(','):
        await update.message.reply_text('Permission denied.')
        return

    if os.path.exists(RESEARCH_JSON_FILE):
        await update.message.reply_text('Research task already in progress.')
        return

    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text('Please provide a query.')
        return

    research_id = str(uuid.uuid4())  # Keep UUID internally
    current_date = datetime.now().strftime('%Y-%m-%d')
    plan = generate_plan(query, current_date)
    base_name = sanitize_filename(query)

    # Setup logging with query-based filename
    log_file = get_unique_filename(base_name, RESEARCH_LOG_DIR, '.log')
    logger = logging.getLogger(research_id)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(handler)

    task_state = {
        'research_id': research_id,
        'user_id': user_id,
        'current_date': current_date,
        'initial_user_query': query,
        'plan': plan,
        'iterations': [],
        'next_queries': [],
        'complete_status': None,
        'final_summary': None,
        'status': 'pending',
        'used_urls': [],
        'base_name': base_name
    }

    prompt = INITIAL_BATCH_QUERIES_PROMPT_TEMPLATE.format(
        current_date=current_date,
        initial_query=query,
        plan=plan,
        max_queries=MAX_QUERIES_PER_BATCH
    )
    task_state['next_queries'] = generate_batch_queries(prompt)
    save_task_state(task_state)

    await update.message.reply_text('Starting research task...')
    context.user_data['current_task_id'] = research_id
    asyncio.create_task(run_research_task(update, context, task_state, logger))

async def run_research_task(update: Update, context, task_state, logger):
    """Run the research task with scraping."""
    try:
        iteration_number = 1
        while iteration_number <= MAX_BATCH_ITERATIONS:
            queries = task_state['next_queries']
            if not queries:
                logger.info(f'Iteration {iteration_number}: No queries generated.')
                await update.message.reply_text(f'Iteration {iteration_number}: No queries.')
                break

            await update.message.reply_text('Searching...')
            logger.info(f'Iteration {iteration_number}: Searching {len(queries)} queries')
            batch_results = []
            for query in queries:
                logger.info(f'Searching: "{query}"')
                results = await perform_research_search(query, logger)
                if not results:
                    logger.warning(f'No results for query: {query}')
                    continue

                for result in results:
                    content = result['content']
                    prompt = SUMMARIZE_STEP_PROMPT_TEMPLATE.format(
                        query=query,
                        raw_content=content,
                        summary_length=SUMMARY_LENGTH
                    )
                    summary = ollama_generate(prompt).get('response', '').strip()
                    batch_results.append({
                        'query': query,
                        'url': result['url'],
                        'title': result['title'],
                        'summary': summary
                    })
                    task_state['used_urls'].append(result['url'])

            if not batch_results:
                logger.error('No valid results in batch.')
                raise Exception('No data retrieved for iteration.')

            await update.message.reply_text('Summarizing...')
            batch_summary_prompt = SUMMARIZE_STEP_PROMPT_TEMPLATE.format(
                query='batch queries',
                raw_content=json.dumps([r['summary'] for r in batch_results], indent=2),
                summary_length=SUMMARY_LENGTH * 2
            )
            batch_summary = ollama_generate(batch_summary_prompt).get('response', '').strip()

            task_state['iterations'].append({
                'iteration_number': iteration_number,
                'queries': batch_results,
                'summary': batch_summary
            })
            save_task_state(task_state)

            iterations_json = json.dumps(task_state['iterations'], indent=2)
            prompt = COMPLETION_CHECK_PROMPT_TEMPLATE.format(
                current_date=task_state['current_date'],
                initial_query=task_state['initial_user_query'],
                plan=task_state['plan'],
                iterations_json=iterations_json
            )
            complete_response = check_completion(prompt)
            task_state['complete_status'] = complete_response
            decision = int(complete_response[0])

            if decision == 2 or iteration_number == MAX_BATCH_ITERATIONS:
                if iteration_number == MAX_BATCH_ITERATIONS:
                    await update.message.reply_text('Max iterations reached.')
                break

            prompt = NEXT_BATCH_QUERIES_PROMPT_TEMPLATE.format(
                current_date=task_state['current_date'],
                initial_query=task_state['initial_user_query'],
                plan=task_state['plan'],
                iterations_json=iterations_json,
                max_queries=MAX_QUERIES_PER_BATCH
            )
            task_state['next_queries'] = generate_batch_queries(prompt)
            save_task_state(task_state)
            iteration_number += 1

        await update.message.reply_text('Making conclusion...')
        iterations_json = json.dumps(task_state['iterations'], indent=2)
        final_prompt = SUMMARIZE_RESEARCH_PROMPT_TEMPLATE.format(
            initial_query=task_state['initial_user_query'],
            plan=task_state['plan'],
            steps=iterations_json
        )
        task_state['final_summary'] = ollama_generate(final_prompt).get('response', '').strip()
        task_state['status'] = 'complete'
        save_task_state(task_state)

        await update.message.reply_text('Generating files...')
        pdf_file, txt_file = generate_pdf(task_state)
        if pdf_file:
            with open(pdf_file, 'rb') as pdf:
                await update.message.reply_document(pdf, caption='Research complete (PDF)')
        if txt_file:
            with open(txt_file, 'rb') as txt:
                await update.message.reply_document(txt, caption='Research raw text')

    except Exception as e:
        logger.error(f'Fatal error: {e}')
        await update.message.reply_text('Error during research, see logs.')
        with open(logger.handlers[0].baseFilename, 'rb') as log_file:
            await update.message.reply_document(log_file, caption='Research log')
    finally:
        if 'current_task_id' in context.user_data:
            del context.user_data['current_task_id']
        archive_completed_task()
        logger.handlers[0].close()
        logger.removeHandler(logger.handlers[0])

def save_task_state(state):
    """Save task state to JSON."""
    with open(RESEARCH_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def archive_completed_task():
    """Archive completed task JSON."""
    if os.path.exists(RESEARCH_JSON_FILE):
        i = 1
        while os.path.exists(f'{RESEARCH_JSON_FILE}.{i:03d}'):
            i += 1
        os.rename(RESEARCH_JSON_FILE, f'{RESEARCH_JSON_FILE}.{i:03d}')

research_handler = CommandHandler('research', research)
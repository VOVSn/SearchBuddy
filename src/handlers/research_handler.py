import os
import json
import uuid
import asyncio
import re
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from constants import (
    RESEARCH_JSON_FILE, MAX_BATCH_ITERATIONS, POWER_USERS,
    INITIAL_BATCH_QUERIES_PROMPT_TEMPLATE, NEXT_BATCH_QUERIES_PROMPT_TEMPLATE,
    COMPLETION_CHECK_PROMPT_TEMPLATE, SUMMARIZE_STEP_PROMPT_TEMPLATE, MAX_QUERIES_PER_BATCH,
    SUMMARIZE_RESEARCH_PROMPT_TEMPLATE
)
from utils.ollama_utils import (
    generate_plan, generate_batch_queries, check_completion, ollama_generate
)
from utils.search_utils import perform_search
from utils.pdf_utils import generate_pdf


def parse_plan(plan):
    """Parse the plan string into a list of numbered steps."""
    # Split by lines and filter for numbered steps (e.g., "1. Do X")
    steps = [line.strip() for line in plan.split('\n') if re.match(r'^\d+\.\s', line)]
    return steps


async def research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /research command to start a research task."""
    user_id = str(update.message.from_user.id)
    if user_id not in POWER_USERS.split(','):
        await update.message.reply_text('You do not have permission to use this command.')
        return

    if os.path.exists(RESEARCH_JSON_FILE):
        await update.message.reply_text('A research task is already in progress.')
        return

    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text('Please provide a query.')
        return

    research_id = str(uuid.uuid4())
    current_date = datetime.now().strftime('%Y-%m-%d')
    plan = generate_plan(query, current_date)  # Only generate plan

    task_state = {
        'research_id': research_id,
        'user_id': user_id,
        'current_date': current_date,
        'initial_user_query': query,
        'plan': plan,  # Single field for the plan
        'iterations': [],
        'next_queries': [],
        'complete_status': None,
        'final_summary': None,
        'status': 'pending'
    }

    # Generate first batch of queries
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
    asyncio.create_task(run_research_task(update, context, task_state))

async def run_research_task(update: Update, context, task_state):
    """Run the research task in the background with batch iterations."""
    try:
        iteration_number = 1
        while iteration_number <= MAX_BATCH_ITERATIONS:
            # Batch search
            queries = task_state['next_queries']
            if not queries:
                await update.message.reply_text(f'Iteration {iteration_number}: No queries generated.')
                break

            await update.message.reply_text(f'Iteration {iteration_number}: Searching {len(queries)} queries...')
            batch_results = []
            for query in queries:
                await update.message.reply_text(f'Searching: "{query}"')
                raw_results = perform_search(query)
                if not raw_results or raw_results == 'Failed to retrieve search results.':
                    raw_results = 'No results found.'
                batch_results.append({'query': query, 'raw_results': raw_results})

            # Summarize batch
            batch_json = json.dumps(batch_results, indent=2)
            prompt = SUMMARIZE_STEP_PROMPT_TEMPLATE.format(query='batch queries', raw_results=batch_json)
            batch_summary = ollama_generate(prompt).get('response', '').strip()

            task_state['iterations'].append({
                'iteration_number': iteration_number,
                'queries': batch_results,
                'summary': batch_summary
            })
            save_task_state(task_state)

            # Check completion
            iterations_json = json.dumps(task_state['iterations'], indent=2)
            prompt = COMPLETION_CHECK_PROMPT_TEMPLATE.format(
                current_date=task_state['current_date'],
                initial_query=task_state['initial_user_query'],
                plan=task_state['plan'],
                iterations_json=iterations_json
            )
            complete_response = check_completion(prompt)
            task_state['complete_status'] = complete_response
            decision = int(complete_response[0])  # Parse first digit (1 or 2)

            if decision == 2 or iteration_number == MAX_BATCH_ITERATIONS:
                if iteration_number == MAX_BATCH_ITERATIONS:
                    await update.message.reply_text('Max iterations reached.')
                break

            # Generate next batch if continuing
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

        # Final summary and PDF
        iterations_json = json.dumps(task_state['iterations'], indent=2)
        prompt = SUMMARIZE_RESEARCH_PROMPT_TEMPLATE.format(
            initial_query=task_state['initial_user_query'],
            plan=task_state['plan'],  # Use plan instead of expanded_query
            steps=iterations_json
        )
        task_state['final_summary'] = ollama_generate(prompt).get('response', '').strip()
        task_state['status'] = 'complete'
        save_task_state(task_state)

        pdf_file = generate_pdf(task_state)
        await update.message.reply_document(open(pdf_file, 'rb'), caption='Research complete!')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')
    finally:
        if 'current_task_id' in context.user_data:
            del context.user_data['current_task_id']
        archive_completed_task()

def save_task_state(state):
    """Save the task state to the JSON file."""
    with open(RESEARCH_JSON_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def archive_completed_task():
    """Archive the completed task JSON file."""
    if os.path.exists(RESEARCH_JSON_FILE):
        i = 1
        while os.path.exists(f'{RESEARCH_JSON_FILE}.{i:03d}'):
            i += 1
        os.rename(RESEARCH_JSON_FILE, f'{RESEARCH_JSON_FILE}.{i:03d}')

research_handler = CommandHandler('research', research)
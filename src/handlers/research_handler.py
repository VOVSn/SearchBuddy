import os
import json
import uuid
import asyncio
import re
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from constants import RESEARCH_JSON_FILE, MAX_RESEARCH_STEPS, POWER_USERS
from utils.ollama_utils import (
    generate_plan, generate_next_query, refine_query, summarize_step, summarize_research
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
    current_date = datetime.now().strftime('%Y-%m-%d')  # Set today's date (e.g., "2025-03-03")
    expanded_query = generate_plan(query, current_date)  # Pass current_date
    plan = expanded_query
    plan_steps = parse_plan(plan)

    task_state = {
        'research_id': research_id,
        'user_id': user_id,
        'current_date': current_date,  # Add current date to JSON
        'initial_user_query': query,
        'expanded_user_query': expanded_query,
        'plan': plan,
        'steps': [],
        'next_query': '',
        'summary': None,
        'status': 'pending'
    }
    save_task_state(task_state)

    await update.message.reply_text('Starting research task...')
    context.user_data['current_task_id'] = research_id
    asyncio.create_task(run_research_task(update, context, task_state, plan_steps))

async def run_research_task(update: Update, context, task_state, plan_steps):
    """Run the research task in the background."""
    try:
        step_number = 1
        while True:
            if len(task_state['steps']) >= MAX_RESEARCH_STEPS:
                task_state['next_query'] = 'complete'
                await update.message.reply_text('Max steps reached. Summarizing...')
                break

            if step_number <= len(plan_steps):
                step_desc = plan_steps[step_number - 1]
            else:
                step_desc = 'Additional step based on previous results'

            next_query = generate_next_query(
                task_state['plan'], task_state['steps'], step_number, task_state['current_date']
            )
            task_state['next_query'] = next_query

            if next_query.lower() == 'complete':
                break

            await update.message.reply_text(f'Doing step {step_number}: {next_query}')

            raw_results = perform_search(next_query)
            if not raw_results or raw_results == 'Failed to retrieve search results.':
                for _ in range(2):
                    next_query = refine_query(next_query)
                    await update.message.reply_text(f'Refining query: {next_query}')
                    raw_results = perform_search(next_query)
                    if raw_results and raw_results != 'Failed to retrieve search results.':
                        break
                else:
                    raw_results = 'No results found after retries.'

            summary = summarize_step(next_query, raw_results)

            task_state['steps'].append({
                'step_number': step_number,
                'description': step_desc,
                'query': next_query,
                'raw_results': raw_results,
                'summary': summary
            })
            save_task_state(task_state)
            step_number += 1

        task_state['summary'] = summarize_research(
            task_state['initial_user_query'],
            task_state['expanded_user_query'],
            task_state['steps']
        )
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
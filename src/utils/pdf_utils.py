import json
import re
from fpdf import FPDF
from constants import (
    RESEARCH_DIR,
    RESEARCH_TXT_DIR,
    FONT_PATH,
    # CONCLUSION_PROMPT_TEMPLATE,
    GENERATE_TXT,
    GENERATE_PDF,
)
from utils.ollama_utils import ollama_generate
from utils.prompts import CONCLUSION_PROMPT_TEMPLATE


class ResearchPDF(FPDF):
    def __init__(self, font_path):
        super().__init__()
        self.add_font('Arial', '', font_path, uni=True)
        self.add_font('Arial', 'B', font_path, uni=True)
        self.set_font('Arial', '', 12)

    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Research Report', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        """Render body text with Markdown support."""
        lines = body.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                self.ln(5)
                continue
            if line.startswith('### ') or line.startswith('#### '):
                self.set_font('Arial', 'B', 16)
                self.multi_cell(0, 10, line[3:])
                self.ln(2)
            else:
                bold_pattern = r'\*\*(.*?)\*\*'
                parts = re.split(bold_pattern, line)
                self.set_font('Arial', '', 12)
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Bold part
                        self.set_font('Arial', 'B', 12)
                        self.write(10, part)
                    else:  # Regular part
                        self.set_font('Arial', '', 12)
                        self.write(10, part)
                self.ln()

    def add_section(self, title, body):
        self.add_page()
        self.chapter_title(title)
        self.chapter_body(body)


def save_txt(task_state, content, base_name):
    """Save raw content to TXT file."""
    from handlers.research_handler import get_unique_filename
    txt_file = get_unique_filename(base_name, RESEARCH_TXT_DIR, '.txt')
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(content)
    return txt_file

def generate_pdf(task_state):
    """Generate TXT and/or PDF report."""
    from handlers.research_handler import get_unique_filename
    base_name = task_state['base_name']

    # Raw content with Markdown
    content = (
        f'Initial Query: {task_state["initial_user_query"]}\n'
        f'Plan:\n{task_state["plan"]}\n\n'
        '### Findings\n'
    )
    for iteration in task_state['iterations']:
        content += f'Iteration {iteration["iteration_number"]}:\n_______\n'
        for q in iteration['queries']:
            content += f'\nQuery: {q["query"]}\nURL: {q["url"]}\nSummary: {q["summary"]}\n'
        content += f'Batch Summary: {iteration["summary"]}\n\n'
    content += f'### Summary\n{task_state["final_summary"]}\n\n'

    iterations_json = json.dumps(task_state['iterations'], indent=2)
    prompt = CONCLUSION_PROMPT_TEMPLATE.format(
        current_date=task_state['current_date'],
        initial_query=task_state['initial_user_query'],
        plan=task_state['plan'],
        iterations_json=iterations_json,
        final_summary=task_state['final_summary']
    )
    conclusion = ollama_generate(prompt).get('response', 'No conclusion generated.')
    content += f'### Conclusion\n{conclusion}\n\n'

    content += '### References\n' + '\n'.join(
        f'{i+1}. {url}' for i, url in enumerate(task_state['used_urls'])
    )

    # Save TXT if enabled
    txt_file = None
    if GENERATE_TXT:
        txt_file = save_txt(task_state, content, base_name)

    # Generate PDF if enabled
    pdf_file = None
    if GENERATE_PDF:
        pdf = ResearchPDF(FONT_PATH)
        pdf.set_title('Research Report')
        pdf.set_author('WebSearchBuddy')

        intro = (
            f'Initial Query: {task_state["initial_user_query"]}\n'
            f'Plan:\n{task_state["plan"]}'
        )
        pdf.add_section('Introduction', intro)

        findings = ''
        for iteration in task_state['iterations']:
            findings += f'Iteration {iteration["iteration_number"]}:\n_______\n'
            for q in iteration['queries']:
                findings += f'\nQuery: {q["query"]}\nURL: {q["url"]}\nSummary: {q["summary"]}\n'
            findings += f'Batch Summary: {iteration["summary"]}\n\n'
        pdf.add_section('Findings', findings)

        pdf.add_section('Summary', task_state['final_summary'])
        pdf.add_section('Conclusion', conclusion)

        used_resources = 'Used Resources:\n' + '\n'.join(
            f'{i+1}. {url}' for i, url in enumerate(task_state['used_urls'])
        )
        pdf.add_section('References', used_resources)

        pdf_file = get_unique_filename(base_name, RESEARCH_DIR, '.pdf')
        pdf.output(pdf_file)

    return pdf_file, txt_file
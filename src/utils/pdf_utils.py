import os
import re
import json

from fpdf import FPDF

from constants import RESEARCH_DIR, FONT_PATH, CONCLUSION_PROMPT_TEMPLATE
from utils.ollama_utils import ollama_generate

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
        self.set_font('Arial', '', 12)
        parts = re.split(r'(\*\*.*?\*\*)', body)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                self.set_font('Arial', 'B', 14)
                self.write(10, part[2:-2])
                self.set_font('Arial', '', 12)
            else:
                self.write(10, part)
        self.ln()

    def add_section(self, title, body):
        self.add_page()
        self.chapter_title(title)
        self.chapter_body(body)

def generate_pdf(task_state):
    """Generate a PDF report from the research task state."""
    pdf = ResearchPDF(FONT_PATH)
    pdf.set_title('Research Report')
    pdf.set_author('WebSearchBuddy')

    intro = (
        f"Initial Query: {task_state['initial_user_query']}\n"
        f"Plan:\n{task_state['plan']}"
    )
    pdf.add_section('Introduction', intro)

    findings = ""
    for iteration in task_state['iterations']:
        findings += f"Iteration {iteration['iteration_number']}:\n_______\n"
        for q in iteration['queries']:
            findings += f"\nQuery: {q['query']}\n\nRaw Results:\n\n{q['raw_results']}...\n"
        findings += f"Summary: {iteration['summary']}\n\n"
    pdf.add_section('Findings', findings)

    pdf.add_section('Summary', task_state['final_summary'])

    # Generate conclusion
    iterations_json = json.dumps(task_state['iterations'], indent=2)
    prompt = CONCLUSION_PROMPT_TEMPLATE.format(
        current_date=task_state['current_date'],
        initial_query=task_state['initial_user_query'],
        plan=task_state['plan'],
        iterations_json=iterations_json,
        final_summary=task_state['final_summary']
    )
    conclusion = ollama_generate(prompt).get('response', 'No conclusion generated.').strip()
    pdf.add_section('Conclusion', conclusion)

    pdf_file = os.path.join(RESEARCH_DIR, f"research_{task_state['research_id']}.pdf")
    pdf.output(pdf_file)
    return pdf_file
import os
import re

from fpdf import FPDF

from constants import RESEARCH_DIR, FONT_PATH

class ResearchPDF(FPDF):
    def __init__(self, font_path):
        super().__init__()
        # Load the TrueType font with Unicode support
        self.add_font('Arial', '', font_path, uni=True)
        self.add_font('Arial', 'B', font_path, uni=True)
        # Set Arial as the default font
        self.set_font('Arial', '', 12)

    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Research Report', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        parts = re.split(r'(\*\*.*?\*\*)', body)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                self.set_font('Arial', 'B', 12)
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
        f"Expanded Query: {task_state['expanded_user_query']}\n"
        f"Plan:\n{task_state['plan']}"
    )
    pdf.add_section('Introduction', intro)

    findings = ""
    for step in task_state['steps']:
        findings += (
            f"Step {step['step_number']}: {step['description']}\n"
            f"Query: {step['query']}\n"
            f"Summary: {step['summary']}\n\n"
        )
    pdf.add_section('Findings', findings)

    pdf.add_section('Summary', task_state['summary'])

    pdf_file = os.path.join(RESEARCH_DIR, f"research_{task_state['research_id']}.pdf")
    pdf.output(pdf_file)
    return pdf_file
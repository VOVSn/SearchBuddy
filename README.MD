# WebSearchBuddy

WebSearchBuddy is a comprehensive tool designed for conducting web research and generating structured reports in PDF format. It utilizes an LLM-based agent to navigate through search results, iteratively improving the understanding and documentation of user queries.

## Features

- **Iterative Research**: Automatically generates plans and summaries for iterative exploration based on initial user queries.
- **PDF Reporting**: Compiles findings into a detailed PDF report with sections including introduction, findings, summary, and conclusion.
- **Dynamic Conclusions**: Generates conclusions using prompts from the research plan and results.

## Installation

To set up WebSearchBuddy, ensure you have Python installed. Follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/VOVSn/SearchBuddy
   cd SearchBuddy
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure constants in `constants.py` for API URLs, directories, and other settings.

## Tech Stack

- **Python**: Core programming language.
- **FPDF**: Used for PDF generation.
- **Requests**: For performing web searches.
- **Ollama Utils**: Custom utility module for interacting with LLMs.

## Configuration

Ensure the following constants are set in `constants.py`:

- `SEARCH_API_URL`: URL for performing web searches.
- `RESEARCH_DIR`: Directory to save research PDFs.
- `FONT_PATH`: Path to the font file used in PDF generation.
- `NUM_SEARCH_RESULTS`: Number of search results to fetch per query.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository and create a new branch for your feature or bug fix.
2. Ensure your code adheres to PEP 8 standards.
3. Write tests for any new functionality.
4. Submit a pull request with a clear description of changes.


# MSB Article Scanner

A Python script to scan and parse the latest articles from Molecular Systems Biology journal (EMBO Press).

## Features

- Fetches latest articles from https://www.embopress.org/toc/17444292/current
- Extracts article titles, publication dates, and abstracts
- Generates a markdown report with the collected information
- Saves reports with datestamps for future reference

## Requirements

- Python 3.6 or higher
- Required packages listed in `requirements.txt`

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Simply run the script:
```bash
python msb_scanner.py
```

The script will:
1. Fetch the latest articles
2. Parse the required information
3. Generate a markdown report in the `reports` subdirectory
4. The report filename will include the current date (e.g., `msb_articles_20250414.md`)

## Output

The script creates markdown files in the `reports` directory with the following format:
- Article title as heading
- Publication date
- Article abstract
- Separator between articles

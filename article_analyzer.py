#!/usr/bin/env python3
"""
Article Analyzer
Uses Grok API to analyze scientific articles and extract key findings.
Accepts a markdown report file as input and outputs the analysis to a markdown file.
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from openai import OpenAI
import httpx
from typing import Dict, List
from dotenv import load_dotenv
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file in Documents folder
env_path = Path.home() / ".env"
load_dotenv(env_path)

class ArticleAnalyzer:
    def __init__(self, api_key: str):
        """Initialize with XAI API key, explicitly disabling proxies."""
        # Create an httpx client that explicitly ignores proxies
        http_client = httpx.Client(proxies=None, transport=httpx.HTTPTransport(retries=3))
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
            http_client=http_client  # Pass the custom client
        )

    def extract_articles_from_markdown(self, markdown_file: Path) -> List[Dict]:
        """Extract articles from markdown report file."""
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split content into articles
            articles = []
            article_sections = content.split('---')[:-1]  # Skip last empty section
            
            for section in article_sections:
                if not section.strip():
                    continue
                
                # Extract article components
                title_match = re.search(r'##\s+(.+?)\n', section)
                authors_match = re.search(r'Authors:\s+(.+?)\n', section)
                abstract_match = re.search(r'Abstract:\s+(.+?)(?=\n\n|$)', section, re.DOTALL)
                doi_match = re.search(r'DOI:\s+\[(.+?)\]', section)
                journal_match = re.search(r'Journal:\s+(.+?)\n', section)
                
                if title_match and abstract_match:
                    article = {
                        'title': title_match.group(1).strip(),
                        'authors': authors_match.group(1).strip() if authors_match else "Authors not available",
                        'abstract': abstract_match.group(1).strip(),
                        'doi': doi_match.group(1) if doi_match else "DOI not available",
                        'journal': journal_match.group(1).strip() if journal_match else None
                    }
                    articles.append(article)
            
            return articles
        
        except Exception as e:
            logger.error(f"Error extracting articles from {markdown_file}: {str(e)}")
            return []

    def analyze_article(self, article: Dict) -> Dict:
        """Send article to Grok API for analysis."""
        journal = article.get('journal', 'this journal')
        prompt = f"""Analyze this scientific article from {journal} and provide a preliminary evaluation:

Title: {article['title']}
Authors: {article['authors']}
DOI: {article.get('doi', article.get('doi_url', 'N/A'))}
Abstract: {article['abstract']}

Please provide a preliminary analysis covering:

1. Core Research Question & Context:
   - What problem is this research addressing?
   - How does it fit into the current state of knowledge?
   - What gap is it trying to fill?

2. Key Findings & Results:
   - What are the 3-5 most important discoveries?
   - What evidence supports these findings?
   - Were there any unexpected or counter-intuitive results?

3. Significance & Innovation:
   - Why are these findings important to the field?
   - What theoretical or practical advances do they represent?
   - How do they change our understanding of the topic?

4. Connections to Other Research Areas:
   - How might these findings impact related fields?
   - What interdisciplinary connections are evident?
   - Could these findings or methods be applied elsewhere?

5. Relevance to Protein Interaction Network Analysis:
   - How might these findings inform or contribute to studies of protein-protein interactions?
   - Are there implications or insights that could be useful in network-based bioinformatics approaches?

Including the references to support your analysis.

Format the response as clear, well-structured Markdown using headings for each section (e.g., ## Core Research Question & Context).
"""

        try:
            completion = self.client.chat.completions.create(
                model="grok-3-beta",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                'article': article,
                'analysis': completion.choices[0].message.content
            }
        
        except Exception as e:
            logger.error(f"Error analyzing article: {str(e)}")
            return None

    def save_analysis(self, analyses: List[Dict], output_file: Path):
        """Save analyses to a markdown file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for analysis_item in analyses:
                    article = analysis_item['article']
                    analysis_content = analysis_item['analysis']
                    
                    f.write(f"# Analysis for: {article['title']}\n\n")
                    f.write(f"**Authors:** {article['authors']}\n")
                    f.write(f"**DOI:** [{article.get('doi', article.get('doi_url', 'N/A'))}](https://doi.org/{article.get('doi', article.get('doi_url', 'N/A'))})\n\n")
                    f.write("## Abstract\n")
                    f.write(f"{article['abstract']}\n\n")
                    f.write("## Grok Analysis\n")
                    f.write(f"{analysis_content}\n\n")
                    f.write("---\n\n") # Separator between articles
                    
            logger.info(f"Analysis saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving analysis: {str(e)}")

def main():
    # --- Argument Parsing --- 
    parser = argparse.ArgumentParser(description="Analyze articles from a markdown report using Grok API.")
    parser.add_argument("input_file", type=Path, 
                        help="Path to the input markdown report file (e.g., reports/msb_articles_20250414.md)")
    parser.add_argument("-o", "--output-file", type=Path, 
                        help="Path to the output analysis markdown file (optional)")
    args = parser.parse_args()

    # Validate input file
    if not args.input_file.is_file():
        logger.error(f"Input file not found: {args.input_file}")
        return
        
    # Determine output file path
    if args.output_file:
        output_file = args.output_file
    else:
        # Default output name based on input file
        timestamp = datetime.now().strftime('%Y%m%d')
        output_filename = f"{args.input_file.stem}_analysis_{timestamp}.md"
        output_file = args.input_file.parent / output_filename
        
    logger.info(f"Input file: {args.input_file}")
    logger.info(f"Output file: {output_file}")
    # ------------------------
    
    try:
        # Get API key from .env file
        api_key = os.getenv('XAI_API_KEY')
        if not api_key:
            logger.error("XAI_API_KEY not found in .env file")
            return

        analyzer = ArticleAnalyzer(api_key)
        analyses = []
        
        logger.info(f"Processing {args.input_file}...")
        
        # Extract articles from the specified report file
        articles = analyzer.extract_articles_from_markdown(args.input_file)
        logger.info(f"Found {len(articles)} articles in {args.input_file}")
        
        # Analyze each article
        for article in articles:
            logger.info(f"Analyzing article: {article['title'][:50]}...")
            analysis = analyzer.analyze_article(article)
            if analysis:
                analyses.append(analysis)
            else:
                logger.warning(f"Failed to analyze article: {article['title'][:50]}")
        
        # Save all analyses
        if analyses:
            analyzer.save_analysis(analyses, output_file)
        else:
            logger.warning("No analyses were generated")

    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")

if __name__ == "__main__":
    main()

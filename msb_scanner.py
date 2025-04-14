#!/usr/bin/env python3
"""
MSB Article Scanner
Scans the latest articles from Molecular Systems Biology journal and creates a markdown report.
"""

import feedparser
from datetime import datetime
from pathlib import Path
import logging
import sys
import re
from dateutil import parser
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_text(text):
    """Clean HTML tags and extra whitespace from text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Fix whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_abstract(entry):
    """Extract abstract from content field."""
    if hasattr(entry, 'content') and entry.content:
        # Get the first content item (they're identical in the feed)
        content = entry.content[0].value
        # Find the position of "Abstract" in the content
        abstract_pos = content.find('Abstract')
        if abstract_pos != -1:
            # Get everything after "Abstract"
            abstract = content[abstract_pos + len('Abstract'):]
            return clean_text(abstract)
        return clean_text(content)
    return "Abstract not available"

def format_date(date_str):
    """Format date string to a consistent format."""
    try:
        date = parser.parse(date_str)
        return date.strftime('%Y-%m-%d')
    except:
        return date_str

def fetch_msb_articles():
    """Fetch articles from Molecular Systems Biology RSS feed."""
    rss_url = "https://www.embopress.org/feed/17444292/most-recent"
    
    try:
        logger.info(f"Fetching RSS feed from {rss_url}...")
        feed = feedparser.parse(rss_url)
        
        if feed.bozo:
            logger.error(f"Error parsing feed: {feed.bozo_exception}")
            return None
        
        articles = []
        for entry in feed.entries:
            try:
                # Extract required fields
                article = {
                    'title': entry.title,
                    'authors': entry.get('author', 'Authors not available'),
                    'abstract': extract_abstract(entry),
                    'doi_url': entry.link,
                    'published_date': format_date(entry.published)
                }
                
                articles.append(article)
                logger.info(f"Successfully parsed article: {article['title'][:50]}...")
                
            except Exception as e:
                logger.error(f"Error parsing article: {e}")
                continue
        
        return articles
    
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        return None

def create_markdown_report(articles):
    """Create a markdown report from the articles."""
    if not articles:
        return "# No articles found\n\nNo articles were found or there was an error fetching the articles."
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    markdown = f"# Molecular Systems Biology - Latest Articles\n\nScanned on: {current_date}\n\n"
    
    for article in articles:
        markdown += f"## {article['title']}\n\n"
        markdown += f"Authors: {article['authors']}\n\n"
        markdown += f"Published: {article['published_date']}\n\n"
        markdown += f"DOI: [{article['doi_url']}]({article['doi_url']})\n\n"
        markdown += f"Abstract:\n{article['abstract']}\n\n"
        markdown += "---\n\n"
    
    return markdown

def save_report(content, output_path: Path):
    """Save the markdown report to the specified file path."""
    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Report saved successfully: {output_path}")
    except Exception as e:
        logger.error(f"Error saving report to {output_path}: {str(e)}")

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Scan MSB RSS feed and save articles to Markdown.")
    parser.add_argument("-o", "--output", type=Path, 
                        help="Path to save the output markdown file (including filename). Defaults to 'reports/msb_articles_YYYYMMDD.md'")
    args = parser.parse_args()

    # Determine output file path
    if args.output:
        output_file = args.output
    else:
        # Default output path
        output_dir = Path("reports")
        filename = f"msb_articles_{datetime.now().strftime('%Y%m%d')}.md"
        output_file = output_dir / filename
        
    logger.info(f"Output will be saved to: {output_file}")
    # ------------------------
        
    try:
        logger.info("Starting MSB Article Scanner...")
        articles = fetch_msb_articles()
        
        if articles:
            markdown_report = create_markdown_report(articles)
            save_report(markdown_report, output_file)
        else:
            logger.warning("No articles found or error fetching feed.")
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generic RSS Article Scanner
- Scans articles from any journal RSS feed using column_mapping.json
- Outputs a markdown report
"""
import sys
import feedparser
import json
from datetime import datetime
from pathlib import Path
import re

def load_mapping(feed_id, mapping_path='column_mapping.json'):
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    if feed_id not in mapping:
        raise ValueError(f"Feed ID '{feed_id}' not found in {mapping_path}")
    return mapping[feed_id]

def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text or '')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_field(entry, tag, map_info):
    # Handle multi-valued fields
    if isinstance(map_info, dict) and 'join_with' in map_info:
        values = []
        # Support both feedparser and raw dict
        if hasattr(entry, tag):
            values = getattr(entry, tag)
        elif tag in entry:
            values = entry[tag]
        # feedparser: multi-valued fields may be list or single
        if not isinstance(values, list):
            values = [values]
        joined = map_info.get('join_with', ', ').join([clean_text(str(v)) for v in values if v])
        return joined
    # Single-valued field
    val = getattr(entry, tag, None) or entry.get(tag) if isinstance(entry, dict) else None
    return clean_text(str(val)) if val else ''

def parse_articles(feed_url, feed_id, mapping_path='column_mapping.json'):
    mapping = load_mapping(feed_id, mapping_path)
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        print("No entries found in feed.")
        return []
    # Print complete first entry for inspection
    import pprint
    print("\nDEBUG: Complete first entry:\n")
    pprint.pprint(feed.entries[0], indent=2, width=120)
    print("\n---\n")
    articles = []
    for entry in feed.entries:
        article = {}
        for tag, map_info in mapping.items():
            canon_field = map_info['target'] if isinstance(map_info, dict) else map_info
            article[canon_field] = extract_field(entry, tag, map_info)
        articles.append(article)
    return articles

def create_markdown_report(articles, feed_id, journal_name=None):
    from datetime import datetime
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    markdown = f"Generated at: {current_datetime}\n\n"
    for article in articles:
        markdown += f"## {article.get('title', 'No Title')}\n\n"
        if 'authors' in article:
            markdown += f"Authors: {article['authors']}\n\n"
        if 'published_date' in article:
            markdown += f"Published: {article['published_date']}\n\n"
        if 'doi_url' in article:
            markdown += f"DOI: [{article['doi_url']}]({article['doi_url']})\n\n"
        if 'link' in article:
            markdown += f"Link: [{article['link']}]({article['link']})\n\n"
        if 'abstract' in article:
            markdown += f"Abstract:\n{article['abstract']}\n\n"
        markdown += "---\n\n"
    return markdown

def save_report(content, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Report saved to {output_path}")

def main():
    import re
    if len(sys.argv) < 3:
        print("Usage: python generic_rss_scanner.py <rss_url_or_file> <feed_id> [journal_name]")
        sys.exit(1)
    feed_url = sys.argv[1]
    feed_id = sys.argv[2]
    journal_name = sys.argv[3] if len(sys.argv) > 3 else None

    # Generate output file name automatically
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use journal name if provided, else feed_id
    if journal_name:
        safe_journal = re.sub(r'[^A-Za-z0-9]+', '_', journal_name.strip()).lower()
        base_name = safe_journal
    else:
        base_name = feed_id
    output_md = f"output/{base_name}_articles_{timestamp}.md"

    try:
        articles = parse_articles(feed_url, feed_id)
        if not articles:
            print("No articles found or error parsing feed.")
            sys.exit(1)
        markdown = create_markdown_report(articles, feed_id, journal_name)
        save_report(markdown, output_md)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

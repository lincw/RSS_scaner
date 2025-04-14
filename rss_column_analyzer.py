#!/usr/bin/env python3
"""
RSS Column Analyzer
"""

import sys
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

def get_rss_content(source):
    if urlparse(source).scheme in ('http', 'https'):
        resp = requests.get(source)
        resp.raise_for_status()
        return resp.content
    else:
        with open(source, 'rb') as f:
            return f.read()

def find_items_or_entries(root):
    # Gather all <item> (RSS 2.0/1.0), <entry> (Atom), with or without namespaces
    items = []
    for elem in root.iter():
        tag = elem.tag
        if tag.endswith('item') or tag.endswith('entry'):
            items.append(elem)
    return items

def analyze_rss_columns(rss_content):
    root = ET.fromstring(rss_content)
    items = find_items_or_entries(root)
    if not items:
        print('No <item> or <entry> elements found. This feed may use an unsupported format or require advanced namespace handling.')
        print('Root tag:', root.tag)
        print('First-level tags:', [child.tag for child in root])
        return
    first_item = items[0]
    print('Detected columns/tags in <item>/<entry> (showing sample value from the first item):')
    for child in first_item:
        # Remove namespace if present
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        # Get text or CDATA content, or attribute if present
        value = (child.text or '').strip()
        if not value and list(child):
            # If the tag has children, show a summary
            value = '[XML subtree]' 
        if len(value) > 100:
            value = value[:100] + '...'
        print(f'- {tag}: {value}')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python rss_column_analyzer.py <rss_url_or_file>')
        sys.exit(1)
    source = sys.argv[1]
    try:
        rss_content = get_rss_content(source)
        analyze_rss_columns(rss_content)
    except Exception as e:
        print(f'Error: {e}')

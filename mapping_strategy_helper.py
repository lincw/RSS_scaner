#!/usr/bin/env python3
"""
RSS Mapping Strategy Helper

- Analyzes an RSS/Atom feed and shows all columns/tags with sample values
- Suggests which tags are likely candidates for canonical fields (title, authors, abstract, date, link)
- Provides a template JSON snippet for column_mapping.json
"""
import sys
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import re
import json
from pathlib import Path

CANONICAL_FIELDS = ['title', 'authors', 'abstract', 'published_date', 'doi_url', 'link']

# Heuristics for likely tag matches
FIELD_HINTS = {
    'title': re.compile(r'title', re.I),
    'authors': re.compile(r'creator|author', re.I),
    'abstract': re.compile(r'description|summary|abstract|content:encoded', re.I),
    'published_date': re.compile(r'date|published|pubDate|updated', re.I),
    'doi_url': re.compile(r'doi|link', re.I),
    'link': re.compile(r'link', re.I),
}

def get_rss_content(source):
    if urlparse(source).scheme in ('http', 'https'):
        resp = requests.get(source)
        resp.raise_for_status()
        return resp.content
    else:
        with open(source, 'rb') as f:
            return f.read()

def find_items_or_entries(root):
    items = []
    for elem in root.iter():
        tag = elem.tag
        if tag.endswith('item') or tag.endswith('entry'):
            items.append(elem)
    return items

def suggest_mapping(tags):
    mapping = {}
    used = set()
    for canon, regex in FIELD_HINTS.items():
        for tag in tags:
            if regex.fullmatch(tag) or regex.search(tag):
                mapping[tag] = canon
                used.add(tag)
                break
    # Add unmapped tags
    for tag in tags:
        if tag not in used:
            mapping[tag] = tag
    return mapping

def interactive_mapping(mapping, tags):
    print('\n--- Interactive Mapping ---')
    print('For each detected tag, enter the canonical field to map to (or press Enter to accept the suggestion).')
    print('Canonical fields: title, authors, abstract, published_date, doi_url, link, or leave as-is.')
    new_mapping = {}
    for tag in tags:
        suggested = mapping[tag]
        user_input = input(f'Map "{tag}" [{suggested}]: ').strip()
        field = user_input if user_input else suggested
        multi = input(f'Is "{tag}" multi-valued (appears multiple times per item)? [y/N]: ').strip().lower()
        if multi == 'y':
            delim = input('Delimiter to join values (default: ", "): ').strip()
            if not delim:
                delim = ', '
            new_mapping[tag] = {"target": field, "join_with": delim}
        else:
            new_mapping[tag] = field
    return new_mapping

def update_json_mapping_file(feed_id, new_mapping, json_path='column_mapping.json'):
    path = Path(json_path)
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    else:
        data = {}
    # Overwrite only the mapping for feed_id, preserve others
    data[feed_id] = new_mapping
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f'Updated mapping saved to {json_path}')

def analyze_and_suggest(rss_content, feed_id_hint='your_feed', update_json=False, json_path='column_mapping.json'):
    root = ET.fromstring(rss_content)
    items = find_items_or_entries(root)
    if not items:
        print('No <item> or <entry> elements found.')
        return
    first_item = items[0]
    print('\nDetected columns/tags in <item>/<entry> (sample values shown):')
    tags = []
    seen = set()
    for child in first_item:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag not in seen:
            tags.append(tag)
            seen.add(tag)
        value = (child.text or '').strip()
        if not value and list(child):
            value = '[XML subtree]'
        if len(value) > 100:
            value = value[:100] + '...'
        print(f'- {tag}: {value}')
    # Suggest mapping
    print('\nSuggested mapping for column_mapping.json:')
    mapping = suggest_mapping(tags)
    print(f'\n"{feed_id_hint}": {{')
    for tag, canon in mapping.items():
        print(f'    "{tag}": "{canon}",')
    print('}\n')
    print('---')
    print('Guide:')
    print('- title: usually the article title')
    print('- authors: may be multiple creator/author tags; join them if needed')
    print('- abstract: often description, summary, or content:encoded')
    print('- published_date: pubDate, published, or date')
    print('- doi_url or link: the article link or DOI')
    print('- You can edit the suggested mapping as needed. For multi-valued fields (e.g., multiple creators), map to your canonical field and handle joining in your processing script.')
    if update_json:
        new_mapping = interactive_mapping(mapping, tags)
        update_json_mapping_file(feed_id_hint, new_mapping, json_path)

def main():
    if len(sys.argv) < 2:
        print('Usage: python mapping_strategy_helper.py <rss_url_or_file> [feed_id_hint] [--update-json] [--json-path path]')
        sys.exit(1)
    source = sys.argv[1]
    feed_id_hint = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'your_feed'
    update_json = '--update-json' in sys.argv
    json_path = 'column_mapping.json'
    for i, arg in enumerate(sys.argv):
        if arg == '--json-path' and i + 1 < len(sys.argv):
            json_path = sys.argv[i + 1]
    try:
        rss_content = get_rss_content(source)
        analyze_and_suggest(rss_content, feed_id_hint, update_json, json_path)
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    main()

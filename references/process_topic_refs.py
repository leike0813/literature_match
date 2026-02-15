import yaml
import os
import re
import argparse
import urllib.request
import json
import difflib
import subprocess
from datetime import datetime

# Optional Zotero API
try:
    from pyzotero import zotero
    HAS_PYZOTERO = True
except ImportError:
    HAS_PYZOTERO = False

def load_config(config_path):
    # Resolve absolute path if not already
    if not os.path.isabs(config_path):
        if not os.path.exists(config_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            alt_path = os.path.join(script_dir, '..', config_path)
            if os.path.exists(alt_path):
                config_path = alt_path
    
    print(f"Loading config from: {os.path.abspath(config_path)}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def fetch_json_from_zotero_memory():
    """
    Fetches the library from Zotero local Better BibTeX API in JSON format.
    Returns the parsed JSON object (List or Dict) or None if failed.
    Does NOT write to disk.
    """
    url = "http://127.0.0.1:23119/better-bibtex/export/library?/1/library.json"
    
    print(f"Fetching Library JSON from Zotero (via Better BibTeX)...")
    print(f"DEBUG: Requesting URL: {url}")
    
    # Method 1: Python urllib (Proxies bypassed)
    try:
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)

        with urllib.request.urlopen(url, timeout=10) as response:
            data = response.read()
            return json.loads(data)
    except Exception as e:
        print(f"Python urllib memory fetch failed: {e}. Trying 'curl' fallback...")

    # Method 2: Curl via subprocess (captured stdout)
    try:
        # -s: Silent, but we want stdout. No -o.
        cmd = ['curl', '-s', url]
        print(f"DEBUG: Running curl command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0 and result.stdout and len(result.stdout) > 10:
            print(f"Successfully fetched JSON via curl (Size: {len(result.stdout)} chars)")
            return json.loads(result.stdout)
        else:
            print(f"Curl failed. Return code: {result.returncode}. Stderr: {result.stderr[:200]}")
    except Exception as e:
        print(f"Curl fallback failed: {e}")
        
    return None

def fetch_json_from_zotero(save_path):
    """
    Fetches the library from Zotero local Better BibTeX API in JSON format.
    Format: BetterBibTeX JSON or CSL JSON
    """
    if not save_path:
        print("Error: 'json_file' is not configured in config.yaml.")
        return False

    # Updated URL based on documentation: Use 'betterbibtex.json' for full metadata (including URLs)
    url = "http://127.0.0.1:23119/better-bibtex/export/library?/1/betterbibtex.json"
    
    print(f"Fetching Library JSON from Zotero (via Better BibTeX)...")
    print(f"DEBUG: Requesting URL: {url}")
    
    # Method 1: Python urllib (Proxies bypassed)
    try:
        # Configure urllib to bypass system proxies (common issue with localhost)
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)

        # Ensure directory exists
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)

        with urllib.request.urlopen(url, timeout=10) as response:
            data = response.read()
            json.loads(data) # Check validity
            with open(save_path, 'wb') as f:
                f.write(data)
        print(f"Successfully saved JSON to: {save_path}")
        return True
    except Exception as e:
        print(f"Python urllib failed: {e}. Trying 'curl' fallback...")

    # Method 2: Curl via subprocess (System command)
    try:
        # Ensure save_path is absolute for curl
        abs_save_path = os.path.abspath(save_path)
        cmd = ['curl', '-s', '-o', abs_save_path, url]
        print(f"DEBUG: Running curl command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(abs_save_path) and os.path.getsize(abs_save_path) > 10:
            print(f"Successfully saved JSON via curl to: {abs_save_path}")
            return True
        else:
            print(f"Curl failed. Return code: {result.returncode}. Stderr: {result.stderr}")
    except Exception as e:
        print(f"Curl fallback failed: {e}")
        
    print("Warning: Could not fetch JSON automatically. Using existing file if available.")
    return False

def parse_markdown_refs(markdown_file):
    """
    Extracts reference titles/authors AND URLs from the markdown file.
    """
    if not os.path.exists(markdown_file):
        print(f"Error: Markdown file not found: {markdown_file}")
        return []

    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()

    ref_section_match = re.search(r'^#+\s+.*?(?:References|参考文献|Works quoted|Works cited).*?$(.*)', content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if not ref_section_match:
        print("No 'References' section found.")
        return []

    ref_text = ref_section_match.group(1)
    refs = []
    
    lines = ref_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        
        match = re.match(r'^\[?(\d+)\]?\.?\s+(.*)', line)
        if match:
            ref_id = match.group(1)
            raw_text = match.group(2)
            
            # Extract URL if present
            # Improved regex to avoid sticking to trailing punctuation like ) or . or ]
            # Key fix: added \] to the excluded character set [^\s\)\]]
            url_match = re.search(r'(https?://[^\s\)\]]+)', raw_text)
            url = url_match.group(1) if url_match else None
            
            if url:
                # Extra cleanup for trailing punctuation
                url = url.rstrip(').,;]')
            
            # --- DEBUG ---
            # if ref_id in ['1', '98']: # Print debug for specific problematic refs
            print(f"DEBUG: Parsed Ref [{ref_id}]")
            print(f"       Raw: {raw_text[:50]}...")
            print(f"       URL: {url}")
            # -------------

            # Cleanup for Title extraction
            clean_text = raw_text
            if url: 
                clean_text = clean_text.replace(url, '')
            clean_text = re.sub(r'\(\d{4}\)', '', clean_text)
            
            # Remove "accessed [Date]" common in Zotero refs
            clean_text = re.sub(r', accessed \w+ \d{1,2}, \d{4}', '', clean_text)
            clean_text = re.sub(r', accessed .*?$', '', clean_text)
            # Remove "arXiv:..."
            clean_text = re.sub(r'arXiv:\d+\.\d+', '', clean_text, flags=re.IGNORECASE)
            
            # Remove " - Source" or " \- Source" patterns (common in this markdown)
            # e.g. "Sparse DETR \- ICLR" -> "Sparse DETR"
            clean_text = re.split(r'\s(?:-|\\-|–|—)\s', clean_text)[0]
            
            query_title = None
            
            # Try to get quoted title, BUT check if it's just a URL/Bracketed Link
            # Pattern: "Title" or "([https://...])"
            title_match = re.search(r'["“](.*?)["”]', clean_text)
            if title_match:
                candidate = title_match.group(1).strip()
                # Heuristic: If candidate looks like a URL (starts with http, [http, (http), skip it
                if not re.match(r'^[\(\[]?https?://', candidate):
                    query_title = candidate
            
            if not query_title:
                # Fallback: Manual cleanup
                # Split by dot or comma? unique to reference style
                # For `Ren, ... "URL" ...`, removing URL leaves `Ren, ... . ...`
                # Heuristic: split by comma, take the longest part? No, authors have commas.
                # Heuristic: just take the whole cleaned text (up to 120 chars) and hope substring match works.
                query_title = clean_text[:120].strip()
                # Remove leading/trailing punctuation
                query_title = query_title.strip('.,;[]() ')
            
            refs.append({
                'id': ref_id,
                'raw_text': raw_text,
                'query_title': query_title,
                'url': url
            })
            
    return refs

def load_local_json_library(json_file):
    """
    Parses the local JSON file (Fallback).
    """
    if not os.path.exists(json_file):
        print(f"Error: Fallback JSON file not found: {json_file}")
        return []
        
    print(f"Loading local fallback JSON: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    return parse_json_data(data)

def parse_json_data(data):
    """
    Helper to normalize JSON data (List vs Dict)
    """
    items = []
    if isinstance(data, list):
        print("Format detected: CSL JSON (List)")
        items = data
    elif isinstance(data, dict):
        print("Format detected: Better BibTeX JSON (Dict)")
        items = data.get('items', [])
    else:
        print("Error: Unknown JSON format.")
    
    print(f"Loaded {len(items)} items.")
    return items

def smart_match_refs(library_items, refs):
    """
    Matches markdown refs to library items using URL (Exact) and Title (Fuzzy).
    Adapts to CSL/BBT field naming differences.
    """
    matched = {}
    print(f"Smart matching {len(refs)} references against {len(library_items)} library items...")
    
    # DEBUG: Inspect the first library item to verify fields
    if library_items:
        print("DEBUG: Sample Library Item Keys:", library_items[0].keys())
        sample_url = library_items[0].get('url') or library_items[0].get('URL')
        print(f"DEBUG: Sample Item URL: {sample_url}")

    # Pre-index library for speed
    url_map = {} 
    
    # Support multiple field names
    def get_field(item, keys):
        for k in keys:
            if k in item: return item[k]
        return None

    def extract_ids(text):
        """Extracts potential identifiers (DOI, ArXiv) from a string."""
        if not text: return {}
        ids = {}
        # ArXiv ID (e.g. 2109.03814)
        # Matches new format YYYY.NNNNN
        arxiv_match = re.search(r'(\d{4}\.\d{4,5})', text)
        if arxiv_match:
            ids['arxiv'] = arxiv_match.group(1)
        
        # DOI (Simple regex)
        doi_match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', text, re.IGNORECASE)
        if doi_match:
            ids['doi'] = doi_match.group(1).lower()
            
        return ids

    # Pre-process library Items
    lib_lookup = []
    for item in library_items:
        u = get_field(item, ['URL', 'url'])
        doi = get_field(item, ['DOI', 'doi'])
        
        # Extract IDs from URL and DOI field
        item_ids = extract_ids(u)
        if doi:
            item_ids.update(extract_ids(doi))
            
        lib_lookup.append({
            'item': item,
            'url': u.lower() if u else '',
            'ids': item_ids
        })

    for ref in refs:
        ref_id = ref['id']
        ref_url = ref['url']
        ref_title = ref['query_title']
        
        found_item = None
        match_type = None
        
        # 1. Strategy: Identifier Match (ArXiv / DOI)
        if ref_url:
            ref_ids = extract_ids(ref_url)
            
            # Check against library
            for entry in lib_lookup:
                # Check ArXiv
                if 'arxiv' in ref_ids and 'arxiv' in entry['ids']:
                     if ref_ids['arxiv'] == entry['ids']['arxiv']:
                         found_item = entry['item']
                         match_type = f"ArXiv ID ({ref_ids['arxiv']})"
                         break
                
                # Check DOI
                if 'doi' in ref_ids and 'doi' in entry['ids']:
                     if ref_ids['doi'] == entry['ids']['doi']:
                         found_item = entry['item']
                         match_type = "DOI"
                         break
                         
                # Fallback: Relaxed URL containment
                if not found_item:
                    # Normalize: remove http/s, www, trailing slash
                    def norm_url(u):
                        if not u: return ""
                        u = u.lower().replace('https://', '').replace('http://', '').replace('www.', '')
                        return u.rstrip('/')
                        
                    ref_clean = norm_url(ref_url)
                    item_clean = norm_url(entry['url'])
                    
                    if ref_clean and item_clean:
                         # 1. Exact-ish
                         if ref_clean == item_clean:
                             found_item = entry['item']
                             match_type = "URL (Exact-ish)"
                             break
                         
                         # 2. Cross-containment (e.g. arxiv.org/abs/123 vs arxiv.org/pdf/123)
                         # Simple check: if one contains the other? No, pdf vs abs.
                         # Check SequenceMatcher
                         ratio = difflib.SequenceMatcher(None, ref_clean, item_clean).ratio()
                         if ratio > 0.85: # Lowered from 0.90
                             found_item = entry['item']
                             match_type = f"URL (Fuzzy: {int(ratio*100)}%)"
                             break

        # 2. Strategy: Title Fuzzy Match
        if not found_item and ref_title:
             # ... (existing title logic) ...
            candidates = [i for i in library_items if get_field(i, ['title', 'title-short'])]
            if candidates:
                item_titles = [get_field(i, ['title']) for i in candidates]
                # Filter None
                item_titles = [t for t in item_titles if t]
                
                # 2a. Fuzzy Match (Difflib)
                matches = difflib.get_close_matches(ref_title, item_titles, n=1, cutoff=0.7)
                if matches:
                    best_title = matches[0]
                    for item in candidates:
                        if get_field(item, ['title']) == best_title:
                            found_item = item
                            ratio = difflib.SequenceMatcher(None, ref_title, best_title).ratio()
                            match_type = f"Title (Fuzzy: {int(ratio*100)}%)"
                            break
                            
                # 2b. Substring Match
                if not found_item:
                    ref_norm = ref_title.lower().replace('-', ' ').replace(':', '').strip()
                    for item in candidates:
                        t = get_field(item, ['title']) or ""
                        t_norm = t.lower().replace('-', ' ').replace(':', '').strip()
                        
                        if len(ref_norm) > 6:
                             if t_norm.startswith(ref_norm) or ref_norm.startswith(t_norm):
                                 found_item = item
                                 match_type = "Title (Prefix Match)"
                                 break
                             if (ref_norm in t_norm or t_norm in ref_norm):
                                 found_item = item
                                 match_type = "Title (Substring)"
                                 break
        
        # 3. Strategy: Author + Year (Last Resort)
        # Catches "Ren, ... (2015)" where title is missing/wrong
        if not found_item:
             # Extract Year from Ref Text
             ref_year_match = re.search(r'(\d{4})', ref['raw_text'])
             if ref_year_match:
                 ref_year = ref_year_match.group(1)
                 
                 for item in library_items:
                     # Get Item Year
                     date = item.get('issued', {}).get('date-parts', [['']])
                     item_year = str(date[0][0]) if date and date[0] else None
                     
                     if item_year != ref_year: continue
                     
                     # Get First Author Family Name
                     creators = item.get('author', [])
                     if not creators: continue
                     family = creators[0].get('family', '').lower()
                     if not family: continue
                     
                     # Check if Family Name in Ref Raw Text (Case insensitive)
                     if family in ref['raw_text'].lower():
                         # Verify it's not a common name like "Wang" causing false positives?
                         # Maybe check first two authors? 
                         # For now, strict Year match + Family name match is decent.
                         found_item = item
                         match_type = f"Author+Year ({family}, {item_year})"
                         break

        if found_item:
            title = get_field(found_item, ['title']) or "Untitled"
            print(f"  [{ref_id}] FOUND by {match_type} -> {title[:30]}...")
            matched[ref_id] = found_item
        else:
            print(f"  [{ref_id}] NOT FOUND. Ref: {ref_title[:40]}...")
            
    return matched

def apply_zotero_tags_json(matched_refs, config, topic_tag):
    """
    Uses Zotero API to find items by Citekey (from JSON match) and tag them via Cloud API.
    """
    if not config.get('zotero', {}).get('api_key'):
        return

    if not HAS_PYZOTERO:
        return

    print("Connecting to Zotero API for tagging...")
    try:
        zot = zotero.Zotero(config['zotero']['library_id'], config['zotero']['library_type'], config['zotero']['api_key'])
        
        for ref_id, item in matched_refs.items():
            # CSL JSON often lacks cloud itemKey. We try best effort.
            # BBT JSON has it.
            item_key = item.get('itemKey')
            citekey = item.get('citationKey') or item.get('id')

            if not item_key:
                # If we don't have itemKey (e.g. CSL JSON), we might need to search by title causing duplicate requests.
                # For safety: Skip tagging if no itemKey
                print(f"  Skipping cloud tag for {citekey}: No 'itemKey' in local metadata (CSL JSON limitation).")
                continue
                
            try:
                print(f"  Tagging {item_key} ({citekey}) -> {topic_tag}")
                zot.add_tags(zot.item(item_key), topic_tag)
            except Exception as e:
                print(f"  Failed to tag {item_key}: {e}")
            
    except Exception as e:
        print(f"Zotero API Error: {e}")

def create_obsidian_notes(matched_refs, config):
    papers_dir = config['papers_dir']
    if not os.path.exists(papers_dir):
        os.makedirs(papers_dir)
        
    templates_dir = config.get('templates_dir')
    template_content = None
    if templates_dir and os.path.exists(templates_dir):
        tpl_path = os.path.join(templates_dir, 'paper_template.md')
        if os.path.exists(tpl_path):
            with open(tpl_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
    
    if not template_content:
        template_content = """---
title: "{title}"
citekey: {citekey}
tags: {tags}
zotero_link: {zotero_select_uri}
pdf_path: {pdf_path}
url: {url}
---
# {title}

## Abstract
{abstract}

## Notes
"""

    created_notes = {}
    default_tags = str(config.get('default_tags', []))

    for ref_id, item in matched_refs.items():
        # CSL: 'id', BBT: 'citationKey'
        citekey = item.get('citationKey') or item.get('id')
        if not citekey: continue
        
        title = item.get('title', 'Untitled')
        abstract = item.get('abstract', '')
        # CSL: 'URL', BBT: 'url'
        url = item.get('URL') or item.get('url', '')
        
        # Zotero URI
        item_key = item.get('itemKey')
        if item_key:
            zotero_select_uri = f"zotero://select/library/items/{item_key}"
        else:
            # Fallback for CSL JSON
            zotero_select_uri = f"zotero://select/items/@{citekey}"
        
        # PDF Path (Attachments)
        pdf_path = "Not found"
        # Check 'attachments' (BBT)
        if 'attachments' in item:
             for att in item['attachments']:
                if 'application/pdf' in att.get('contentType', '') or att.get('path', '').lower().endswith('.pdf'):
                    pdf_path = att.get('path')
                    break
        
        # Format
        content = template_content.replace('{title}', title)\
                                  .replace('{citekey}', citekey)\
                                  .replace('{tags}', default_tags)\
                                  .replace('{pdf_path}', pdf_path)\
                                  .replace('{url}', url)\
                                  .replace('{zotero_select_uri}', zotero_select_uri)\
                                  .replace('{abstract}', abstract)
        
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        filename = f"{citekey} - {safe_title}.md"
        if len(filename) > 150: filename = filename[:147] + ".md"
        filepath = os.path.join(papers_dir, filename)
        
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created note: {filename}")
        else:
            print(f"Skipped existing note: {filename}")
        
        # Store tuple: (citekey, filename_stem)
        created_notes[ref_id] = (citekey, filename.replace('.md', ''))
        
    return created_notes


def format_harvard(item):
    """
    Formats a Zotero item into a more complete Harvard style citation.
    """
    # Authors
    creators = item.get('author', [])
    if not creators:
        creators = item.get('editor', [])
        
    author_parts = []
    if creators:
        for i, c in enumerate(creators):
            family = c.get('family', '')
            given = c.get('given', '')
            initials = ''.join([n[0] for n in given.split()]) if given else ''
            
            if i == 0:
                author_parts.append(f"{family}, {initials}.")
            else:
                author_parts.append(f"{initials}. {family}")
        
    if not author_parts:
        author_str = "Anon."
    elif len(author_parts) == 1:
        author_str = author_parts[0]
    elif len(author_parts) == 2:
        author_str = f"{author_parts[0]} and {author_parts[1]}"
    else:
        author_str = f"{author_parts[0]} et al."
            
    # Year
    date = item.get('issued', {}).get('date-parts', [['']])
    year = date[0][0] if date and date[0] else "n.d."
    
    # Title
    title = item.get('title', 'Untitled')
    
    # Container / Source Details
    parts = [f"{author_str} ({year}) '{title}'"]
    
    container = item.get('container-title') or item.get('publisher') or item.get('source')
    if container:
        parts.append(f"_{container}_") # Italics for journal/publisher
        
    vol = item.get('volume')
    issue = item.get('issue')
    page = item.get('page')
    
    details = ""
    if vol:
        details += f"{vol}"
    if issue:
        details += f"({issue})"
    if page:
        if details: details += ", "
        details += f"pp. {page}"
        
    if details:
        parts.append(details)
        
    # DOI/URL
    doi = item.get('DOI')
    url = item.get('URL')
    
    if doi:
        parts.append(f"doi: {doi}")
    elif url:
        parts.append(f"Available at: {url}")
        
    return ", ".join(parts) + "."

def update_markdown_links(markdown_file, created_notes, matched_refs_map=None):
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    count = 0
    debug_replacement = []
    
    # 1. Update text citations
    for ref_id, (citekey, note_name) in created_notes.items():
        eid = re.escape(ref_id)
        pattern = r'(\[' + eid + r'\]|(?<=\s)' + eid + r'(?=[。，\.]))'
        
        matches = re.findall(pattern, content)
        if matches:
            link_text = f"[[{note_name}|{citekey}]]"
            content = re.sub(pattern, link_text, content)
            count += len(matches)
            debug_replacement.append(f"[{ref_id}] -> {link_text} ({len(matches)} times)")
            
    # 2. Insert Reference Section
    works_cited_match = re.search(r'(#{2,4}\s*[*_]*(?:Works cited|Works quoted|References|参考文献)[*_]*)', content, re.IGNORECASE)
    
    if works_cited_match and matched_refs_map:
        bib_section = "\n## 参考文献 (References)\n\n"
        
        # Deduplicate items by Citation Key
        unique_items = {}
        for item in matched_refs_map.values():
            key = item.get('citationKey') or item.get('id')
            if key:
                unique_items[key] = item
        
        # Sort by citekey
        sorted_keys = sorted(unique_items.keys())
        
        for citekey in sorted_keys:
            item = unique_items[citekey]
            harvard = format_harvard(item)
            
            # Use concise link
            # We need to find the note filename. 
            # Since matched_refs_map is id->item, we need a reverse lookup or just use one of the notes created.
            # created_notes is id -> (citekey, filename_stem)
            
            note_name = citekey # Fallback
            # Find any note name for this citekey
            for _, (c, n) in created_notes.items():
                if c == citekey:
                    note_name = n
                    break
            
            note_link = f"[[{note_name}|{citekey}]]"
            bib_section += f"- {note_link}: {harvard}\n"
            
        bib_section += "\n---\n\n"
        
        start_idx = works_cited_match.start()
        content = content[:start_idx] + bib_section + content[start_idx:]
        print(f"Inserted '参考文献' section with {len(unique_items)} unique items.")
    else:
        print("Warning: Could not find 'Works cited'/'References' section header. Bibliography NOT inserted.")
        
    output_file = markdown_file.replace('.md', '_processed.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"\n--- Linking Report ---")
    print(f"Total replacements: {count}")
    print(f"Saved processed markdown to: {output_file}")
    
def main():
    parser = argparse.ArgumentParser(description="Topic-Based Ingestion (Smart Match)")
    parser.add_argument("markdown_file", help="Input markdown file")
    parser.add_argument("--tag", help="Topic tag to apply in Zotero (Optional)")
    parser.add_argument("--config", default="configs/ingestion_config.yaml")
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    # 1. Automated Export
    library_data = fetch_json_from_zotero_memory()
    library_items = []
    
    if library_data:
        print("Using data fetched from Zotero API.")
        library_items = parse_json_data(library_data)
    else:
        print("API fetch failed. Trying local fallback file...")
        json_path = config.get('json_file')
        if json_path:
             library_items = load_local_json_library(json_path)
        else:
             print("Error: No 'json_file' configured for fallback.")
             
    if not library_items:
        print("No library items loaded. Exiting.")
        return
    
    # 2. Parse Markdown
    refs = parse_markdown_refs(args.markdown_file)
    if not refs: return
    
    # 3. Smart Match
    matched_refs = smart_match_refs(library_items, refs)
    
    # Report Unmatched Library Items (Zotero items NOT used in this markdown)
    # Get set of all library Item keys
    all_lib_keys = set()
    for item in library_items:
        k = item.get('citationKey') or item.get('id')
        if k: all_lib_keys.add(k)
        
    # Get set of matched Item keys
    matched_lib_keys = set()
    for item in matched_refs.values():
         k = item.get('citationKey') or item.get('id')
         if k: matched_lib_keys.add(k)
         
    unmatched_keys = all_lib_keys - matched_lib_keys
    
    if unmatched_keys:
        print(f"\n--- Unmatched Library Items Report ({len(unmatched_keys)} items) ---")
        print("These Zotero items were NOT found in the markdown references:")
        for k in sorted(unmatched_keys):
            # Find item to show title
            item = next((i for i in library_items if (i.get('citationKey')==k or i.get('id')==k)), None)
            title = item.get('title', 'Unknown Title') if item else 'Unknown'
            print(f"- [{k}] {title[:60]}...")
        print("-------------------------------------------------------------------\n")
    else:
        print("\nAll Zotero library items were matched to at least one reference!\n")
    
    # 4. Tag in Zotero (Optional)
    if args.tag:
        apply_zotero_tags_json(matched_refs, config, args.tag)
    
    # 5. Create Notes
    created_notes = create_obsidian_notes(matched_refs, config)
    
    # 6. Link
    update_markdown_links(args.markdown_file, created_notes, matched_refs_map=matched_refs)

if __name__ == "__main__":
    main()

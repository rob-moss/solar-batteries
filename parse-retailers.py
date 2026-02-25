#!/usr/bin/env python3
"""Parse AER retailers PDF text and create Markdown file."""

# Read the extracted text
with open('/tmp/aer_retailers_text.txt', 'r') as f:
    lines = f.readlines()

# Find where data starts (after "CDR Brand" header)
data_start = None
for i, line in enumerate(lines):
    if 'CDR Brand' in line:
        data_start = i + 1
        break

if data_start is None:
    print("ERROR: Could not find 'CDR Brand' header")
    exit(1)

# Collect non-empty lines after header
non_empty_lines = []
for i in range(data_start, len(lines)):
    stripped = lines[i].strip()
    if stripped:
        non_empty_lines.append(stripped)

# Group into triplets: name, URI, brand
retailers = []
for i in range(0, len(non_empty_lines) - 2, 3):
    name = non_empty_lines[i]
    uri = non_empty_lines[i + 1]
    brand = non_empty_lines[i + 2]
    
    if uri.startswith('https://'):
        retailers.append({
            'name': name,
            'uri': uri,
            'brand': brand
        })

# Create Markdown table
markdown_content = """# AER Energy - Retailer Base URIs and CDR Brands

This document contains the official list of energy retailers participating in the Consumer Data Right (CDR) scheme, 
their base URIs, and CDR brand identifiers as of January 2026.

| Retailer Name | Base URI | CDR Brand |
|---|---|---|
"""

for retailer in retailers:
    markdown_content += f"| {retailer['name']} | {retailer['uri']} | {retailer['brand']} |\n"

markdown_content += "\n"

# Write output file
with open('aer-api-retailers.md', 'w') as f:
    f.write(markdown_content)

print(f"✓ Created aer-api-retailers.md with {len(retailers)} retailers")

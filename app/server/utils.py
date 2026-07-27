"""Shared utility functions."""

import html
import re
import json
from urllib.parse import urlparse


def normalize_url(url):
    """Remove query parameters and trailing slash from URL for duplicate detection."""
    if not url:
        return url
    parsed = urlparse(url)
    base_url = f'{parsed.scheme}://{parsed.netloc}{parsed.path}'
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return base_url


def stream_json(data):
    """Return JSON data as a dictionary (for FastAPI auto-serialization)."""
    return data


def mask_pii(text):
    """Mask personally identifiable information for safe sharing."""
    masked = text
    masked = re.sub(r'[\+]?\d[\d\s\-\(\)]{8,15}', '[PHONE]', masked)
    masked = re.sub(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', '[EMAIL]', masked)
    masked = re.sub(r'linkedin\.com/in/[^\s]+', 'linkedin.com/in/[PROFILE]', masked)
    masked = re.sub(r'github\.com/[^\s]+', 'github.com/[PROFILE]', masked)
    lines = masked.split('\n')
    if lines and len(lines[0].strip()) < 60 and not any(c in lines[0] for c in '@:;#'):
        lines[0] = '[NAME]'
        masked = '\n'.join(lines)
    return masked


def text_to_html(text):
    """Convert plain text resume to simple HTML."""
    lines = text.split('\n')
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append('<br>')
            continue
        escaped = html.escape(line)
        if line.isupper() or line in ('Summary', 'Professional Experience', 'Skills', 'Education', 'Languages'):
            html_lines.append(f'<h3 style="margin:0.5em 0 0.2em;color:#e6edf3;font-size:14px;border-bottom:1px solid #30363d;padding-bottom:2px">{escaped}</h3>')
        elif line.startswith('●') or line.startswith('•') or line.startswith('-'):
            html_lines.append(f'<div style="margin:2px 0;padding-left:1em">{escaped}</div>')
        elif '|' in line and ('Engineer' in line or 'Developer' in line):
            html_lines.append(f'<div style="font-weight:600;color:#c9d1d9;margin:4px 0 2px">{escaped}</div>')
        else:
            html_lines.append(f'<div style="margin:2px 0">{escaped}</div>')
    return '\n'.join(html_lines)

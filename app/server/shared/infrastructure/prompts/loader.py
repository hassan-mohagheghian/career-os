"""Prompt template loader."""

import os

# Base directory for prompt templates — resolved relative to this file
# shared/infrastructure/prompts/ → go up 3 levels to app/server/
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


def load_prompt(name, **kwargs):
    """Load a prompt template and fill in variables.

    Supports both flat ('step8_score') and nested ('insights/career_intelligence') names.
    Searches all bounded context prompt directories.
    """
    # Search across all bounded context prompt directories
    search_dirs = [
        os.path.join(_BASE_DIR, 'companies', 'infrastructure', 'ai', 'prompts'),
        os.path.join(_BASE_DIR, 'jobs', 'infrastructure', 'ai', 'prompts'),
        os.path.join(_BASE_DIR, 'career', 'infrastructure', 'ai', 'prompts'),
        os.path.join(_BASE_DIR, 'skills', 'infrastructure', 'ai', 'prompts'),
        os.path.join(_BASE_DIR, 'resume', 'infrastructure', 'ai', 'prompts'),
    ]

    for prompts_dir in search_dirs:
        template_path = os.path.join(prompts_dir, f'{name}.txt')
        if os.path.exists(template_path):
            with open(template_path) as f:
                template = f.read()
            return template.format(**kwargs)

    raise FileNotFoundError(
        f"Prompt not found: {name}.txt (searched {len(search_dirs)} prompt directories)"
    )

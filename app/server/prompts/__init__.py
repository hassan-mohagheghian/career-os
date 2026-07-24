import os

PROMPTS_DIR = os.path.dirname(__file__)

def load_prompt(name, **kwargs):
    """Load a prompt template and fill in variables.

    Supports both flat ('step8_score') and nested ('career_intel/career_intelligence') names.
    Falls back to flat lookup if nested path doesn't exist.
    """
    # Try nested path first (e.g. 'career_intel/career_intelligence')
    nested_path = os.path.join(PROMPTS_DIR, f'{name}.txt')
    if os.path.exists(nested_path):
        with open(nested_path) as f:
            template = f.read()
        return template.format(**kwargs)
    raise FileNotFoundError(f"Prompt not found: {name}.txt (searched {PROMPTS_DIR})")

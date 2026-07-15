import os

PROMPTS_DIR = os.path.dirname(__file__)

def load_prompt(name, **kwargs):
    """Load a prompt template and fill in variables."""
    path = os.path.join(PROMPTS_DIR, f'{name}.txt')
    with open(path) as f:
        template = f.read()
    return template.format(**kwargs)

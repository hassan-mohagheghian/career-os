from .extract import register_job_extraction_prompts
from .score import register_job_score_prompts
from .summarize import register_job_summary_prompts

__all__ = [
    "register_job_extraction_prompts",
    "register_job_score_prompts",
    "register_job_summary_prompts",
]

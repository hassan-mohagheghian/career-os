from langchain_core.prompts import ChatPromptTemplate

from ..base import PromptSpec, PromptType
from ..inputs import JobSummaryInput
from ..registry import get_registry
from ..template import PromptTemplate


TEMPLATE_STR = """You are a job posting summarizer. Create a concise summary of the following job posting.

Job Information:
- Title: {title}
- Company: {company}
- Location: {location}
- Tech Stack: {stack}
- Description: {description}
- Requirements: {requirements}
- Benefits: {benefits}

Create a summary that includes:
1. Key Responsibilities
2. Required Skills
3. What Makes This Role Attractive
4. Career Growth Potential
5. Team/Company Culture Highlights

Keep the summary concise and actionable."""


def build_prompt_template() -> PromptTemplate:
    langchain_template = ChatPromptTemplate.from_messages([
        ("system", TEMPLATE_STR),
    ])
    spec = PromptSpec(
        identifier="job.summary",
        version="1.0.0",
        description="Generate a concise summary of a job posting",
        owner="jobs",
        prompt_type=PromptType.SUMMARIZATION,
        supported_providers=["any"],
        tags=["job", "summary", "concise"],
        input_schema=JobSummaryInput.model_json_schema(),
    )
    return PromptTemplate(template=langchain_template, spec=spec)


def register_job_summary_prompts() -> None:
    get_registry().register(build_prompt_template())

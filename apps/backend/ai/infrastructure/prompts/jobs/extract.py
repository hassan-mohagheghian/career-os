from langchain_core.prompts import ChatPromptTemplate

from ..base import PromptSpec, PromptType
from ..inputs import JobExtractionInput
from ..registry import get_registry
from ..template import PromptTemplate


TEMPLATE_STR = """You are a job posting analyzer. Extract structured information from the following job posting content.

Job Content:
{content}

Extract the following fields:
- title: Job title/position
- company: Company name
- location: Job location
- salary: Salary range (if mentioned)
- stack: Required tech stack
- description: Job description
- requirements: Job requirements
- benefits: Benefits offered

Return the extracted information in a structured JSON format."""


def build_prompt_template() -> PromptTemplate:
    langchain_template = ChatPromptTemplate.from_messages([
        ("system", TEMPLATE_STR),
    ])
    spec = PromptSpec(
        identifier="job.extract",
        version="1.0.0",
        description="Extract structured job data from raw posting content",
        owner="jobs",
        prompt_type=PromptType.EXTRACTION,
        supported_providers=["any"],
        tags=["job", "extraction", "structured"],
        input_schema=JobExtractionInput.model_json_schema(),
    )
    return PromptTemplate(template=langchain_template, spec=spec)


def register_job_extraction_prompts() -> None:
    get_registry().register(build_prompt_template())

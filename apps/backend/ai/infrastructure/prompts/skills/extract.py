from langchain_core.prompts import ChatPromptTemplate

from ..base import PromptSpec, PromptType
from ..inputs import SkillExtractionInput
from ..registry import get_registry
from ..template import PromptTemplate


TEMPLATE_STR = """You are a skills analyst. Extract and categorize skills from job postings.

Job Postings:
{job_data}

For each job posting, extract:
1. Technical skills (programming languages, frameworks, tools)
2. Soft skills (communication, leadership, teamwork)
3. Domain skills (industry-specific knowledge)
4. Certifications or qualifications

Categorize each skill as:
- programming_languages
- frameworks
- databases
- cloud_platforms
- tools
- soft_skills

Also note the frequency of each skill across all job postings.

Return a structured JSON with skills, categories, and frequency data."""


def build_prompt_template() -> PromptTemplate:
    langchain_template = ChatPromptTemplate.from_messages([
        ("system", TEMPLATE_STR),
    ])
    spec = PromptSpec(
        identifier="skills.extract",
        version="1.0.0",
        description="Extract and categorize skills from job postings",
        owner="skills",
        prompt_type=PromptType.EXTRACTION,
        supported_providers=["any"],
        tags=["skills", "extraction", "categorization"],
        input_schema=SkillExtractionInput.model_json_schema(),
    )
    return PromptTemplate(template=langchain_template, spec=spec)


def register_skill_extraction_prompts() -> None:
    get_registry().register(build_prompt_template())

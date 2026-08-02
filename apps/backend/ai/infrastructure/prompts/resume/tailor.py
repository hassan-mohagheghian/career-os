from langchain_core.prompts import ChatPromptTemplate

from ..base import PromptSpec, PromptType
from ..inputs import ResumeTailorInput
from ..registry import get_registry
from ..template import PromptTemplate


TEMPLATE_STR = """You are a resume tailoring expert. Tailor the following resume for the specific job posting.

Job Information:
- Title: {job_title}
- Company: {job_company}
- Requirements: {job_requirements}
- Tech Stack: {job_stack}

Original Resume:
{resume_text}

Create a tailored version that:
1. Highlights relevant experience for this specific role
2. Emphasizes matching technical skills
3. Adjusts bullet points to align with job requirements
4. Maintains professional formatting
5. Keeps the most impactful achievements prominent

Return the tailored resume in a clean, professional format."""


def build_prompt_template() -> PromptTemplate:
    langchain_template = ChatPromptTemplate.from_messages([
        ("system", TEMPLATE_STR),
    ])
    spec = PromptSpec(
        identifier="resume.tailor",
        version="1.0.0",
        description="Tailor a resume for a specific job posting",
        owner="resume",
        prompt_type=PromptType.USER,
        supported_providers=["any"],
        tags=["resume", "tailoring", "job-match"],
        input_schema=ResumeTailorInput.model_json_schema(),
    )
    return PromptTemplate(template=langchain_template, spec=spec)


def register_resume_tailor_prompts() -> None:
    get_registry().register(build_prompt_template())

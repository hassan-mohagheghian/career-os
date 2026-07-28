from langchain_core.prompts import ChatPromptTemplate

from ..base import PromptSpec, PromptType
from ..inputs import CoverLetterInput
from ..registry import get_registry
from ..template import PromptTemplate


TEMPLATE_STR = """You are a professional cover letter writer. Create a compelling cover letter for this position.

Job Information:
- Title: {job_title}
- Company: {job_company}
- Description: {job_description}
- Requirements: {job_requirements}

Candidate Background:
{resume_text}

Write a cover letter that:
1. Opens with genuine enthusiasm for the role and company
2. Highlights 2-3 most relevant experiences from the resume
3. Shows knowledge of the company's mission, products, or culture
4. Demonstrates how the candidate's skills solve the company's problems
5. Closes with a confident call to action

Tone: Professional yet personable
Length: 3-4 paragraphs
Format: Standard business letter format

Return the cover letter text."""


def build_prompt_template() -> PromptTemplate:
    langchain_template = ChatPromptTemplate.from_messages([
        ("system", TEMPLATE_STR),
    ])
    spec = PromptSpec(
        identifier="resume.cover-letter",
        version="1.0.0",
        description="Generate a tailored cover letter for a job application",
        owner="resume",
        prompt_type=PromptType.USER,
        supported_providers=["any"],
        tags=["resume", "cover-letter", "job-application"],
        input_schema=CoverLetterInput.model_json_schema(),
    )
    return PromptTemplate(template=langchain_template, spec=spec)


def register_cover_letter_prompts() -> None:
    get_registry().register(build_prompt_template())

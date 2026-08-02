from langchain_core.prompts import ChatPromptTemplate

from ..base import PromptSpec, PromptType
from ..inputs import JobScoreInput
from ..registry import get_registry
from ..template import PromptTemplate


TEMPLATE_STR = """You are a job fit analyzer. Analyze the following job posting and provide a fit score.

Job Information:
- Title: {title}
- Company: {company}
- Location: {location}
- Tech Stack: {stack}
- Description: {description}

User Profile:
- Skills: {user_skills}
- Experience: {user_experience}
- Preferences: {user_preferences}

Provide:
1. Fit Score (0-100): How well the job matches the user's profile
2. Success Score (0-100): Probability of successfully getting the job
3. Match Level: High/Medium/Low
4. Key Match Factors: List of factors that match
5. Potential Concerns: List of concerns or gaps

Return the analysis in a structured JSON format."""


def build_prompt_template() -> PromptTemplate:
    langchain_template = ChatPromptTemplate.from_messages([
        ("system", TEMPLATE_STR),
    ])
    spec = PromptSpec(
        identifier="job.score",
        version="1.0.0",
        description="Score and analyze job fit for the user's profile",
        owner="jobs",
        prompt_type=PromptType.EVALUATION,
        supported_providers=["any"],
        tags=["job", "scoring", "fit"],
        input_schema=JobScoreInput.model_json_schema(),
    )
    return PromptTemplate(template=langchain_template, spec=spec)


def register_job_score_prompts() -> None:
    get_registry().register(build_prompt_template())

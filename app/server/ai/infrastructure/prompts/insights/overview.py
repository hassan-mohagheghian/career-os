from langchain_core.prompts import ChatPromptTemplate

from ..base import PromptSpec, PromptType
from ..inputs import CareerInsightsInput
from ..registry import get_registry
from ..template import PromptTemplate


TEMPLATE_STR = """You are a career insights analyst. Generate a comprehensive career overview.

Career Data:
- Total Jobs Tracked: {job_count}
- Total Skills: {skill_count}
- Health Score: {health_score}

Generate an overview that includes:
1. Career Health Assessment: Overall career trajectory
2. Key Strengths: Top skills and experiences
3. Areas for Improvement: Skills that need development
4. Market Position: How competitive the candidate is
5. Action Items: Top 3 things to do next

Keep the summary concise and actionable."""


def build_prompt_template() -> PromptTemplate:
    langchain_template = ChatPromptTemplate.from_messages([
        ("system", TEMPLATE_STR),
    ])
    spec = PromptSpec(
        identifier="insights.overview",
        version="1.0.0",
        description="Generate a comprehensive career overview and insights",
        owner="career",
        prompt_type=PromptType.SUMMARIZATION,
        supported_providers=["any"],
        tags=["career", "insights", "overview"],
        input_schema=CareerInsightsInput.model_json_schema(),
    )
    return PromptTemplate(template=langchain_template, spec=spec)


def register_career_insights_prompts() -> None:
    get_registry().register(build_prompt_template())

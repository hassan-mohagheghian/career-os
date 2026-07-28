from langchain_core.prompts import ChatPromptTemplate

from ..base import PromptSpec, PromptType
from ..inputs import RoadmapInput
from ..registry import get_registry
from ..template import PromptTemplate


TEMPLATE_STR = """You are a career development advisor. Analyze skill gaps and create a learning roadmap.

Current Skills:
{current_skills}

Market Demand (from job postings):
{market_demand}

Create a learning roadmap that:
1. Identifies the top 10 skills to learn or improve
2. Prioritizes based on market demand and career impact
3. Estimates learning time for each skill
4. Suggests learning resources (courses, projects, certifications)
5. Defines milestones for progress tracking

For each skill in the roadmap, provide:
- skill: Skill name
- priority: high/medium/low
- current_level: Current proficiency (0-5)
- target_level: Target proficiency (0-5)
- estimated_time: Time to reach target
- learning_resources: Suggested resources
- milestones: Progress checkpoints

Return the roadmap as a structured JSON."""


def build_prompt_template() -> PromptTemplate:
    langchain_template = ChatPromptTemplate.from_messages([
        ("system", TEMPLATE_STR),
    ])
    spec = PromptSpec(
        identifier="skills.roadmap",
        version="1.0.0",
        description="Generate a learning roadmap based on skill gaps",
        owner="skills",
        prompt_type=PromptType.SUMMARIZATION,
        supported_providers=["any"],
        tags=["skills", "roadmap", "learning"],
        input_schema=RoadmapInput.model_json_schema(),
    )
    return PromptTemplate(template=langchain_template, spec=spec)


def register_roadmap_prompts() -> None:
    get_registry().register(build_prompt_template())

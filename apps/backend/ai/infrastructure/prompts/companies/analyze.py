from langchain_core.prompts import ChatPromptTemplate

from ..base import PromptSpec, PromptType
from ..inputs import CompanyAnalysisInput
from ..registry import get_registry
from ..template import PromptTemplate


TEMPLATE_STR = """You are a company intelligence analyst. Analyze the following company data and provide insights.

Company Information:
- Name: {name}
- Type: {company_type}
- Industry: {industry}
- Size: {size}
- Location: {location}
- Tech Stack: {tech_stack}
- Visa Sponsorship: {visa_sponsorship}

Provide:
1. Fit Score (0-100): How well this company matches the user's career goals
2. Success Score (0-100): Probability of successfully getting hired
3. Overall Score (0-100): Combined score
4. Culture Assessment: Company culture analysis
5. Growth Potential: Career growth opportunities
6. Visa Assessment: Visa sponsorship likelihood and process
7. Key Strengths: List of company strengths
8. Potential Concerns: List of concerns or risks

Return the analysis in a structured JSON format."""


def build_prompt_template() -> PromptTemplate:
    langchain_template = ChatPromptTemplate.from_messages([
        ("system", TEMPLATE_STR),
    ])
    spec = PromptSpec(
        identifier="company.analyze",
        version="1.0.0",
        description="Analyze company data and provide intelligence insights",
        owner="companies",
        prompt_type=PromptType.EVALUATION,
        supported_providers=["any"],
        tags=["company", "analysis", "intelligence"],
        input_schema=CompanyAnalysisInput.model_json_schema(),
    )
    return PromptTemplate(template=langchain_template, spec=spec)


def register_company_analysis_prompts() -> None:
    get_registry().register(build_prompt_template())

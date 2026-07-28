from langchain_core.prompts import ChatPromptTemplate

from ..base import PromptSpec, PromptType
from ..inputs import CompanyExtractionInput
from ..registry import get_registry
from ..template import PromptTemplate


TEMPLATE_STR = """You are a company data extractor. Extract structured information from the following company content.

Company Content:
{content}

Extract the following fields:
- name: Company name
- company_type: Type of company (STARTUP, SME, ENTERPRISE, AGENCY, etc.)
- industry: Industry sector
- size: Company size (employees)
- location: Headquarters location
- website: Company website
- description: Company description
- tech_stack: Technologies used
- visa_sponsorship: Whether they sponsor visas (true/false/null)

Return the extracted information in a structured JSON format."""


def build_prompt_template() -> PromptTemplate:
    langchain_template = ChatPromptTemplate.from_messages([
        ("system", TEMPLATE_STR),
    ])
    spec = PromptSpec(
        identifier="company.extract",
        version="1.0.0",
        description="Extract structured company data from raw content",
        owner="companies",
        prompt_type=PromptType.EXTRACTION,
        supported_providers=["any"],
        tags=["company", "extraction", "structured"],
        input_schema=CompanyExtractionInput.model_json_schema(),
    )
    return PromptTemplate(template=langchain_template, spec=spec)


def register_company_extraction_prompts() -> None:
    get_registry().register(build_prompt_template())

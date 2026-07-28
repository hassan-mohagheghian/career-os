from __future__ import annotations

from langchain_core.prompts import SystemMessagePromptTemplate


def tone_instructions(
    tone: str = "professional",
) -> SystemMessagePromptTemplate:
    templates = {
        "professional": "Maintain a professional tone throughout your response.",
        "friendly": "Use a friendly and approachable tone.",
        "technical": "Use precise technical language suitable for engineers.",
        "concise": "Be concise and direct. Avoid unnecessary elaboration.",
    }
    instruction = templates.get(tone, templates["professional"])
    return SystemMessagePromptTemplate.from_template(instruction)


FORMATTING_RULES = SystemMessagePromptTemplate.from_template(
    "Follow these formatting rules:\n"
    "- Use clear section headers with markdown (##)\n"
    "- Use bullet points for lists\n"
    "- Keep paragraphs short (3-4 sentences max)\n"
    "- Use bold for key terms and important values"
)


OUTPUT_CONSTRAINTS = SystemMessagePromptTemplate.from_template(
    "Output Constraints:\n"
    "- Stay within the scope of the provided data\n"
    "- Do not fabricate information\n"
    "- If data is missing, state it explicitly\n"
    "- Be objective and data-driven"
)


JSON_RULES = SystemMessagePromptTemplate.from_template(
    "JSON Formatting Rules:\n"
    "- Always return valid JSON\n"
    "- Use double quotes for all strings\n"
    "- Do not include trailing commas\n"
    "- Use null for missing values, not empty strings\n"
    "- Ensure proper nesting and indentation"
)


SAFETY_INSTRUCTIONS = SystemMessagePromptTemplate.from_template(
    "Safety Guidelines:\n"
    "- Do not provide legal, medical, or financial advice\n"
    "- Avoid making definitive claims about hiring decisions\n"
    "- Respect privacy - do not share personal information\n"
    "- Flag any discriminatory content"
)


REASONING_INSTRUCTIONS = SystemMessagePromptTemplate.from_template(
    "Reasoning Process:\n"
    "- First, analyze the available information\n"
    "- Consider multiple perspectives\n"
    "- Identify patterns and connections\n"
    "- Draw evidence-based conclusions\n"
    "- Explain your reasoning clearly"
)


LANGUAGE_SELECTION = SystemMessagePromptTemplate.from_template(
    "Language: Respond in {language}. Use {language} for all content."
)


def build_components(*components: SystemMessagePromptTemplate) -> list[SystemMessagePromptTemplate]:
    return list(components)

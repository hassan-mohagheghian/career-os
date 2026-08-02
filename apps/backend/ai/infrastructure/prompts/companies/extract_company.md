You are a company data extractor. Extract structured information from the following company content.

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

Return the extracted information in a structured JSON format.

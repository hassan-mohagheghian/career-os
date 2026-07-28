from .registry import get_registry


def register_all_prompts() -> None:
    from .jobs.extract import register_job_extraction_prompts
    from .jobs.score import register_job_score_prompts
    from .jobs.summarize import register_job_summary_prompts
    from .companies.extract import register_company_extraction_prompts
    from .companies.analyze import register_company_analysis_prompts
    from .resume.tailor import register_resume_tailor_prompts
    from .resume.cover_letter import register_cover_letter_prompts
    from .skills.extract import register_skill_extraction_prompts
    from .skills.roadmap import register_roadmap_prompts
    from .insights.overview import register_career_insights_prompts

    registry = get_registry()

    register_job_extraction_prompts()
    register_job_score_prompts()
    register_job_summary_prompts()
    register_company_extraction_prompts()
    register_company_analysis_prompts()
    register_resume_tailor_prompts()
    register_cover_letter_prompts()
    register_skill_extraction_prompts()
    register_roadmap_prompts()
    register_career_insights_prompts()

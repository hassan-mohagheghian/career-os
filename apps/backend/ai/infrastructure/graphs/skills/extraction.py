"""Skill Extraction Graph — LangGraph workflow for extracting skills from job postings.

Graph: START → load_jobs → extract_skills → categorize → enrich → END

Design Pattern: Pipeline Pattern — sequential data transformation.
Each node owns its own prompt and produces typed output.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Optional

from ..runtime.graph import GraphBuilder
from ..runtime.state import BaseState, SkillExtractionOutput


def build_skill_extraction_graph() -> GraphBuilder:
    """Build the skill extraction workflow graph.

    Returns a compiled GraphBuilder ready for execution.
    """

    def load_jobs(state: BaseState) -> BaseState:
        """Stage 1: Load Jobs.

        Loads recent job postings for skill extraction.
        """
        job_ids = state["context"].get("job_ids", [])

        if job_ids:
            state["metadata"]["job_ids"] = job_ids
            return state

        # Load recent jobs if no specific IDs provided
        try:
            from shared.infrastructure.database.session import get_session_sync
            from jobs.infrastructure.models.job_model import JobModel

            session = get_session_sync()
            jobs = session.query(
                JobModel.id, JobModel.role, JobModel.description, JobModel.stack
            ).filter(JobModel.deleted == 0).order_by(
                JobModel.created_at.desc()
            ).limit(50).all()

            state["metadata"]["jobs"] = [
                {
                    "id": r.id,
                    "role": r.role or "",
                    "description": r.description or "",
                    "stack": r.stack or "",
                }
                for r in jobs
            ] if jobs else []
        except Exception as e:
            state["errors"].append(f"Failed to load jobs: {e}")

        return state

    def extract_skills(state: BaseState) -> BaseState:
        """Stage 2: Extract Skills.

        Extracts skills from job descriptions and stacks.
        Uses prompt: skills/extract_skills.md
        """
        jobs = state["metadata"].get("jobs", [])

        if not jobs:
            state["errors"].append("No jobs to extract skills from")
            return state

        try:
            all_skills = set()
            skill_sources = {}

            for job in jobs:
                stack = job.get("stack", "")
                description = job.get("description", "")

                # Extract from stack
                if stack:
                    for skill in stack.split(","):
                        skill = skill.strip()
                        if skill:
                            all_skills.add(skill)
                            skill_sources.setdefault(skill, []).append(
                                job.get("id", "unknown")
                            )

                # Extract from description (simple keyword matching)
                if description:
                    # Common tech keywords
                    tech_keywords = [
                        "python", "javascript", "typescript", "react", "vue",
                        "angular", "node", "fastapi", "django", "flask",
                        "postgresql", "mysql", "mongodb", "redis", "docker",
                        "kubernetes", "aws", "gcp", "azure", "git", "linux",
                        "java", "go", "rust", "c++", "sql", "nosql",
                        "graphql", "rest", "api", "microservices", "ci/cd",
                    ]
                    desc_lower = description.lower()
                    for keyword in tech_keywords:
                        if keyword in desc_lower:
                            all_skills.add(keyword)
                            skill_sources.setdefault(keyword, []).append(
                                job.get("id", "unknown")
                            )

            state["metadata"]["extracted_skills"] = list(all_skills)
            state["metadata"]["skill_sources"] = skill_sources
            state["metadata"]["extract"] = {
                "success": True,
                "skill_count": len(all_skills),
            }
        except Exception as e:
            state["errors"].append(f"Skill extraction failed: {e}")
            state["metadata"]["extract"] = {"success": False, "error": str(e)}

        return state

    def categorize_skills(state: BaseState) -> BaseState:
        """Stage 3: Categorize Skills.

        Categorizes extracted skills into groups.
        """
        skills = state["metadata"].get("extracted_skills", [])

        if not skills:
            state["metadata"]["categories"] = {}
            return state

        try:
            categories = {
                "programming_languages": [],
                "frameworks": [],
                "databases": [],
                "cloud_platforms": [],
                "tools": [],
                "soft_skills": [],
            }

            # Simple categorization rules
            lang_keywords = {"python", "javascript", "typescript", "java", "go", "rust", "c++"}
            framework_keywords = {"react", "vue", "angular", "fastapi", "django", "flask", "node"}
            db_keywords = {"postgresql", "mysql", "mongodb", "redis", "sql", "nosql"}
            cloud_keywords = {"aws", "gcp", "azure", "docker", "kubernetes"}
            tool_keywords = {"git", "linux", "ci/cd", "graphql", "rest", "api", "microservices"}

            for skill in skills:
                skill_lower = skill.lower()
                if skill_lower in lang_keywords:
                    categories["programming_languages"].append(skill)
                elif skill_lower in framework_keywords:
                    categories["frameworks"].append(skill)
                elif skill_lower in db_keywords:
                    categories["databases"].append(skill)
                elif skill_lower in cloud_keywords:
                    categories["cloud_platforms"].append(skill)
                elif skill_lower in tool_keywords:
                    categories["tools"].append(skill)
                else:
                    categories["tools"].append(skill)

            state["metadata"]["categories"] = categories
            state["metadata"]["categorize"] = {"success": True}
        except Exception as e:
            state["errors"].append(f"Categorization failed: {e}")
            state["metadata"]["categorize"] = {"success": False, "error": str(e)}

        return state

    def enrich_skills(state: BaseState) -> BaseState:
        """Stage 4: Enrich Skills.

        Enriches skills with frequency and demand data.
        """
        skills = state["metadata"].get("extracted_skills", [])
        sources = state["metadata"].get("skill_sources", {})

        if not skills:
            state["metadata"]["enriched_skills"] = []
            return state

        try:
            enriched = []
            for skill in skills:
                enriched.append({
                    "name": skill,
                    "frequency": len(sources.get(skill, [])),
                    "demand_level": "high" if len(sources.get(skill, [])) > 5 else "medium",
                })

            # Sort by frequency
            enriched.sort(key=lambda x: x["frequency"], reverse=True)

            state["metadata"]["enriched_skills"] = enriched
            state["metadata"]["enrich"] = {"success": True}
        except Exception as e:
            state["errors"].append(f"Enrichment failed: {e}")
            state["metadata"]["enrich"] = {"success": False, "error": str(e)}

        return state

    def completion_event(state: BaseState) -> BaseState:
        """Stage 5: Completion Event.

        Builds final typed output.
        """
        enriched = state["metadata"].get("enriched_skills", [])
        categories = state["metadata"].get("categories", {})

        output = SkillExtractionOutput(
            skills=enriched,
            categories=categories,
            raw_skills=[s["name"] for s in enriched],
        )

        state["output"] = json.dumps(output.model_dump(), default=str)
        state["metadata"]["completion"] = {"success": True}
        state["metadata"]["typed_output"] = output.model_dump()

        return state

    # Build the graph
    builder = GraphBuilder("skill_extraction")
    builder.add_node("load_jobs", load_jobs)
    builder.add_node("extract_skills", extract_skills)
    builder.add_node("categorize_skills", categorize_skills)
    builder.add_node("enrich_skills", enrich_skills)
    builder.add_node("completion_event", completion_event)

    builder.add_edge("load_jobs", "extract_skills")
    builder.add_edge("extract_skills", "categorize_skills")
    builder.add_edge("categorize_skills", "enrich_skills")
    builder.add_edge("enrich_skills", "completion_event")

    builder.set_entry("load_jobs")
    builder.set_finish("completion_event")

    return builder

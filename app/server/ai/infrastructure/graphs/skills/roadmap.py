"""Skill Roadmap Generation Graph — LangGraph workflow for learning roadmaps.

Graph: START → load_skills → load_market → analyze_gaps → generate_roadmap → prioritize → END

Design Pattern: Pipeline Pattern — sequential data transformation.
Each node owns its own prompt and produces typed output.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Optional

from ..runtime.graph import GraphBuilder
from ..runtime.state import BaseState, SkillRoadmapOutput


def build_skill_roadmap_graph() -> GraphBuilder:
    """Build the skill roadmap generation workflow graph.

    Returns a compiled GraphBuilder ready for execution.
    """

    def load_current_skills(state: BaseState) -> BaseState:
        """Stage 1: Load Current Skills.

        Loads the user's current skills from database.
        """
        try:
            from shared.infrastructure.database.session import get_session_sync
            from skills.infrastructure.models.skill_model import SkillModel

            session = get_session_sync()
            rows = session.query(
                SkillModel.name, SkillModel.level, SkillModel.category
            ).order_by(SkillModel.level.desc()).all()

            state["metadata"]["current_skills"] = [
                {"name": r.name, "level": r.level, "category": r.category}
                for r in rows
            ] if rows else []
        except Exception as e:
            state["errors"].append(f"Failed to load skills: {e}")

        return state

    def load_market_data(state: BaseState) -> BaseState:
        """Stage 2: Load Market Data.

        Loads market demand data from job postings.
        """
        try:
            from shared.infrastructure.database.session import get_session_sync
            from jobs.infrastructure.models.job_model import JobModel

            session = get_session_sync()
            jobs = session.query(
                JobModel.stack, JobModel.requirements
            ).filter(JobModel.deleted == 0).order_by(
                JobModel.created_at.desc()
            ).limit(100).all()

            # Aggregate skill demand
            skill_demand = {}
            for job in jobs:
                stack = job.stack or ""
                for skill in stack.split(","):
                    skill = skill.strip()
                    if skill:
                        skill_demand[skill] = skill_demand.get(skill, 0) + 1

            state["metadata"]["market_demand"] = skill_demand
            state["metadata"]["market_jobs_analyzed"] = len(jobs)
        except Exception as e:
            state["errors"].append(f"Failed to load market data: {e}")

        return state

    def analyze_gaps(state: BaseState) -> BaseState:
        """Stage 3: Analyze Skill Gaps.

        Compares current skills against market demand.
        Uses prompt: skills/analyze_gaps.md
        """
        current_skills = state["metadata"].get("current_skills", [])
        market_demand = state["metadata"].get("market_demand", {})

        if not market_demand:
            state["metadata"]["gaps"] = []
            return state

        try:
            current_names = {s["name"].lower() for s in current_skills if s.get("name")}
            current_levels = {s["name"].lower(): s.get("level", 0) for s in current_skills}

            gaps = []
            for skill, demand in sorted(market_demand.items(), key=lambda x: x[1], reverse=True):
                if skill.lower() not in current_names:
                    gaps.append({
                        "skill": skill,
                        "demand": demand,
                        "current_level": 0,
                        "gap_type": "missing",
                    })
                elif current_levels.get(skill.lower(), 0) < 3:
                    gaps.append({
                        "skill": skill,
                        "demand": demand,
                        "current_level": current_levels.get(skill.lower(), 0),
                        "gap_type": "below_market",
                    })

            state["metadata"]["gaps"] = gaps
            state["metadata"]["analyze_gaps"] = {
                "success": True,
                "gap_count": len(gaps),
            }
        except Exception as e:
            state["errors"].append(f"Gap analysis failed: {e}")
            state["metadata"]["analyze_gaps"] = {"success": False, "error": str(e)}

        return state

    def generate_roadmap(state: BaseState) -> BaseState:
        """Stage 4: Generate Learning Roadmap.

        Creates a structured learning roadmap based on gaps.
        Uses prompt: skills/generate_roadmap.md
        """
        gaps = state["metadata"].get("gaps", [])

        if not gaps:
            state["metadata"]["roadmap"] = []
            return state

        try:
            roadmap = []
            for i, gap in enumerate(gaps[:10]):  # Top 10 gaps
                priority = "high" if gap["demand"] > 10 else "medium"
                estimated_time = "2-4 weeks" if gap["gap_type"] == "missing" else "1-2 weeks"

                roadmap.append({
                    "skill": gap["skill"],
                    "priority": priority,
                    "current_level": gap["current_level"],
                    "target_level": 3,
                    "estimated_time": estimated_time,
                    "learning_resources": [],
                    "milestones": [],
                })

            state["metadata"]["roadmap"] = roadmap
            state["metadata"]["generate_roadmap"] = {
                "success": True,
                "items": len(roadmap),
            }
        except Exception as e:
            state["errors"].append(f"Roadmap generation failed: {e}")
            state["metadata"]["generate_roadmap"] = {
                "success": False,
                "error": str(e),
            }

        return state

    def prioritize(state: BaseState) -> BaseState:
        """Stage 5: Prioritize Roadmap Items.

        Prioritizes roadmap items based on impact and effort.
        """
        roadmap = state["metadata"].get("roadmap", [])

        if not roadmap:
            state["metadata"]["prioritized_roadmap"] = []
            return state

        try:
            # Sort by priority and demand
            prioritized = sorted(
                roadmap,
                key=lambda x: (
                    0 if x["priority"] == "high" else 1,
                    -x.get("target_level", 0),
                ),
            )

            priorities = [item["skill"] for item in prioritized]
            timelines = {
                item["skill"]: item["estimated_time"]
                for item in prioritized
            }

            state["metadata"]["prioritized_roadmap"] = prioritized
            state["metadata"]["priorities"] = priorities
            state["metadata"]["timelines"] = timelines
            state["metadata"]["prioritize"] = {"success": True}
        except Exception as e:
            state["errors"].append(f"Prioritization failed: {e}")
            state["metadata"]["prioritize"] = {"success": False, "error": str(e)}

        return state

    def completion_event(state: BaseState) -> BaseState:
        """Stage 6: Completion Event.

        Builds final typed output.
        """
        roadmap = state["metadata"].get("prioritized_roadmap", [])
        priorities = state["metadata"].get("priorities", [])
        timelines = state["metadata"].get("timelines", {})

        output = SkillRoadmapOutput(
            roadmap=roadmap,
            priorities=priorities,
            estimated_timelines=timelines,
            learning_resources=[],
        )

        state["output"] = json.dumps(output.model_dump(), default=str)
        state["metadata"]["completion"] = {"success": True}
        state["metadata"]["typed_output"] = output.model_dump()

        return state

    # Build the graph
    builder = GraphBuilder("skill_roadmap")
    builder.add_node("load_current_skills", load_current_skills)
    builder.add_node("load_market_data", load_market_data)
    builder.add_node("analyze_gaps", analyze_gaps)
    builder.add_node("generate_roadmap", generate_roadmap)
    builder.add_node("prioritize", prioritize)
    builder.add_node("completion_event", completion_event)

    builder.add_edge("load_current_skills", "load_market_data")
    builder.add_edge("load_market_data", "analyze_gaps")
    builder.add_edge("analyze_gaps", "generate_roadmap")
    builder.add_edge("generate_roadmap", "prioritize")
    builder.add_edge("prioritize", "completion_event")

    builder.set_entry("load_current_skills")
    builder.set_finish("completion_event")

    return builder

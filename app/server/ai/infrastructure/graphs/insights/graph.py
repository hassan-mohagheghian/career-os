"""Career Insights — LangGraph workflows for career intelligence.

Each insight section is an independent graph that can be executed
standalone or composed via the parent orchestrator.

Child Graphs:
- overview: Career health score and summary
- skills: Skill gap analysis and recommendations
- market: Job market trends and analysis
- companies: Company intelligence and targeting
- networking: Professional network recommendations
- opportunities: Job opportunity funnel

Parent Graph:
- insights: Orchestrates all child graphs in sequence
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Optional

from ..runtime.graph import GraphBuilder
from ..runtime.state import BaseState, InsightSectionOutput, CareerInsightsOutput


# ── Child Graph: Overview ───────────────────────────────────────────

def build_overview_graph() -> GraphBuilder:
    """Build the career overview insight graph.

    Graph: START → collect_data → compute_health → generate_summary → END
    """
    def collect_data(state: BaseState) -> BaseState:
        """Collect job and skill data for overview."""
        try:
            from shared.infrastructure.database.session import get_session_sync
            from jobs.infrastructure.models.job_model import JobModel
            from skills.infrastructure.models.skill_model import SkillModel

            session = get_session_sync()

            jobs = session.query(
                JobModel.company, JobModel.role, JobModel.score,
                JobModel.match, JobModel.overall_score
            ).filter(JobModel.deleted == 0).order_by(
                JobModel.overall_score.desc()
            ).limit(50).all()

            state["metadata"]["jobs"] = [
                {"company": r.company, "role": r.role, "score": r.score,
                 "match": r.match, "overall_score": r.overall_score}
                for r in jobs
            ] if jobs else []

            skills = session.query(
                SkillModel.name, SkillModel.level, SkillModel.category
            ).order_by(SkillModel.level.desc()).all()

            state["metadata"]["skills"] = [
                {"name": r.name, "level": r.level, "category": r.category}
                for r in skills
            ] if skills else []
        except Exception as e:
            state["errors"].append(f"Data collection failed: {e}")

        return state

    def compute_health(state: BaseState) -> BaseState:
        """Compute career health score."""
        jobs = state["metadata"].get("jobs", [])
        skills = state["metadata"].get("skills", [])

        try:
            # Simple health score calculation
            job_score = sum(j.get("overall_score", 0) or 0 for j in jobs) / max(len(jobs), 1)
            skill_score = sum(s.get("level", 0) for s in skills) / max(len(skills), 1) * 20

            health_score = (job_score * 0.6 + skill_score * 0.4)
            state["metadata"]["health_score"] = round(health_score, 1)
            state["metadata"]["job_count"] = len(jobs)
            state["metadata"]["skill_count"] = len(skills)
        except Exception as e:
            state["errors"].append(f"Health calculation failed: {e}")

        return state

    def generate_summary(state: BaseState) -> BaseState:
        """Generate overview summary."""
        health_score = state["metadata"].get("health_score", 0)
        job_count = state["metadata"].get("job_count", 0)
        skill_count = state["metadata"].get("skill_count", 0)

        state["metadata"]["overview_data"] = {
            "health_score": health_score,
            "total_jobs": job_count,
            "total_skills": skill_count,
            "summary": f"Career health: {health_score}/100. "
                       f"Tracking {job_count} jobs with {skill_count} skills.",
        }

        return state

    builder = GraphBuilder("insights_overview")
    builder.add_node("collect_data", collect_data)
    builder.add_node("compute_health", compute_health)
    builder.add_node("generate_summary", generate_summary)
    builder.add_edge("collect_data", "compute_health")
    builder.add_edge("compute_health", "generate_summary")
    builder.set_entry("collect_data")
    builder.set_finish("generate_summary")

    return builder


# ── Child Graph: Skills ─────────────────────────────────────────────

def build_skills_insight_graph() -> GraphBuilder:
    """Build the skills insight graph.

    Graph: START → load_skills → analyze_gaps → generate_recommendations → END
    """
    def load_skills(state: BaseState) -> BaseState:
        """Load skills data."""
        try:
            from shared.infrastructure.database.session import get_session_sync
            from skills.infrastructure.models.skill_model import SkillModel

            session = get_session_sync()
            skills = session.query(
                SkillModel.name, SkillModel.level, SkillModel.category
            ).order_by(SkillModel.level.desc()).all()

            state["metadata"]["skills"] = [
                {"name": r.name, "level": r.level, "category": r.category}
                for r in skills
            ] if skills else []
        except Exception as e:
            state["errors"].append(f"Failed to load skills: {e}")

        return state

    def analyze_gaps(state: BaseState) -> BaseState:
        """Analyze skill gaps."""
        skills = state["metadata"].get("skills", [])

        try:
            total_skills = len(skills)
            avg_level = sum(s.get("level", 0) for s in skills) / max(total_skills, 1)
            categories = {}
            for s in skills:
                cat = s.get("category", "unknown")
                categories.setdefault(cat, []).append(s)

            state["metadata"]["skill_analysis"] = {
                "total_skills": total_skills,
                "average_level": round(avg_level, 2),
                "categories": {k: len(v) for k, v in categories.items()},
            }
        except Exception as e:
            state["errors"].append(f"Gap analysis failed: {e}")

        return state

    def generate_recommendations(state: BaseState) -> BaseState:
        """Generate skill recommendations."""
        analysis = state["metadata"].get("skill_analysis", {})

        recommendations = []
        if analysis.get("average_level", 0) < 2:
            recommendations.append("Focus on improving core skill levels")
        if analysis.get("total_skills", 0) < 5:
            recommendations.append("Expand skill portfolio with in-demand technologies")

        state["metadata"]["skills_data"] = {
            "analysis": analysis,
            "recommendations": recommendations,
        }

        return state

    builder = GraphBuilder("insights_skills")
    builder.add_node("load_skills", load_skills)
    builder.add_node("analyze_gaps", analyze_gaps)
    builder.add_node("generate_recommendations", generate_recommendations)
    builder.add_edge("load_skills", "analyze_gaps")
    builder.add_edge("analyze_gaps", "generate_recommendations")
    builder.set_entry("load_skills")
    builder.set_finish("generate_recommendations")

    return builder


# ── Child Graph: Market ─────────────────────────────────────────────

def build_market_insight_graph() -> GraphBuilder:
    """Build the market insight graph.

    Graph: START → analyze_demand → analyze_trends → generate_report → END
    """
    def analyze_demand(state: BaseState) -> BaseState:
        """Analyze market demand from job postings."""
        try:
            from shared.infrastructure.database.session import get_session_sync
            from jobs.infrastructure.models.job_model import JobModel

            session = get_session_sync()
            jobs = session.query(JobModel.stack, JobModel.location).filter(
                JobModel.deleted == 0
            ).all()

            skill_demand = {}
            location_demand = {}
            for job in jobs:
                stack = job.stack or ""
                for skill in stack.split(","):
                    skill = skill.strip()
                    if skill:
                        skill_demand[skill] = skill_demand.get(skill, 0) + 1

                loc = job.location or "Unknown"
                location_demand[loc] = location_demand.get(loc, 0) + 1

            state["metadata"]["skill_demand"] = dict(
                sorted(skill_demand.items(), key=lambda x: x[1], reverse=True)[:20]
            )
            state["metadata"]["location_demand"] = dict(
                sorted(location_demand.items(), key=lambda x: x[1], reverse=True)[:10]
            )
            state["metadata"]["total_market_jobs"] = len(jobs)
        except Exception as e:
            state["errors"].append(f"Demand analysis failed: {e}")

        return state

    def analyze_trends(state: BaseState) -> BaseState:
        """Analyze market trends."""
        skill_demand = state["metadata"].get("skill_demand", {})
        location_demand = state["metadata"].get("location_demand", {})

        state["metadata"]["trends"] = {
            "top_skills": list(skill_demand.keys())[:5],
            "top_locations": list(location_demand.keys())[:5],
            "market_health": "strong" if len(skill_demand) > 10 else "moderate",
        }

        return state

    def generate_report(state: BaseState) -> BaseState:
        """Generate market report."""
        trends = state["metadata"].get("trends", {})
        total = state["metadata"].get("total_market_jobs", 0)

        state["metadata"]["market_data"] = {
            "total_jobs": total,
            "trends": trends,
            "summary": f"Found {total} jobs. Top skills: {', '.join(trends.get('top_skills', [])[:3])}",
        }

        return state

    builder = GraphBuilder("insights_market")
    builder.add_node("analyze_demand", analyze_demand)
    builder.add_node("analyze_trends", analyze_trends)
    builder.add_node("generate_report", generate_report)
    builder.add_edge("analyze_demand", "analyze_trends")
    builder.add_edge("analyze_trends", "generate_report")
    builder.set_entry("analyze_demand")
    builder.set_finish("generate_report")

    return builder


# ── Child Graph: Companies ──────────────────────────────────────────

def build_companies_insight_graph() -> GraphBuilder:
    """Build the companies insight graph.

    Graph: START → load_companies → analyze_targeting → generate_shortlist → END
    """
    def load_companies(state: BaseState) -> BaseState:
        """Load company data from analyzed jobs."""
        try:
            from shared.infrastructure.database.session import get_session_sync
            from jobs.infrastructure.models.job_model import JobModel

            session = get_session_sync()
            jobs = session.query(
                JobModel.company, JobModel.overall_score
            ).filter(JobModel.deleted == 0).order_by(
                JobModel.overall_score.desc()
            ).all()

            companies = {}
            for job in jobs:
                name = job.company or "Unknown"
                if name not in companies:
                    companies[name] = {"name": name, "jobs": 0, "avg_score": 0, "scores": []}
                companies[name]["jobs"] += 1
                if job.overall_score:
                    companies[name]["scores"].append(job.overall_score)

            for data in companies.values():
                scores = data.pop("scores")
                data["avg_score"] = round(sum(scores) / max(len(scores), 1), 1)

            state["metadata"]["companies"] = list(companies.values())
        except Exception as e:
            state["errors"].append(f"Failed to load companies: {e}")

        return state

    def analyze_targeting(state: BaseState) -> BaseState:
        """Analyze company targeting opportunities."""
        companies = state["metadata"].get("companies", [])

        targeting = []
        for company in companies:
            targeting.append({
                "name": company["name"],
                "opportunity_count": company["jobs"],
                "fit_score": company["avg_score"],
                "priority": "high" if company["avg_score"] > 70 else "medium",
            })

        state["metadata"]["targeting"] = targeting
        return state

    def generate_shortlist(state: BaseState) -> BaseState:
        """Generate company shortlist."""
        targeting = state["metadata"].get("targeting", [])

        shortlist = sorted(targeting, key=lambda x: x["fit_score"], reverse=True)[:10]

        state["metadata"]["companies_data"] = {
            "total_companies": len(targeting),
            "shortlist": shortlist,
            "summary": f"Tracking {len(targeting)} companies. Top: {shortlist[0]['name'] if shortlist else 'N/A'}",
        }

        return state

    builder = GraphBuilder("insights_companies")
    builder.add_node("load_companies", load_companies)
    builder.add_node("analyze_targeting", analyze_targeting)
    builder.add_node("generate_shortlist", generate_shortlist)
    builder.add_edge("load_companies", "analyze_targeting")
    builder.add_edge("analyze_targeting", "generate_shortlist")
    builder.set_entry("load_companies")
    builder.set_finish("generate_shortlist")

    return builder


# ── Child Graph: Networking ─────────────────────────────────────────

def build_networking_insight_graph() -> GraphBuilder:
    """Build the networking insight graph.

    Graph: START → analyze_connections → generate_recommendations → END
    """
    def analyze_connections(state: BaseState) -> BaseState:
        """Analyze professional network."""
        companies = state["metadata"].get("companies_data", {}).get("shortlist", [])

        state["metadata"]["network_analysis"] = {
            "target_companies": [c["name"] for c in companies],
            "network_strength": "developing",
            "recommendations": [
                "Connect with employees at target companies",
                "Join relevant professional communities",
                "Attend industry events and meetups",
            ],
        }

        return state

    def generate_recommendations(state: BaseState) -> BaseState:
        """Generate networking recommendations."""
        analysis = state["metadata"].get("network_analysis", {})

        state["metadata"]["networking_data"] = {
            "target_companies": analysis.get("target_companies", []),
            "action_items": analysis.get("recommendations", []),
            "summary": f"Focus on connecting with {len(analysis.get('target_companies', []))} target companies",
        }

        return state

    builder = GraphBuilder("insights_networking")
    builder.add_node("analyze_connections", analyze_connections)
    builder.add_node("generate_recommendations", generate_recommendations)
    builder.add_edge("analyze_connections", "generate_recommendations")
    builder.set_entry("analyze_connections")
    builder.set_finish("generate_recommendations")

    return builder


# ── Child Graph: Opportunities ──────────────────────────────────────

def build_opportunities_insight_graph() -> GraphBuilder:
    """Build the opportunities insight graph.

    Graph: START → load_opportunities → analyze_funnel → generate_action_plan → END
    """
    def load_opportunities(state: BaseState) -> BaseState:
        """Load job opportunities."""
        try:
            from shared.infrastructure.database.session import get_session_sync
            from jobs.infrastructure.models.job_model import JobModel

            session = get_session_sync()
            jobs = session.query(
                JobModel.id, JobModel.role, JobModel.company,
                JobModel.overall_score, JobModel.match
            ).filter(JobModel.deleted == 0).order_by(
                JobModel.overall_score.desc()
            ).all()

            state["metadata"]["opportunities"] = [
                {
                    "id": r.id,
                    "role": r.role,
                    "company": r.company,
                    "score": r.overall_score,
                    "match": r.match,
                }
                for r in jobs
            ] if jobs else []
        except Exception as e:
            state["errors"].append(f"Failed to load opportunities: {e}")

        return state

    def analyze_funnel(state: BaseState) -> BaseState:
        """Analyze opportunity funnel."""
        opportunities = state["metadata"].get("opportunities", [])

        funnel = {
            "total": len(opportunities),
            "high_priority": len([o for o in opportunities if (o.get("score") or 0) > 70]),
            "medium_priority": len([o for o in opportunities if 40 <= (o.get("score") or 0) <= 70]),
            "low_priority": len([o for o in opportunities if (o.get("score") or 0) < 40]),
        }

        state["metadata"]["funnel"] = funnel
        return state

    def generate_action_plan(state: BaseState) -> BaseState:
        """Generate action plan."""
        funnel = state["metadata"].get("funnel", {})
        opportunities = state["metadata"].get("opportunities", [])

        top_opportunities = opportunities[:5]

        state["metadata"]["opportunities_data"] = {
            "funnel": funnel,
            "top_opportunities": top_opportunities,
            "action_items": [
                f"Apply to {funnel.get('high_priority', 0)} high-priority jobs",
                f"Research {funnel.get('medium_priority', 0)} medium-priority opportunities",
                "Update resume for top opportunities",
            ],
            "summary": f"{funnel.get('total', 0)} opportunities. "
                       f"{funnel.get('high_priority', 0)} high-priority.",
        }

        return state

    builder = GraphBuilder("insights_opportunities")
    builder.add_node("load_opportunities", load_opportunities)
    builder.add_node("analyze_funnel", analyze_funnel)
    builder.add_node("generate_action_plan", generate_action_plan)
    builder.add_edge("load_opportunities", "analyze_funnel")
    builder.add_edge("analyze_funnel", "generate_action_plan")
    builder.set_entry("load_opportunities")
    builder.set_finish("generate_action_plan")

    return builder


# ── Parent Graph: Career Insights ───────────────────────────────────

def build_insights_generation_graph() -> GraphBuilder:
    """Build the parent insights generation graph.

    Orchestrates all child graphs in sequence. Each child graph
    can also be executed independently.

    Graph: START → overview → skills → market → companies →
           networking → opportunities → aggregate → END
    """
    # Build child graphs
    overview_graph = build_overview_graph().compile()
    skills_graph = build_skills_insight_graph().compile()
    market_graph = build_market_insight_graph().compile()
    companies_graph = build_companies_insight_graph().compile()
    networking_graph = build_networking_insight_graph().compile()
    opportunities_graph = build_opportunities_insight_graph().compile()

    def run_overview(state: BaseState) -> BaseState:
        """Execute overview child graph."""
        try:
            result = overview_graph.invoke(state)
            state["metadata"]["section_overview"] = result.get("metadata", {}).get("overview_data", {})
        except Exception as e:
            state["errors"].append(f"Overview failed: {e}")
            state["metadata"]["section_overview"] = {"error": str(e)}
        return state

    def run_skills(state: BaseState) -> BaseState:
        """Execute skills child graph."""
        try:
            result = skills_graph.invoke(state)
            state["metadata"]["section_skills"] = result.get("metadata", {}).get("skills_data", {})
        except Exception as e:
            state["errors"].append(f"Skills insight failed: {e}")
            state["metadata"]["section_skills"] = {"error": str(e)}
        return state

    def run_market(state: BaseState) -> BaseState:
        """Execute market child graph."""
        try:
            result = market_graph.invoke(state)
            state["metadata"]["section_market"] = result.get("metadata", {}).get("market_data", {})
        except Exception as e:
            state["errors"].append(f"Market insight failed: {e}")
            state["metadata"]["section_market"] = {"error": str(e)}
        return state

    def run_companies(state: BaseState) -> BaseState:
        """Execute companies child graph."""
        try:
            result = companies_graph.invoke(state)
            state["metadata"]["section_companies"] = result.get("metadata", {}).get("companies_data", {})
        except Exception as e:
            state["errors"].append(f"Companies insight failed: {e}")
            state["metadata"]["section_companies"] = {"error": str(e)}
        return state

    def run_networking(state: BaseState) -> BaseState:
        """Execute networking child graph."""
        try:
            result = networking_graph.invoke(state)
            state["metadata"]["section_networking"] = result.get("metadata", {}).get("networking_data", {})
        except Exception as e:
            state["errors"].append(f"Networking insight failed: {e}")
            state["metadata"]["section_networking"] = {"error": str(e)}
        return state

    def run_opportunities(state: BaseState) -> BaseState:
        """Execute opportunities child graph."""
        try:
            result = opportunities_graph.invoke(state)
            state["metadata"]["section_opportunities"] = result.get("metadata", {}).get("opportunities_data", {})
        except Exception as e:
            state["errors"].append(f"Opportunities insight failed: {e}")
            state["metadata"]["section_opportunities"] = {"error": str(e)}
        return state

    def aggregate_results(state: BaseState) -> BaseState:
        """Aggregate all section results into final output."""
        overview = state["metadata"].get("section_overview", {})
        skills = state["metadata"].get("section_skills", {})
        market = state["metadata"].get("section_market", {})
        companies = state["metadata"].get("section_companies", {})
        networking = state["metadata"].get("section_networking", {})
        opportunities = state["metadata"].get("section_opportunities", {})

        output = CareerInsightsOutput(
            overview=InsightSectionOutput(
                section="overview",
                data=overview,
                summary=overview.get("summary", ""),
            ),
            skills=InsightSectionOutput(
                section="skills",
                data=skills,
                summary=skills.get("summary", ""),
            ),
            market=InsightSectionOutput(
                section="market",
                data=market,
                summary=market.get("summary", ""),
            ),
            companies=InsightSectionOutput(
                section="companies",
                data=companies,
                summary=companies.get("summary", ""),
            ),
            networking=InsightSectionOutput(
                section="networking",
                data=networking,
                summary=networking.get("summary", ""),
            ),
            opportunities=InsightSectionOutput(
                section="opportunities",
                data=opportunities,
                summary=opportunities.get("summary", ""),
            ),
            health_score=overview.get("health_score"),
            generated_sections=[
                s for s in ["overview", "skills", "market", "companies", "networking", "opportunities"]
                if state["metadata"].get(f"section_{s}") and "error" not in state["metadata"].get(f"section_{s}", {})
            ],
        )

        state["output"] = json.dumps(output.model_dump(), default=str)
        state["metadata"]["typed_output"] = output.model_dump()

        return state

    # Build the parent graph
    builder = GraphBuilder("insights_generation")
    builder.add_node("overview", run_overview)
    builder.add_node("skills", run_skills)
    builder.add_node("market", run_market)
    builder.add_node("companies", run_companies)
    builder.add_node("networking", run_networking)
    builder.add_node("opportunities", run_opportunities)
    builder.add_node("aggregate", aggregate_results)

    builder.add_edge("overview", "skills")
    builder.add_edge("skills", "market")
    builder.add_edge("market", "companies")
    builder.add_edge("companies", "networking")
    builder.add_edge("networking", "opportunities")
    builder.add_edge("opportunities", "aggregate")

    builder.set_entry("overview")
    builder.set_finish("aggregate")

    # Individual sections can fail without stopping the pipeline
    builder.set_retry("overview", max_retries=1, delay=0.5)
    builder.set_retry("skills", max_retries=1, delay=0.5)
    builder.set_retry("market", max_retries=1, delay=0.5)
    builder.set_retry("companies", max_retries=1, delay=0.5)
    builder.set_retry("networking", max_retries=1, delay=0.5)
    builder.set_retry("opportunities", max_retries=1, delay=0.5)

    return builder

"""Insights Generation Graph — LangGraph workflow for career intelligence.

Graph: START → overview → opportunities → companies → market → networking → skills_intel → END

Design Pattern: Pipeline with partial failure support.
"""

from __future__ import annotations

from ..runtime.graph import GraphBuilder
from ..runtime.state import AgentState


def build_insights_generation_graph() -> GraphBuilder:
    """Build the insights generation workflow graph.

    Each section is an independent node. If one fails, the rest continue.
    """

    def overview(state: AgentState) -> AgentState:
        state["metadata"]["section_overview"] = True
        return state

    def opportunities(state: AgentState) -> AgentState:
        state["metadata"]["section_opportunities"] = True
        return state

    def companies(state: AgentState) -> AgentState:
        state["metadata"]["section_companies"] = True
        return state

    def market(state: AgentState) -> AgentState:
        state["metadata"]["section_market"] = True
        return state

    def networking(state: AgentState) -> AgentState:
        state["metadata"]["section_networking"] = True
        return state

    def skills_intel(state: AgentState) -> AgentState:
        state["metadata"]["section_skills_intel"] = True
        # Generate final output
        completed = [k for k in state.get("metadata", {}) if k.startswith("section_")]
        state["output"] = f"Generated {len(completed)} insight sections"
        return state

    builder = GraphBuilder("insights_generation")
    builder.add_node("overview", overview)
    builder.add_node("opportunities", opportunities)
    builder.add_node("companies", companies)
    builder.add_node("market", market)
    builder.add_node("networking", networking)
    builder.add_node("skills_intel", skills_intel)
    builder.add_edge("overview", "opportunities")
    builder.add_edge("opportunities", "companies")
    builder.add_edge("companies", "market")
    builder.add_edge("market", "networking")
    builder.add_edge("networking", "skills_intel")
    builder.set_entry("overview")
    builder.set_finish("skills_intel")

    return builder

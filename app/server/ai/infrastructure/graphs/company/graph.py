"""Company Processing Graph — LangGraph workflow for company intelligence.

Graph: START → fetch → extract → analyze → save → END

Design Pattern: Pipeline Pattern — sequential data transformation.
"""

from __future__ import annotations

from ..runtime.graph import GraphBuilder
from ..runtime.state import AgentState


def build_company_processing_graph() -> GraphBuilder:
    """Build the company processing workflow graph."""
    def fetch(state: AgentState) -> AgentState:
        """Fetch company content."""
        content = state["input"]
        state["metadata"]["raw_content"] = content
        state["metadata"]["content_length"] = len(content)
        return state

    def extract(state: AgentState) -> AgentState:
        """Extract structured company data."""
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
            from services.company_worker import _extract_company_info
            pid = state["context"].get("pid", "ai_company")
            result = _extract_company_info(state["input"], "multi_note", pid)
            if result:
                state["metadata"]["company_data"] = result
        except Exception as e:
            state["errors"].append(f"Extraction failed: {e}")
        return state

    def analyze(state: AgentState) -> AgentState:
        """Generate intelligence analysis."""
        company_data = state.get("metadata", {}).get("company_data", {})
        if company_data:
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
                from services.company_worker import _analyze_company
                pid = state["context"].get("pid", "ai_analyze")
                company_type = company_data.get("company_type", "UNKNOWN")
                result = _analyze_company(company_data, pid, company_type=company_type)
                if result:
                    state["metadata"]["intelligence"] = result
                    state["output"] = str(result)
            except Exception as e:
                state["errors"].append(f"Analysis failed: {e}")
        return state

    def save(state: AgentState) -> AgentState:
        """Save results (placeholder — actual save happens in worker)."""
        state["metadata"]["saved"] = True
        return state

    builder = GraphBuilder("company_processing")
    builder.add_node("fetch", fetch)
    builder.add_node("extract", extract)
    builder.add_node("analyze", analyze)
    builder.add_node("save", save)
    builder.add_edge("fetch", "extract")
    builder.add_edge("extract", "analyze")
    builder.add_edge("analyze", "save")
    builder.set_entry("fetch")
    builder.set_finish("save")

    return builder

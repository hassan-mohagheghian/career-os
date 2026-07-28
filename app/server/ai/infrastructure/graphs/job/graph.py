"""Job Processing Graph — LangGraph workflow for job analysis.

Graph: START → fetch → validate → extract → score → END

Design Pattern: Pipeline Pattern — sequential data transformation.
"""

from __future__ import annotations

from ..runtime.graph import GraphBuilder
from ..runtime.state import AgentState


def build_job_processing_graph() -> GraphBuilder:
    """Build the job processing workflow graph.

    Returns a compiled GraphBuilder ready for execution.
    """
    def fetch(state: AgentState) -> AgentState:
        """Fetch job content from URL."""
        url = state["context"].get("url", state["input"])
        if url.startswith("http"):
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
                from services.worker import _fetch_url
                content = _fetch_url(url)
                state["metadata"]["raw_content"] = content
                state["metadata"]["content_length"] = len(content)
            except Exception as e:
                state["errors"].append(f"Fetch failed: {e}")
        else:
            state["metadata"]["raw_content"] = url
        return state

    def validate(state: AgentState) -> AgentState:
        """Validate fetched content."""
        content = state.get("metadata", {}).get("raw_content", "")
        if len(content) < 50:
            state["errors"].append("Content too short to be a valid job posting")
        state["metadata"]["validated"] = True
        return state

    def extract(state: AgentState) -> AgentState:
        """Extract structured job data."""
        content = state.get("metadata", {}).get("raw_content", "")
        if content:
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
                from services.worker import _extract_all
                pid = state["context"].get("pid", "ai_job")
                result = _extract_all(content, pid)
                if result:
                    state["metadata"]["extraction"] = result
            except Exception as e:
                state["errors"].append(f"Extraction failed: {e}")
        return state

    def score(state: AgentState) -> AgentState:
        """Score the job."""
        extraction = state.get("metadata", {}).get("extraction", {})
        if isinstance(extraction, dict):
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
                from services.worker import normalize_score
                state["metadata"]["score"] = normalize_score(extraction.get("score", "P"))
                state["output"] = str(extraction)
            except Exception as e:
                state["errors"].append(f"Scoring failed: {e}")
        return state

    builder = GraphBuilder("job_processing")
    builder.add_node("fetch", fetch)
    builder.add_node("validate", validate)
    builder.add_node("extract", extract)
    builder.add_node("score", score)
    builder.add_edge("fetch", "validate")
    builder.add_edge("validate", "extract")
    builder.add_edge("extract", "score")
    builder.set_entry("fetch")
    builder.set_finish("score")

    return builder

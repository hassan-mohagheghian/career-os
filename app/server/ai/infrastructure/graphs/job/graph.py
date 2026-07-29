from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from ..runtime.graph import GraphBuilder
from ..runtime.state import BaseState, JobExtractionOutput, JobAnalysisOutput

from ai.infrastructure.tools.fetch import fetch_page


def build_job_processing_graph() -> GraphBuilder:

    def load_context(state: BaseState) -> BaseState:
        pid = state["context"].get("pid")
        url = state["context"].get("url", state["input"])
        notes = state["context"].get("notes", [])
        links = state["context"].get("links", [])
        source = state["context"].get("source", "cli")

        state["context"]["source"] = source
        state["context"]["pid"] = pid

        notes_text = []
        for note in notes:
            if isinstance(note, dict):
                if note.get("type") == "text" and note.get("content"):
                    notes_text.append(f"[NOTE] {note['content']}")
                elif note.get("type") == "url" and note.get("content"):
                    notes_text.append(f"[NOTE_URL] {note['content']}")
            elif isinstance(note, str):
                notes_text.append(f"[NOTE] {note}")
        state["context"]["notes_text"] = "\n".join(notes_text)

        links_text = []
        for link in links:
            if isinstance(link, dict):
                link_url = link.get("url", "")
                link_title = link.get("title", "Link")
                if link_url:
                    links_text.append(f"[{link_title}] {link_url}")
            elif isinstance(link, str):
                links_text.append(f"[Link] {link}")
        state["context"]["links_text"] = "\n".join(links_text)

        resume_text = state["context"].get("resume_text", "")
        linkedin_text = state["context"].get("linkedin_text", "")
        rules = state["context"].get("rules", "")

        if not resume_text:
            try:
                from dependencies import get_session_sync
                from jobs.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
                session = get_session_sync()
                try:
                    resume_repo = SQLAlchemyResumeRepository(session)
                    resume_text = resume_repo.get_latest_original_raw_text() or ""
                finally:
                    session.close()
            except Exception:
                resume_text = ""
            state["context"]["resume_text"] = resume_text

        if not linkedin_text:
            try:
                from dependencies import get_session_sync
                from jobs.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
                session = get_session_sync()
                try:
                    resume_repo = SQLAlchemyResumeRepository(session)
                    linkedin_text = resume_repo.get_latest_linkedin_raw_text() or ""
                finally:
                    session.close()
            except Exception:
                linkedin_text = ""
            state["context"]["linkedin_text"] = linkedin_text

        if not rules:
            try:
                from dependencies import get_session_sync
                from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository
                session = get_session_sync()
                try:
                    rule_repo = SQLAlchemyRuleRepository(session)
                    rows = rule_repo.get_enabled_by_scopes(["SHARED", "JOB"])
                finally:
                    session.close()
                if rows:
                    lines = []
                    current_cat = None
                    for r in rows:
                        cat = r["category"]
                        if cat != current_cat:
                            current_cat = cat
                            lines.append(f"\n\xad\u2015 {cat.upper()} {'\u2500' * (35 - len(cat))}")
                        weight = r.get("score_weight") or r["priority"]
                        lines.append(f"  #{r['priority']:>3}  {r['key']} (weight:{weight}): {r['value']}")
                    rules = "\n".join(lines)
                else:
                    rules = "No scoring rules set."
            except Exception:
                rules = "No scoring rules set."
            state["context"]["rules"] = rules

        state["metadata"]["load_context"] = {
            "success": True,
            "has_resume": bool(resume_text),
            "has_linkedin": bool(linkedin_text),
            "has_rules": bool(rules),
        }

        return state

    def validate_input(state: BaseState) -> BaseState:
        url = state["context"].get("url", state["input"])
        notes = state["context"].get("notes", [])
        links = state["context"].get("links", [])

        has_url = bool(url and url.startswith("http"))
        has_notes = bool(notes)
        has_links = bool(links)

        if not (has_url or has_notes or has_links):
            state["errors"].append("No job sources provided (URL, notes, or links)")
            return state

        state["metadata"]["validation"] = {
            "has_url": has_url,
            "has_notes": has_notes,
            "has_links": has_links,
            "valid": True,
        }

        return state

    def fetch_url(state: BaseState) -> BaseState:
        url = state["context"].get("url", state["input"])
        notes = state["context"].get("notes", [])
        links = state["context"].get("links", [])

        parts = []

        for note in notes:
            if isinstance(note, dict):
                if note.get("type") == "text" and note.get("content"):
                    parts.append(f"[NOTE] {note['content']}")

        if url and url.startswith("http"):
            try:
                page = fetch_page(url)
                if page.is_ok:
                    parts.append(page.plain_text)
                else:
                    error_msg = page.error.message if page.error else "Fetch failed"
                    state["errors"].append(f"URL fetch failed: {error_msg}")
                    state["metadata"]["fetch"] = {"success": False, "error": error_msg}
            except Exception as e:
                state["errors"].append(f"URL fetch failed: {e}")
                state["metadata"]["fetch"] = {"success": False, "error": str(e)}

        for note in notes:
            if isinstance(note, dict):
                if note.get("type") == "url" and note.get("content"):
                    note_url = note["content"].strip()
                    if note_url.startswith("http") and (not url or note_url not in url):
                        try:
                            page = fetch_page(note_url)
                            if page.is_ok:
                                parts.append(f"[URL] {page.plain_text}")
                        except Exception:
                            pass

        for link in links:
            if isinstance(link, dict):
                link_url = link.get("url", "")
                if link_url and link_url.startswith("http"):
                    try:
                        page = fetch_page(link_url)
                        if page.is_ok:
                            parts.append(f"[{link.get('title', 'Link')}] {page.plain_text}")
                    except Exception:
                        pass

        content = "\n\n".join(parts)[:8000] if parts else ""

        if content:
            state["metadata"]["raw_content"] = content
            state["metadata"]["content_length"] = len(content)
            state["metadata"]["fetch"] = {
                "success": True,
                "url": url,
                "length": len(content),
                "has_notes": bool(notes),
                "has_links": bool(links),
            }
        else:
            if not state["errors"]:
                state["errors"].append("No content fetched from any source")
            state["metadata"]["fetch"] = {"success": False, "error": "No content"}

        return state

    def fallback_to_notes(state: BaseState) -> BaseState:
        if state["metadata"].get("raw_content"):
            state["metadata"]["fallback"] = {
                "skipped": True,
                "reason": "Content already fetched",
            }
            return state

        notes_text = state["context"].get("notes_text", "")
        if notes_text:
            state["metadata"]["raw_content"] = notes_text
            state["metadata"]["content_length"] = len(notes_text)
            state["metadata"]["fallback"] = {"used_notes": True, "length": len(notes_text)}
        else:
            state["metadata"]["fallback"] = {
                "used_notes": False,
                "reason": "No notes available",
            }

        return state

    def extract_raw_content(state: BaseState) -> BaseState:
        content = state["metadata"].get("raw_content", "")

        if not content:
            state["errors"].append("No content available for extraction")
            return state

        try:
            from shared.infrastructure.ai.compat import get_llm_service
            from shared.infrastructure.prompts.loader import load_prompt

            prompt = load_prompt(
                "job_processing/step3_extract_raw",
                content=content[:5000],
            )

            llm = get_llm_service()
            resp = llm.generate_structured(
                prompt,
                timeout=90,
            )
            result = json.loads(resp.content)

            if result:
                state["metadata"]["extraction"] = result
                state["metadata"]["extract_raw"] = {"success": True}
            else:
                state["metadata"]["extract_raw"] = {
                    "success": False,
                    "reason": "Extraction returned None",
                }
        except Exception as e:
            state["errors"].append(f"Raw extraction failed: {e}")
            state["metadata"]["extract_raw"] = {"success": False, "error": str(e)}

        return state

    def clean_content(state: BaseState) -> BaseState:
        extraction = state["metadata"].get("extraction", {})

        if not extraction:
            state["metadata"]["clean"] = {
                "skipped": True,
                "reason": "No extraction to clean",
            }
            return state

        for key, val in extraction.items():
            if isinstance(val, list):
                extraction[key] = "\n".join(str(item) for item in val)
            elif isinstance(val, str):
                extraction[key] = val.strip()

        state["metadata"]["extraction"] = extraction
        state["metadata"]["clean"] = {
            "success": True,
            "fields_cleaned": list(extraction.keys()),
        }

        return state

    def extract_structured_data(state: BaseState) -> BaseState:
        extraction = state["metadata"].get("extraction", {})

        if not extraction:
            state["metadata"]["structured"] = {
                "skipped": True,
                "reason": "No extraction to structure",
            }
            return state

        url = state["context"].get("url", "")
        structured = JobExtractionOutput.from_llm_extraction(extraction, url=url)

        state["metadata"]["structured"] = structured.model_dump()
        state["metadata"]["extract_struct"] = {"success": True}

        return state

    def analyze_job(state: BaseState) -> BaseState:
        structured = state["metadata"].get("structured", {})

        if not structured:
            state["metadata"]["analysis"] = {
                "skipped": True,
                "reason": "No structured data to analyze",
            }
            return state

        try:
            stack = structured.get("stack", "")
            state["metadata"]["tech_stack"] = stack

            requirements = structured.get("requirements", "")
            state["metadata"]["requirements_analysis"] = {
                "has_requirements": bool(requirements),
                "length": len(requirements),
            }

            state["metadata"]["analyze"] = {"success": True}
        except Exception as e:
            state["errors"].append(f"Analysis failed: {e}")
            state["metadata"]["analyze"] = {"success": False, "error": str(e)}

        return state

    def extract_skills_node(state: BaseState) -> BaseState:
        structured = state["metadata"].get("structured", {})
        description = structured.get("description", "")

        if not description:
            state["metadata"]["skills"] = {
                "skipped": True,
                "reason": "No description to extract skills from",
            }
            return state

        try:
            stack = structured.get("stack", "")
            skills = [s.strip() for s in stack.split(",") if s.strip()]
            state["metadata"]["extracted_skills"] = skills
            state["metadata"]["extract_skills"] = {
                "success": True,
                "count": len(skills),
            }
        except Exception as e:
            state["errors"].append(f"Skill extraction failed: {e}")
            state["metadata"]["extract_skills"] = {
                "success": False,
                "error": str(e),
            }

        return state

    def score_job(state: BaseState) -> BaseState:
        extraction = state["metadata"].get("extraction", {})

        if not extraction:
            state["metadata"]["scoring"] = {
                "skipped": True,
                "reason": "No extraction to score",
            }
            return state

        try:
            from jobs.infrastructure.workers.worker import normalize_score

            score = normalize_score(extraction.get("score", "P"))
            state["metadata"]["score"] = score
            state["metadata"]["fit_score"] = extraction.get("fit_score")
            state["metadata"]["success_score"] = extraction.get("success_score")
            state["metadata"]["overall_score"] = extraction.get("overall_score")
            state["metadata"]["scoring"] = {"success": True, "score": score}
        except Exception as e:
            state["errors"].append(f"Scoring failed: {e}")
            state["metadata"]["scoring"] = {"success": False, "error": str(e)}

        return state

    def generate_summary(state: BaseState) -> BaseState:
        structured = state["metadata"].get("structured", {})
        extraction = state["metadata"].get("extraction", {})

        if not structured and not extraction:
            state["metadata"]["summary"] = {
                "skipped": True,
                "reason": "No data to summarize",
            }
            return state

        try:
            summary_parts = []
            if structured.get("title"):
                summary_parts.append(f"Position: {structured['title']}")
            if structured.get("company"):
                summary_parts.append(f"Company: {structured['company']}")
            if structured.get("location"):
                summary_parts.append(f"Location: {structured['location']}")
            if extraction.get("summary"):
                summary_parts.append(f"Summary: {extraction['summary']}")

            summary = "\n".join(summary_parts)
            state["metadata"]["job_summary"] = summary
            state["metadata"]["generate_summary"] = {"success": True}
        except Exception as e:
            state["errors"].append(f"Summary generation failed: {e}")
            state["metadata"]["generate_summary"] = {
                "success": False,
                "error": str(e),
            }

        return state

    def persist_results(state: BaseState) -> BaseState:
        structured = state["metadata"].get("structured", {})
        extraction = state["metadata"].get("extraction", {})
        raw_content = state["metadata"].get("raw_content", "")

        if not structured and not extraction:
            state["metadata"]["persistence"] = {
                "skipped": True,
                "reason": "No data to persist",
            }
            return state

        try:
            from dependencies import get_session_sync
            from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
            from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
            from jobs.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository

            pid = state["context"].get("pid")
            url = state["context"].get("url", state["input"])

            session = get_session_sync()
            try:
                job_repo = SQLAlchemyJobRepository(session)
                summary_repo = SQLAlchemySummaryRepository(session)
                resume_repo = SQLAlchemyResumeRepository(session)

                temp_num = job_repo.get_next_num()
                existing_num = job_repo.get_num_by_url(url) if url else None
                job_num = existing_num or temp_num

                company = structured.get("company") or extraction.get("company") or "Unknown"
                title = structured.get("title") or extraction.get("title") or "Unknown"
                score = state["metadata"].get("score", "P")
                match = extraction.get("match", "Medium")
                fit_score = state["metadata"].get("fit_score")
                success_score = state["metadata"].get("success_score")
                overall_score = state["metadata"].get("overall_score")

                job_data = {
                    "num": job_num,
                    "company": company,
                    "role": title,
                    "location": structured.get("location", "Not specified"),
                    "match": match,
                    "score": score,
                    "success": extraction.get("success", "P"),
                    "salary": structured.get("salary", "Not specified"),
                    "stack": structured.get("stack", ""),
                    "visa": extraction.get("visa", "Uncertain"),
                    "applicants": extraction.get("applicants", "Not specified"),
                    "posted": extraction.get("posted", "Not specified"),
                    "industry": extraction.get("industry", ""),
                    "domain": extraction.get("domain", ""),
                    "notes": extraction.get("notes", ""),
                    "action": extraction.get("action", ""),
                    "url": url,
                    "raw_description": raw_content,
                    "structured_description": json.dumps(extraction, ensure_ascii=False) if extraction else None,
                    "fit_score": fit_score,
                    "success_score": success_score,
                    "overall_score": overall_score,
                    "company_url": extraction.get("company_url"),
                    "linkedin_url": extraction.get("linkedin_url"),
                    "workflow_log": json.dumps(state.get("node_history", [])),
                }
                job_repo.upsert(job_data)

                summary_data = {
                    "num": job_num,
                    "company": company,
                    "match": match,
                    "score": score,
                    "summary": extraction.get("summary", ""),
                    "stack": structured.get("stack", ""),
                    "resumeFit": extraction.get("resumeFit", ""),
                    "note": extraction.get("note", ""),
                    "url": url,
                }
                summary_repo.upsert(summary_data)

            finally:
                session.close()

            state["metadata"]["persistence"] = {
                "success": True,
                "job_num": job_num,
                "company": company,
            }
            state["context"]["job_num"] = job_num

        except Exception as e:
            state["errors"].append(f"Persistence failed: {e}")
            state["metadata"]["persistence"] = {
                "success": False,
                "error": str(e),
            }

        return state

    def completion_event(state: BaseState) -> BaseState:
        output = JobAnalysisOutput(
            extraction=JobExtractionOutput(
                **state["metadata"].get("structured", {})
            ),
            tech_stack=state["metadata"].get("extracted_skills", []),
            requirements_analysis=state["metadata"].get(
                "requirements_analysis", {}
            ),
            score=state["metadata"].get("score", ""),
            fit_score=state["metadata"].get("fit_score"),
            success_score=state["metadata"].get("success_score"),
            overall_score=state["metadata"].get("overall_score"),
            summary=state["metadata"].get("job_summary", ""),
        )

        state["output"] = json.dumps(output.model_dump(), default=str)
        state["metadata"]["completion"] = {"success": True}
        state["metadata"]["typed_output"] = output.model_dump()

        return state

    builder = GraphBuilder("job_processing")
    builder.add_node("load_context", load_context)
    builder.add_node("validate_input", validate_input)
    builder.add_node("fetch_url", fetch_url)
    builder.add_node("fallback_to_notes", fallback_to_notes)
    builder.add_node("extract_raw_content", extract_raw_content)
    builder.add_node("clean_content", clean_content)
    builder.add_node("extract_structured_data", extract_structured_data)
    builder.add_node("analyze_job", analyze_job)
    builder.add_node("extract_skills", extract_skills_node)
    builder.add_node("score_job", score_job)
    builder.add_node("generate_summary", generate_summary)
    builder.add_node("persist_results", persist_results)
    builder.add_node("completion_event", completion_event)

    builder.add_edge("load_context", "validate_input")
    builder.add_edge("validate_input", "fetch_url")
    builder.add_edge("fetch_url", "fallback_to_notes")
    builder.add_edge("fallback_to_notes", "extract_raw_content")
    builder.add_edge("extract_raw_content", "clean_content")
    builder.add_edge("clean_content", "extract_structured_data")
    builder.add_edge("extract_structured_data", "analyze_job")
    builder.add_edge("analyze_job", "extract_skills")
    builder.add_edge("extract_skills", "score_job")
    builder.add_edge("score_job", "generate_summary")
    builder.add_edge("generate_summary", "persist_results")
    builder.add_edge("persist_results", "completion_event")

    builder.set_entry("load_context")
    builder.set_finish("completion_event")

    builder.set_retry("extract_raw_content", max_retries=2, delay=1.0)
    builder.set_retry("score_job", max_retries=2, delay=1.0)

    return builder

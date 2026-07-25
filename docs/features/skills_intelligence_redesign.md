# Skills Intelligence Redesign — Implementation Plan

## Vision

Transform `Insights → Skills` into a complete Skill Intelligence system that creates a closed loop:

```
Jobs → Market Skill Intelligence → User Skill Profile → Gap Analysis → Recommendations → Roadmap → Knowledge Base
```

## Current State Analysis

### What Exists
- **SkillsIntelSection** (660 lines): Full skill list with categories, filters, merge, CRUD
- **SkillsTab**: Roadmap-focused standalone page (uses `useSkills` hook)
- **SkillRoadmapDrawer**: Per-skill roadmap generation/progress
- **SkillDetailDrawer**: Skill detail with relationships, aliases, tags
- **Backend**: tech_stack CRUD, skill_roadmaps generation, insights generation
- **AI Prompt**: `skills_intelligence.txt` — comprehensive but outputs to JSON blob, not DB

### What's Missing
1. **AI → DB propagation**: Skills intelligence report stored as JSON blob, never fills `tech_stack` or `skill_relationships`
2. **Market skill extraction**: No dedicated agent to extract skills from jobs/companies
3. **Skill evidence tracking**: `tech_stack.evidence` and `tech_stack.market_relevance` columns exist but are never populated
4. **Skill gap matrix UI**: No visual comparison of market vs user skills
5. **Recommendations UI**: AI recommendations exist in JSON but not rendered as actionable cards

## Implementation Plan

### Phase 1: Database & Backend (Foundation)

**1.1 Update `tech_stack` table schema**
- Add `description TEXT` column for skill descriptions
- Add `evidence_sources TEXT` column (JSON: array of source types)
- Add `last_analyzed_at TIMESTAMP` column

**1.2 Create `skill_evidence` table**
```sql
CREATE TABLE skill_evidence (
  id INTEGER PRIMARY KEY,
  skill_name TEXT NOT NULL,
  source_type TEXT NOT NULL,  -- 'job', 'company', 'resume', 'manual'
  source_id INTEGER,          -- job num, company id, etc.
  evidence TEXT,              -- description of evidence
  frequency INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**1.3 Update `_fill_skills_from_insights()` in `services/insights.py`**
- After AI generation, propagate skills to `tech_stack`
- Create `skill_evidence` entries from AI report
- Update `market_relevance` and `confidence` on existing skills

**1.4 Create new API endpoints**
- `GET /api/tech-stack/:id/evidence` — Get evidence for a skill
- `POST /api/tech-stack/:id/evidence` — Add evidence
- `GET /api/tech-stack/market-analysis` — Get market demand summary

### Phase 2: AI Pipeline Enhancement

**2.1 Update `skills_intelligence.txt` prompt**
- Add structured output for evidence tracking
- Add market demand percentages per skill
- Add skill category recommendations
- Ensure output includes all data needed for DB propagation

**2.2 Create `skills_market_analysis.txt` prompt**
- Input: All jobs with stack columns
- Output: Market skill demand with frequency, importance, related skills
- Purpose: Standalone market analysis (not dependent on user skills)

**2.3 Update `_fill_skills_from_insights()` to:**
- Parse market demand from AI report
- Update `tech_stack.market_relevance` with real percentages
- Create `skill_evidence` entries linking skills to jobs/companies
- Update `skill_relationships` from AI report relationships

### Phase 3: Frontend — Insights → Skills Page

**3.1 Design new Skills Intelligence page**
Replace current empty placeholder with:

```
┌─────────────────────────────────────────────────────┐
│ Skills Intelligence                    [Refresh]     │
├─────────────────────────────────────────────────────┤
│ [Overview Cards]                                    │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│ │ Total   │ │ Market  │ │Strengths│ │  Gaps   │   │
│ │ Skills  │ │ Demand  │ │         │ │         │   │
│ │   42    │ │   78%   │ │   15    │ │   8     │   │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
├─────────────────────────────────────────────────────┤
│ [Market Demand Chart]  [Skill Gap Matrix]           │
│ Top skills: Python, SQL, Docker, K8s                │
│ Gap: K8s (Advanced vs Beginner) = High Priority     │
├─────────────────────────────────────────────────────┤
│ [Categories]                                        │
│ Backend | Cloud | AI | Database | Frontend           │
├─────────────────────────────────────────────────────┤
│ [Recommendations]                                   │
│ "Learn Kubernetes — 45% of target jobs require it"  │
├─────────────────────────────────────────────────────┤
│ [Roadmap Preview]                                   │
│ Phase 1: PostgreSQL optimization (2 weeks)          │
│ Phase 2: Kubernetes basics (4 weeks)                │
└─────────────────────────────────────────────────────┘
```

**3.2 Components to create/update**
- `SkillsIntelligencePage.tsx` — Main page with cards, charts, matrix
- `MarketDemandChart.tsx` — Bar chart of top skills by demand
- `SkillGapMatrix.tsx` — Table: Skill | Market | User | Gap | Priority
- `RecommendationCard.tsx` — Actionable recommendation with ROI
- `RoadmapPreview.tsx` — Current phase + next skills

**3.3 Components to keep (from SkillsIntelSection)**
- Category tabs, filters, sorting
- Tech stack CRUD (add, hide, delete, rename)
- Merge mode (DnD)
- Hidden skills section

### Phase 4: Integration

**4.1 Wire `_fill_skills_from_insights()` after AI generation**
- Already partially implemented
- Enhance to propagate ALL AI data to DB

**4.2 Update SkillsTab (top-level)**
- Add "Market Analysis" section showing extracted market skills
- Keep roadmap generation
- Add "Review Discovered Skills" to accept AI-extracted skills into tech_stack

**4.3 Update generation history**
- Skills intelligence runs already tracked
- Add market analysis runs tracking

## File Changes Summary

| File | Action |
|------|--------|
| `core/db.py` | Add `skill_evidence` table, `tech_stack` columns |
| `migrations.py` | Add migration for new columns/table |
| `services/insights.py` | Enhance `_fill_skills_from_insights()` |
| `blueprints/tech_stack.py` | Add evidence endpoints |
| `prompts/insights/skills_intelligence.txt` | Update prompt for structured output |
| `prompts/insights/skills_market_analysis.txt` | NEW — market skill extraction |
| `features/insights/components/SkillsIntelligencePage.tsx` | NEW — main page |
| `features/insights/components/MarketDemandChart.tsx` | NEW — chart component |
| `features/insights/components/SkillGapMatrix.tsx` | NEW — gap table |
| `features/insights/components/RecommendationCard.tsx` | NEW — recommendation cards |
| `features/insights/components/RoadmapPreview.tsx` | NEW — roadmap preview |
| `features/insights/components/InsightsTab.tsx` | Update to render SkillsIntelligencePage |
| `features/skills/components/SkillsTab.tsx` | Add market analysis section |

## Verification

1. `npx vite build` passes
2. `npx vitest run` — 23+ tests pass
3. `python -m pytest app/server/tests/` — 306+ tests pass
4. Insights → Skills shows market demand chart, gap matrix, recommendations
5. Skills (top-level) shows market analysis + roadmap generation
6. AI generation fills skills into tech_stack with evidence
7. Skill evidence is trackable and queryable

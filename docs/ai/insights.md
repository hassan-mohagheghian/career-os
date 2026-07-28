# Career Insights Architecture

## Overview

Career Insights is implemented as a composition of 6 independent child graphs, orchestrated by a parent graph. Each child graph can be executed independently or composed together.

## Child Graphs

### 1. Overview

**Graph**: `insights_overview`
**Purpose**: Career health score and summary

```
collect_data → compute_health → generate_summary
```

**Data Sources**:
- Jobs table (recent 50 jobs)
- Skills table (all user skills)

**Output**: Health score (0-100), job count, skill count

### 2. Skills

**Graph**: `insights_skills`
**Purpose**: Skill gap analysis and recommendations

```
load_skills → analyze_gaps → generate_recommendations
```

**Data Sources**:
- Skills table

**Output**: Skill analysis, recommendations

### 3. Market

**Graph**: `insights_market`
**Purpose**: Job market trends and analysis

```
analyze_demand → analyze_trends → generate_report
```

**Data Sources**:
- Jobs table (all active jobs)

**Output**: Skill demand, location demand, market health

### 4. Companies

**Graph**: `insights_companies`
**Purpose**: Company intelligence and targeting

```
load_companies → analyze_targeting → generate_shortlist
```

**Data Sources**:
- Jobs table (company data)

**Output**: Company shortlist, targeting priorities

### 5. Networking

**Graph**: `insights_networking`
**Purpose**: Professional network recommendations

```
analyze_connections → generate_recommendations
```

**Data Sources**:
- Companies insight data

**Output**: Target companies, action items

### 6. Opportunities

**Graph**: `insights_opportunities`
**Purpose**: Job opportunity funnel

```
load_opportunities → analyze_funnel → generate_action_plan
```

**Data Sources**:
- Jobs table (all active jobs)

**Output**: Opportunity funnel, action plan

## Parent Graph

The parent `insights_generation` graph orchestrates all 6 child graphs:

```
overview → skills → market → companies → networking → opportunities → aggregate
```

### Partial Failure Support

Each section is wrapped in try/except. If one section fails:
- Error is recorded in `state["errors"]`
- Section metadata gets `{"error": "..."}`
- Pipeline continues to next section
- Final output includes `generated_sections` list

### Aggregation

The `aggregate` node collects all section results into a `CareerInsightsOutput` Pydantic model with:
- Individual section data
- Health score (from overview)
- List of successfully generated sections

## Independent Execution

Each child graph can be executed standalone:

```python
from ai.infrastructure.graphs.insights.graph import build_overview_graph

overview = build_overview_graph().compile()
result = overview.invoke(create_initial_state())
```

## Adding a New Section

1. Create `build_{section}_graph()` in `insights/graph.py`
2. Add to `__init__.py` exports
3. Add to parent graph as new node
4. Add edge from previous section
5. Add retry config
6. Update `aggregate` to include new section

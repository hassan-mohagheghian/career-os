# Changelog

## [Unreleased] — Career Intelligence System

### Added
- **Career Intelligence module** — New main menu tab with 6 sections
  - Overview: Career health score, position cards, next actions
  - Opportunities: Job funnel (Apply Now → Low Priority)
  - Companies: Product vs Recruiting company rankings
  - Skills: Strengths, gaps, learning ROI
  - Market: Country/city analysis, remote opportunities
  - Networking: Connection strategy, LinkedIn search queries
- **Database tables**: `career_insight_runs`, `career_insights`
- **Backend service**: `services/career_intel.py`
- **API endpoints**: `/api/career-intelligence/*`
- **AI prompt**: `prompts/career_intelligence.txt`
- **Frontend components**: 8 new components in `components/career-intel/`
- **Workflow UI**: Processing status cards per section
- **Documentation**: Full `/docs` structure

### Changed
- App.jsx: Added Career Intel tab to sidebar and routing
- hooks/index.js: Exported useCareerIntel hook

## [Previous]

### Added
- Company processing pipeline (fetch → extract → analyze)
- Company intelligence (product vs recruiting analysis)
- Configurable scoring rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING)
- Resume/cover letter generation via Mimo CLI
- WebSocket real-time processing output
- SSE for pending items streaming
- Per-section independent refresh for intelligence
- LinkedIn profile integration
- Job reprocessing and rescoring

"""Database initialization and path configuration.

Table creation is handled by SQLAlchemy models + Alembic.
This module provides DB_PATH and one-time data migration utilities.
"""

import json
import os

from dotenv import load_dotenv
load_dotenv()

_file_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.join(_file_dir, '..', '..', '..')
_db_path = os.environ.get('DB_PATH', os.path.join(_server_dir, "db", "jobs.db"))
# Resolve relative paths against the server directory
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.normpath(os.path.join(_server_dir, _db_path))

# Ensure db directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def init_db():
    """Initialize database tables using SQLAlchemy models.

    Table creation is delegated to Base.metadata.create_all() which uses
    the declarative models defined in infrastructure/database/models/.
    Schema migrations are handled by Alembic.
    """
    from shared.infrastructure.database.sqlalchemy_config import engine, Base
    # Import all models to register them with Base.metadata
    import jobs.infrastructure.models.job_model
    import skills.infrastructure.models.skill_model
    import companies.infrastructure.models.company_model
    import processing.infrastructure.models.pending_model
    import career.infrastructure.models.insight_model
    import shared.infrastructure.database.models.misc_models

    Base.metadata.create_all(bind=engine)

    # Seed initial rules if table is empty
    from shared.infrastructure.database.sqlalchemy_config import SessionLocal
    from shared.infrastructure.database.models.misc_models import PreferenceModel
    session = SessionLocal()
    try:
        count = session.query(PreferenceModel).count()
        if count == 0:
            _seed_initial_rules(session)
    finally:
        session.close()


def _seed_initial_rules(session):
    """Seed the initial scoring rules into the preferences table."""
    from shared.infrastructure.database.models.misc_models import PreferenceModel

    rules = [
        # Shared rules
        ("success", "shared", "SHARED", "visa_and_relocation_compatibility",
         "Evaluate visa sponsorship and relocation support.", "Main impact: Success Score", 100, 100),
        ("success", "shared", "SHARED", "market_and_location_accessibility",
         "Evaluate location accessibility.", "Main impact: Success Score", 95, 90),
        ("success", "shared", "SHARED", "communication_and_work_culture",
         "Evaluate work culture and communication.", "Main impact: Success Score", 80, 70),
        ("success", "shared", "SHARED", "sensitive_industry_penalty",
         "Reduce score for sensitive industries.", "Main impact: Success Score", 60, 50),
        # Job rules
        ("fit", "job", "JOB", "python_backend_core",
         "Python must be the primary language.", "Core Python backend requirement", 100, 100),
        ("fit", "job", "JOB", "role_alignment",
         "Backend engineer, Platform engineer.", "Title patterns that match", 85, 85),
        ("success", "job", "JOB", "hiring_probability",
         "Assess hiring likelihood.", "Application success likelihood", 80, 80),
        ("fit", "job", "JOB", "technical_synergy",
         "Evaluate technical synergy.", "Cloud and backend infrastructure overlap", 75, 75),
        ("fit", "job", "JOB", "engineering_depth",
         "Evaluate engineering depth.", "Seniority and depth match", 70, 70),
        ("fit", "job", "JOB", "work_and_communication_fit",
         "Evaluate work arrangement and culture.", "Work culture compatibility", 65, 65),
        ("fit", "job", "JOB", "candidate_job_alignment",
         "Evaluate how well the specific job matches.", "Profile-to-job match quality", 55, 55),
        # Product company rules
        ("fit", "company", "COMPANY_PRODUCT", "company_quality",
         "Evaluate company quality.", "Core company evaluation", 100, 100),
        ("fit", "company", "COMPANY_PRODUCT", "engineering_culture",
         "Evaluate engineering culture.", "Engineering team quality", 90, 85),
        ("fit", "company", "COMPANY_PRODUCT", "growth_and_career_potential",
         "Evaluate growth opportunities.", "Career advancement potential", 80, 75),
        ("fit", "company", "COMPANY_PRODUCT", "candidate_company_alignment",
         "Evaluate alignment with candidate profile.", "Profile match quality", 65, 60),
        ("fit", "company", "COMPANY_PRODUCT", "product_maturity",
         "Evaluate product maturity signals.", "Product viability assessment", 50, 50),
        # Recruiting company rules
        ("fit", "recruiter", "COMPANY_RECRUITING", "recruiter_network_value",
         "Evaluate recruiter value.", "Main impact: Company Fit Score", 100, 100),
        ("success", "recruiter", "COMPANY_RECRUITING", "recruiter_market_access",
         "Evaluate market access.", "Main impact: Company Success Score", 95, 85),
        ("fit", "recruiter", "COMPANY_RECRUITING", "recruiter_profile_alignment",
         "Evaluate profile alignment.", "Main impact: Company Fit Score", 85, 80),
        ("success", "recruiter", "COMPANY_RECRUITING", "recruiter_activity_and_opportunity",
         "Evaluate opportunity generation.", "Main impact: Company Success Score", 70, 70),
    ]

    for cat, rule_type, scope, key, value, desc, priority, weight in rules:
        session.add(PreferenceModel(
            category=cat, rule_type=rule_type, scope=scope, key=key,
            value=value, description=desc, priority=priority, score_weight=weight,
        ))
    session.commit()
    print(f"[db] Seeded {len(rules)} scoring rules")


def load_json_to_db():
    """No-op: data is now managed entirely in SQLite."""
    pass


def migrate_existing_analysis_files():
    """Migrate existing analysis JSON files to the analysis_runs table."""
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    from shared.infrastructure.database.sqlalchemy_config import SessionLocal
    from shared.infrastructure.database.models.misc_models import AnalysisRunModel

    session = SessionLocal()
    try:
        count = session.query(AnalysisRunModel).count()
        if count > 0:
            return

        import re
        from datetime import datetime

        migrated = 0

        if not os.path.isdir(data_dir):
            return

        for filename in os.listdir(data_dir):
            match = re.match(r"dashboard_insights_(\d+)\.json", filename)
            if match:
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath) as f:
                        data = json.load(f)
                    session.add(AnalysisRunModel(
                        page="dashboard",
                        created_at=datetime.now().isoformat(),
                        analysis_json=json.dumps(data, ensure_ascii=False),
                    ))
                    migrated += 1
                except Exception as e:
                    print(f"Warning: Failed to migrate {filename}: {e}")

        for filename in os.listdir(data_dir):
            match = re.match(r"skills_insights_(\d+)\.json", filename)
            if match:
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath) as f:
                        data = json.load(f)
                    session.add(AnalysisRunModel(
                        page="skills",
                        created_at=datetime.now().isoformat(),
                        analysis_json=json.dumps(data, ensure_ascii=False),
                    ))
                    migrated += 1
                except Exception as e:
                    print(f"Warning: Failed to migrate {filename}: {e}")

        session.commit()
        print(f"Migrated {migrated} analysis records to analysis_runs table")
    finally:
        session.close()


def migrate_resume_files_to_db():
    """Migrate existing resume files from inputs/ and resumes/ to the DB."""
    import glob as globmod
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    from shared.infrastructure.database.sqlalchemy_config import SessionLocal
    from shared.infrastructure.database.models.misc_models import ResumeModel

    session = SessionLocal()
    try:
        # 1. Migrate master resume from inputs/original/resume.txt
        master_path = os.path.join(project_root, "inputs", "original", "resume.txt")
        if os.path.exists(master_path):
            existing = session.query(ResumeModel).filter(ResumeModel.id.like("original_%")).count()
            if existing == 0:
                with open(master_path) as f:
                    raw_text = f.read().strip()
                if raw_text:
                    content_html = _text_to_html(raw_text)
                    from datetime import datetime
                    session.add(ResumeModel(
                        id="original_1", title="Resume v1", company="", role="",
                        content=content_html, version=1, raw_text=raw_text,
                        created_at=datetime.now().isoformat(),
                    ))
                    session.commit()
                    print(f"[migrate] Imported master resume from {master_path}")
                    try:
                        os.remove(master_path)
                    except OSError:
                        pass
            else:
                try:
                    os.remove(master_path)
                except OSError:
                    pass

        # 2. Migrate tailored resumes from resumes/by_job/
        by_job_dir = os.path.join(project_root, "resumes", "by_job")
        if os.path.isdir(by_job_dir):
            txt_files = sorted(globmod.glob(os.path.join(by_job_dir, "*.txt")))
            migrated_count = 0
            for filepath in txt_files:
                basename = os.path.basename(filepath)
                parts = basename.replace('.txt', '').split('_', 2)
                company = parts[1] if len(parts) > 1 else basename
                role = parts[2].replace('_', ' ') if len(parts) > 2 else ''

                with open(filepath) as f:
                    raw_text = f.read().strip()
                if not raw_text:
                    continue

                resume_id = f"file_{basename.replace('.txt', '')}"
                existing = session.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
                if not existing:
                    from datetime import datetime
                    content_html = _text_to_html(raw_text)
                    session.add(ResumeModel(
                        id=resume_id, title=f"{company} (File Import)",
                        company=company, role=role, content=content_html,
                        version=1, raw_text=raw_text,
                        created_at=datetime.now().isoformat(),
                    ))
                    migrated_count += 1

            session.commit()
            if migrated_count > 0:
                print(f"[migrate] Imported {migrated_count} tailored resumes from {by_job_dir}")

            for filepath in txt_files:
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            try:
                os.rmdir(by_job_dir)
            except OSError:
                pass

    finally:
        session.close()


def _text_to_html(text):
    """Convert plain text resume to simple HTML."""
    import re
    lines = text.strip().split('\n')
    html_parts = []
    for line in lines:
        line = line.strip()
        if not line:
            html_parts.append('<br/>')
            continue
        if re.match(r'^[A-Z][A-Z\s]{3,}$', line) or line in ('Summary', 'Experience', 'Education', 'Skills', 'Projects', 'Certifications', 'Languages'):
            html_parts.append(f'<h3 style="margin:12px 0 4px;font-size:13px;border-bottom:1px solid #ddd;padding-bottom:2px;">{line}</h3>')
        elif line.startswith('•') or line.startswith('-'):
            html_parts.append(f'<li style="margin:2px 0;font-size:11px;">{line.lstrip("•- ")}</li>')
        else:
            html_parts.append(f'<p style="margin:3px 0;font-size:11px;">{line}</p>')
    return '\n'.join(html_parts)


if __name__ == "__main__":
    init_db()
    load_json_to_db()
    migrate_existing_analysis_files()
    migrate_resume_files_to_db()
    print(f"Database initialized at {DB_PATH}")

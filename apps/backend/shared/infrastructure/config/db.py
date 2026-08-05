"""Database initialization and path configuration.

Table creation is handled by SQLAlchemy models + Alembic.
This module provides DB_PATH and one-time data migration utilities.
"""

import json
import os

from dotenv import load_dotenv
from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.utils import text_to_html
load_dotenv()

log = get_logger('db')

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
    from shared.infrastructure.database.sqlalchemy_config import engine, Base, ensure_schemas
    ensure_schemas()
    # Import all models to register them with Base.metadata
    import jobs.infrastructure.models.job_model
    import jobs.infrastructure.models.misc_models
    import skills.infrastructure.models.skill_model
    import skills.infrastructure.models.skill_roadmap_models
    import companies.infrastructure.models.company_model
    import rules.infrastructure.models.rule_model

    Base.metadata.create_all(bind=engine)

    # Seed initial rules if table is empty
    from shared.infrastructure.database.sqlalchemy_config import SessionLocal
    from rules.infrastructure.models.rule_model import RuleModel
    session = SessionLocal()
    try:
        count = session.query(RuleModel).count()
        if count == 0:
            _seed_initial_rules(session)
    finally:
        session.close()


def _seed_initial_rules(session):
    """Seed the initial scoring rules into the rules table."""
    from rules.infrastructure.models.rule_model import RuleModel

    rules = [
        # Shared rules
        ("success", "shared", "SHARED", "visa_and_relocation_compatibility",
         "Evaluate visa sponsorship and relocation support.", "Main impact: Success Score", 100),
        ("success", "shared", "SHARED", "market_and_location_accessibility",
         "Evaluate location accessibility.", "Main impact: Success Score", 95),
        ("success", "shared", "SHARED", "communication_and_work_culture",
         "Evaluate work culture and communication.", "Main impact: Success Score", 80),
        ("success", "shared", "SHARED", "sensitive_industry_penalty",
         "Reduce score for sensitive industries.", "Main impact: Success Score", 60),
        # Job rules
        ("fit", "job", "JOB", "python_backend_core",
         "Python must be the primary language.", "Core Python backend requirement", 100),
        ("fit", "job", "JOB", "role_alignment",
         "Backend engineer, Platform engineer.", "Title patterns that match", 85),
        ("success", "job", "JOB", "hiring_probability",
         "Assess hiring likelihood.", "Application success likelihood", 80),
        ("fit", "job", "JOB", "technical_synergy",
         "Evaluate technical synergy.", "Cloud and backend infrastructure overlap", 75),
        ("fit", "job", "JOB", "engineering_depth",
         "Evaluate engineering depth.", "Seniority and depth match", 70),
        ("fit", "job", "JOB", "work_and_communication_fit",
         "Evaluate work arrangement and culture.", "Work culture compatibility", 65),
        ("fit", "job", "JOB", "candidate_job_alignment",
         "Evaluate how well the specific job matches.", "Profile-to-job match quality", 55),
        # Product company rules
        ("fit", "company", "COMPANY_PRODUCT", "company_quality",
         "Evaluate company quality.", "Core company evaluation", 100),
        ("fit", "company", "COMPANY_PRODUCT", "engineering_culture",
         "Evaluate engineering culture.", "Engineering team quality", 90),
        ("fit", "company", "COMPANY_PRODUCT", "growth_and_career_potential",
         "Evaluate growth opportunities.", "Career advancement potential", 80),
        ("fit", "company", "COMPANY_PRODUCT", "candidate_company_alignment",
         "Evaluate alignment with candidate profile.", "Profile match quality", 65),
        ("fit", "company", "COMPANY_PRODUCT", "product_maturity",
         "Evaluate product maturity signals.", "Product viability assessment", 50),
        # Recruiting company rules
        ("fit", "recruiter", "COMPANY_RECRUITING", "recruiter_network_value",
         "Evaluate recruiter value.", "Main impact: Company Fit Score", 100),
        ("success", "recruiter", "COMPANY_RECRUITING", "recruiter_market_access",
         "Evaluate market access.", "Main impact: Company Success Score", 95),
        ("fit", "recruiter", "COMPANY_RECRUITING", "recruiter_profile_alignment",
         "Evaluate profile alignment.", "Main impact: Company Fit Score", 85),
        ("success", "recruiter", "COMPANY_RECRUITING", "recruiter_activity_and_opportunity",
         "Evaluate opportunity generation.", "Main impact: Company Success Score", 70),
    ]

    for cat, rule_type, scope, key, value, desc, priority in rules:
        session.add(RuleModel(
            category=cat, rule_type=rule_type, scope=scope, key=key,
            value=value, description=desc, priority=priority,
        ))
    session.commit()
    log.info("Seeded scoring rules", count=len(rules))


def load_json_to_db():
    """No-op: data is now managed entirely in SQLite."""
    pass


def migrate_resume_files_to_db():
    """Migrate existing resume files from inputs/ and resumes/ to the DB."""
    import glob as globmod
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    from shared.infrastructure.database.sqlalchemy_config import SessionLocal
    from jobs.infrastructure.models.misc_models import ResumeModel

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
                    content_html = text_to_html(raw_text)
                    from datetime import datetime
                    session.add(ResumeModel(
                        id="original_1", title="Resume v1", company="", role="",
                        content=content_html, version=1, raw_text=raw_text,
                        created_at=datetime.now().isoformat(),
                    ))
                    session.commit()
                    log.info("Imported master resume", path=master_path)
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
                    content_html = text_to_html(raw_text)
                    session.add(ResumeModel(
                        id=resume_id, title=f"{company} (File Import)",
                        company=company, role=role, content=content_html,
                        version=1, raw_text=raw_text,
                        created_at=datetime.now().isoformat(),
                    ))
                    migrated_count += 1

            session.commit()
            if migrated_count > 0:
                log.info("Imported tailored resumes", count=migrated_count, path=str(by_job_dir))

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
    """Convert plain text resume to simple HTML (shared helper).

    Delegates to shared.infrastructure.utils.text_to_html.
    """
    from shared.infrastructure.utils import text_to_html as _shared_text_to_html
    return _shared_text_to_html(text)


if __name__ == "__main__":
    init_db()
    load_json_to_db()
    migrate_resume_files_to_db()
    log.info("Database initialized", path=DB_PATH)

import json
from pathlib import Path
from backend.app.core.database import engine, SessionLocal, Base
from backend.app.models import User, Rule
from backend.app.core.security import get_password_hash
from backend.app.core.config import settings

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed users if empty
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            print("Seeding initial users...")
            users = [
                User(
                    username="admin",
                    email="admin@labelsure.gov.in",
                    hashed_password=get_password_hash("Admin@LabelSure2026"),
                    full_name="Chief Legal Metrology Officer",
                    role="ADMIN",
                    badge_number="CLM-DL-001"
                ),
                User(
                    username="inspector1",
                    email="inspector1@labelsure.gov.in",
                    hashed_password=get_password_hash("Inspector@2026"),
                    full_name="Rajesh Sharma (Inspector)",
                    role="INSPECTOR",
                    badge_number="INS-DL-412"
                ),
                User(
                    username="supervisor1",
                    email="supervisor1@labelsure.gov.in",
                    hashed_password=get_password_hash("Supervisor@2026"),
                    full_name="Priya Varma (Assistant Controller)",
                    role="SUPERVISOR",
                    badge_number="SUP-DL-105"
                ),
                User(
                    username="viewer1",
                    email="viewer1@labelsure.gov.in",
                    hashed_password=get_password_hash("Viewer@2026"),
                    full_name="Compliance Audit Observer",
                    role="VIEWER",
                    badge_number="AUD-GOV-999"
                )
            ]
            db.add_all(users)
            db.commit()
            print("Users seeded successfully.")
            
        # Seed rules from versioned JSON files
        rules_dir = settings.RULES_DIR / "versions"
        if rules_dir.exists():
            for rule_file in rules_dir.glob("*.json"):
                print(f"Loading rules from {rule_file.name}...")
                with open(rule_file, "r", encoding="utf-8") as f:
                    rule_list = json.load(f)
                    for r_data in rule_list:
                        existing = db.query(Rule).filter(
                            Rule.rule_id == r_data["rule_id"],
                            Rule.rule_version == r_data["rule_version"]
                        ).first()
                        if not existing:
                            rule_obj = Rule(
                                rule_id=r_data["rule_id"],
                                rule_version=r_data["rule_version"],
                                clause_reference=r_data["clause_reference"],
                                requirement=r_data["requirement"],
                                applicability=r_data["applicability"],
                                validation_logic=r_data["validation_logic"],
                                severity=r_data.get("severity", "HIGH"),
                                effective_from=r_data["effective_from"],
                                effective_to=r_data.get("effective_to"),
                                source_document=r_data["source_document"],
                                source_url=r_data["source_url"],
                                notes=r_data.get("notes")
                            )
                            db.add(rule_obj)
            db.commit()
            print("Versioned rules loaded successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()

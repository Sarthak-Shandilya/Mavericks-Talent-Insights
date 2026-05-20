"""Initialize SQLite database with all required data."""
import random
import sys
from datetime import date, datetime, timedelta, UTC

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Initialize engine
engine = create_engine("sqlite:///./mavericks.db")


def setup_database():
    """Create tables, seed reference data, users, and test data."""
    print("Setting up database...")

    import models  # noqa — register ORM mappers
    from models.base import Base
    from utils.security import hash_password

    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")

    with Session(engine) as session:
        from models.user import Role
        try:
            if session.query(Role).count() > 0:
                print("✓ Database already seeded")
                return
        except Exception:
            pass

        # ------------------------------------------------------------------ #
        # Roles
        # ------------------------------------------------------------------ #
        print("Seeding roles...")
        from models.user import Role, User

        roles = {}
        for name, desc in [
            ("system_admin",          "Users, config, audit"),
            ("training_coordinator",  "Bulk upload and stage updates"),
            ("trainer",               "Review trainee performance"),
            ("hr",                    "Training outcomes and insights"),
            ("business_head",         "Dashboards and effectiveness"),
        ]:
            r = Role(name=name, description=desc)
            session.add(r)
            roles[name] = r
        session.flush()

        # ------------------------------------------------------------------ #
        # Streams
        # ------------------------------------------------------------------ #
        print("Seeding streams...")
        from models.reference import Stream, TrainingStageType

        stream_objs = {}
        for code, label in [("java", "Java Full Stack"), ("data", "Data Engineering"),
                             ("qa", "QA Automation"), ("cloud", "Cloud DevOps")]:
            s = Stream(code=code, label=label, is_active=True)
            session.add(s)
            stream_objs[code] = s
        session.flush()

        # ------------------------------------------------------------------ #
        # Training stage types
        # ------------------------------------------------------------------ #
        print("Seeding training stage types...")
        stage_objs = {}
        for code, label, order in [
            ("spark",       "Spark Training",         1),
            ("foundation",  "Foundation",             2),
            ("coding",      "Coding Phase",           3),
            ("project",     "Project Phase",          4),
            ("competency",  "Competency Development", 5),
        ]:
            st = TrainingStageType(code=code, label=label, sort_order=order, is_active=True)
            session.add(st)
            stage_objs[code] = st
        session.flush()

        # ------------------------------------------------------------------ #
        # Users
        # ------------------------------------------------------------------ #
        print("Creating users...")
        users_seed = [
            ("sarthaks3@hexaware.com",   "Sarthak1@",   "Sarthak Sharma",        "system_admin"),
            ("tc1@hexaware.com",         "Coordinator1@", "Riya Patel",          "training_coordinator"),
            ("trainer1@hexaware.com",    "Trainer1@",   "John Doe",              "trainer"),
            ("hr1@hexaware.com",         "HR1pass@",    "Anjali Gupta",          "hr"),
            ("bh1@hexaware.com",         "BH1pass@",    "Vikram Singh",          "business_head"),
        ]
        user_objs = {}
        for email, pw, name, role_key in users_seed:
            u = User(email=email, password_hash=hash_password(pw),
                     full_name=name, role_id=roles[role_key].id, is_active=True)
            session.add(u)
            user_objs[email] = u
        session.flush()

        # ------------------------------------------------------------------ #
        # Batches
        # ------------------------------------------------------------------ #
        print("Creating batches...")
        from models.trainee import Batch

        batch_objs = {}
        for code, name, start, stream_hint in [
            ("BATCH-2025-Q3", "Batch 2025 Q3", date(2025, 7, 1),  "java"),
            ("BATCH-2025-Q4", "Batch 2025 Q4", date(2025, 10, 1), "data"),
            ("BATCH-2026-Q1", "Batch 2026 Q1", date(2026, 1, 15), "qa"),
        ]:
            b = Batch(code=code, name=name, start_date=start,
                      location="Bangalore", stream_hint=stream_hint)
            session.add(b)
            batch_objs[code] = b
        session.flush()

        # ------------------------------------------------------------------ #
        # Trainees (20 across 3 batches)
        # ------------------------------------------------------------------ #
        print("Creating trainees with stages, assessments & performance data...")
        from models.automation import PerformanceClassification
        from models.trainee import Assessment, Trainee, TraineeCompetency, TraineeStage

        first_names = ["Rahul", "Priya", "Amit", "Anjali", "Vikram", "Sneha",
                       "Karthik", "Divya", "Rohan", "Pooja", "Arjun", "Kavya",
                       "Deepak", "Swati", "Anil", "Meera", "Ravi", "Nisha", "Suresh", "Ritu"]
        last_names  = ["Kumar", "Sharma", "Reddy", "Patel", "Singh", "Nair",
                       "Iyer", "Rao", "Gupta", "Verma"]
        colleges    = ["JNTU College", "Anna University", "VIT University",
                       "SRM Institute", "BITS Pilani", "NIT Warangal"]
        cities      = ["Bangalore", "Hyderabad", "Chennai", "Pune", "Mumbai"]
        states      = ["Karnataka", "Telangana", "Tamil Nadu", "Maharashtra", "Maharashtra"]
        statuses    = ["Active", "Active", "Active", "On Hold", "Completed"]  # weighted
        competencies = ["Java Full Stack", "Data Engineering", "QA Automation", "Cloud DevOps"]

        batch_stream_map = {
            "BATCH-2025-Q3": ("java",  stream_objs["java"]),
            "BATCH-2025-Q4": ("data",  stream_objs["data"]),
            "BATCH-2026-Q1": ("qa",    stream_objs["qa"]),
        }

        all_trainees = []
        for i in range(1, 21):
            batch_code = random.choice(list(batch_objs.keys()))
            batch_obj  = batch_objs[batch_code]
            stream_code, stream_obj = batch_stream_map[batch_code]

            first = first_names[i - 1]
            last  = random.choice(last_names)
            city_idx = random.randint(0, len(cities) - 1)
            doj  = batch_obj.start_date + timedelta(days=random.randint(0, 30))
            training_status = random.choice(statuses)

            current_stage = random.choice(list(stage_objs.values()))

            t = Trainee(
                employee_id=f"EMP{10000 + i}",
                superset_id=f"SUP{20000 + i}",
                doj=doj,
                full_name=f"{first} {last}",
                gender="Male" if i % 2 == 0 else "Female",
                email=f"{first.lower()}.{last.lower()}{i}@example.com",
                phone=f"+91-{9000000000 + i}",
                college_name=random.choice(colleges),
                college_city=cities[city_idx],
                college_state=states[city_idx],
                base_location=random.choice(cities),
                current_training_location="Bangalore",
                training_status=training_status,
                stream_id=stream_obj.id,
                current_training_stage_id=current_stage.id,
                category=random.choice(["Fresher", "Lateral"]),
                assigned_competency=random.choice(competencies),
                batch_id=batch_obj.id,
                is_active=True,
            )
            session.add(t)
            all_trainees.append(t)
        session.flush()

        # Training stages per trainee
        tc_user = user_objs["tc1@hexaware.com"]
        stage_statuses = ["Completed", "Completed", "Pending", "Not Applicable"]
        for trainee in all_trainees:
            for stage in stage_objs.values():
                ts = TraineeStage(
                    trainee_id=trainee.id,
                    stage_type_id=stage.id,
                    status=random.choice(stage_statuses),
                    score=round(random.uniform(50, 100), 2),
                    attempts=random.randint(1, 3),
                    completion_date=date(2025, 10, 1) if random.random() > 0.4 else None,
                    updated_by_user_id=tc_user.id,
                )
                session.add(ts)
        session.flush()

        # Assessments per trainee
        assessment_catalog = [
            ("Spark",      "SP_P1_A1"), ("Spark", "SP_P1_A2"), ("Spark", "SP_FINAL"),
            ("Foundation", "FM1"),      ("Foundation", "FM2"),  ("Foundation", "FM3"),
            ("Technical",  "SQL"),      ("Technical", "Java"),  ("Technical", "Python"),
            ("Coding",     "CT1"),      ("Coding", "CT2"),      ("Coding", "CT3"),
        ]
        for trainee in all_trainees:
            for program, code in random.sample(assessment_catalog, k=random.randint(4, 8)):
                a = Assessment(
                    trainee_id=trainee.id,
                    program=program,
                    assessment_code=code,
                    attempt_no=1,
                    score=round(random.uniform(40, 100), 2),
                    max_score=100,
                    assessment_date=date(2025, 11, 1) + timedelta(days=random.randint(0, 90)),
                )
                session.add(a)

        # Competencies per trainee
        for trainee in all_trainees:
            TraineeCompetency(
                trainee_id=trainee.id,
                competency_name=trainee.assigned_competency,
                status=random.choice(["Not Started", "In Progress", "Completed"]),
                skill_level=random.choice(["Beginner", "Intermediate", "Advanced"]),
                readiness_flag=random.random() > 0.6,
            )
        session.flush()

        # Performance classifications
        for trainee in all_trainees:
            composite = round(random.uniform(35, 95), 2)
            if composite >= 75:
                classification = "HIGH"
            elif composite >= 50:
                classification = "AVERAGE"
            else:
                classification = "LOW"
            pc = PerformanceClassification(
                trainee_id=trainee.id,
                classification=classification,
                composite_score=composite,
            )
            session.add(pc)

        session.commit()
        print("✓ All test data seeded successfully")
        print("\n=== Credentials ===")
        for email, pw, name, role_key in users_seed:
            print(f"  [{role_key:22s}]  {email:35s}  pw: {pw}")


if __name__ == "__main__":
    try:
        setup_database()
        print("\n✓ Setup complete!")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



def setup_database():
    """Create tables and seed reference data."""
    print("Setting up database...")
    
    # Import models to register them
    import models  # noqa
    from models.base import Base
    from utils.security import hash_password
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")
    
    with Session(engine) as session:
        # Check if already seeded
        from models.user import Role
        try:
            result = session.query(Role).count()
            if result > 0:
                print("✓ Database already seeded")
                return
        except:
            pass  # Table might not exist yet
        
        # Insert roles using ORM
        print("Seeding roles...")
        from models.user import Role, User
        
        roles_data = [
            ("system_admin", "Users, config, audit"),
            ("training_coordinator", "Bulk upload and stage updates"),
            ("trainer", "Review trainee performance"),
            ("hr", "Training outcomes and insights"),
            ("business_head", "Dashboards and effectiveness"),
        ]
        
        roles = {}
        for role_name, description in roles_data:
            role = Role(name=role_name, description=description)
            session.add(role)
            roles[role_name] = role
        
        session.flush()  # Assign IDs but don't commit yet
        
        # Insert streams using ORM
        print("Seeding streams...")
        from models.reference import Stream
        
        streams_data = [
            ("java", "Java Full Stack"),
            ("data", "Data Engineering"),
            ("qa", "QA Automation"),
            ("cloud", "Cloud DevOps"),
        ]
        
        for code, label in streams_data:
            stream = Stream(code=code, label=label, is_active=True)
            session.add(stream)
        
        # Insert training stage types using ORM
        print("Seeding training stages...")
        from models.reference import TrainingStageType
        
        stages_data = [
            ("spark", "Spark Training", 1),
            ("foundation", "Foundation", 2),
            ("coding", "Coding Phase", 3),
            ("project", "Project Phase", 4),
            ("competency", "Competency Development", 5),
        ]
        
        for code, label, order in stages_data:
            stage = TrainingStageType(code=code, label=label, sort_order=order, is_active=True)
            session.add(stage)
        
        # Insert admin user using ORM
        print("Creating admin user...")
        admin_email = "sarthaks3@hexaware.com"
        admin_password = "Sarthak1@"
        admin_hash = hash_password(admin_password)
        
        admin_user = User(
            email=admin_email,
            password_hash=admin_hash,
            full_name="System Administrator",
            role_id=roles["system_admin"].id,
            is_active=True
        )
        session.add(admin_user)
        
        session.commit()
        print("✓ Database seeded successfully")
        print(f"\nAdmin credentials:")
        print(f"  Email: {admin_email}")
        print(f"  Password: {admin_password}")


if __name__ == "__main__":
    try:
        setup_database()
        print("\n✓ Setup complete!")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

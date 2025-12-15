from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import db_models, auth

load_dotenv()

def create_admin_user(email: str, password: str):
    db: Session = SessionLocal()

    try:
        existing_user = db.query(db_models.User).filter(db_models.User.email == email).first()
        if existing_user:
            print(f"User {email} already exists. Updating to admin role...")

            admin_role = db.query(db_models.Role).filter(db_models.Role.name == "admin").first()
            if not admin_role:
                admin_role = db_models.Role(name="admin")
                db.add(admin_role)
                db.commit()
                db.refresh(admin_role)

            existing_user.role_id = admin_role.id
            db.commit()
            return

        admin_role = db.query(db_models.Role).filter(db_models.Role.name == "admin").first()
        if not admin_role:
            admin_role = db_models.Role(name="admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)

        # Create admin user
        hashed_password = auth.get_password_hash(password)
        admin_user = db_models.User(
            email=email,
            password=hashed_password,
            role_id=admin_role.id
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print(f"Admin user created successfully!")
        print(f"   Email: {email}")
        print(f"   Role: admin")

    except Exception as e:
        print(f"{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    email = "admin@example.com"
    password = "admin123"

    print(f"Creating admin user: {email}")
    create_admin_user(email, password)

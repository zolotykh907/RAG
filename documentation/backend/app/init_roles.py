from sqlalchemy.orm import Session
from . import db_models
from .database import SessionLocal


def init_roles():
    """Initialize roles in the database"""
    db = SessionLocal()
    try:
        existing_roles = db.query(db_models.Role).count()
        if existing_roles > 0:
            print("Roles already exist, skipping initialization")
            return

        user_role = db_models.Role(name="user")
        admin_role = db_models.Role(name="admin")

        db.add(user_role)
        db.add(admin_role)
        db.commit()

        print("Roles initialized successfully: user, admin")
    except Exception as e:
        print(f"Error initializing roles: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_roles()

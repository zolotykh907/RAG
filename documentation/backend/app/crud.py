from sqlalchemy.orm import Session
from . import db_models, schemas


def create_page(db: Session, page: schemas.PageCreate):
    db_page = db_models.Page(name=page.name, url=page.url)
    db.add(db_page)
    db.commit()
    db.refresh(db_page)

    db_kpi = db_models.KPI(page_id=db_page.id, visits=0, total_time_seconds=0)
    db.add(db_kpi)
    db.commit()
    db.refresh(db_page)

    return db_page


def get_page_by_id(db: Session, page_id: int):
    return db.query(db_models.Page).filter(db_models.Page.id == page_id).first()


def get_all_pages_with_kpi(db: Session):
    return db.query(db_models.Page).all()


def increment_page_visit(db: Session, page_id: int):
    kpi = db.query(db_models.KPI).filter(db_models.KPI.page_id == page_id).first()
    if kpi:
        kpi.visits += 1
        db.commit()
        db.refresh(kpi)
    return kpi


def update_page_time(db: Session, page_id: int, time_seconds: int):
    kpi = db.query(db_models.KPI).filter(db_models.KPI.page_id == page_id).first()
    if kpi:
        kpi.total_time_seconds += time_seconds
        db.commit()
        db.refresh(kpi)
    return kpi


def delete_page(db: Session, page_id: int):
    """Delete a page and its KPI data (CASCADE)"""
    db_page = db.query(db_models.Page).filter(db_models.Page.id == page_id).first()
    if db_page:
        db.delete(db_page)
        db.commit()
        return True
    return False

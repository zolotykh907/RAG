import os
import json
import io
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import requests
from sqlalchemy.orm import Session
import uvicorn
from PIL import Image

from app.database import SessionLocal
from app import crud, schemas, db_models, auth
from app.auth_router import router as auth_router


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
POSTS_URL = os.getenv("POSTS_URL")
POSTS_PATH = os.getenv("POSTS_PATH")

app = FastAPI(
    title="Documentation",
    description="API for OTD",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/pages", response_model=schemas.PageWithKPI, status_code=status.HTTP_201_CREATED)
def create_page(
    page: schemas.PageCreate,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_user)
):
    """Create a new page with associated KPI record"""
    db_page = crud.create_page(db=db, page=page)
    return db_page


@app.get("/pages/{page_id}", response_model=schemas.PageWithKPI)
def get_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_user)
):
    """Get page by ID with its KPI data"""
    db_page = crud.get_page_by_id(db=db, page_id=page_id)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return db_page


@app.post("/pages/{page_id}/visit")
def visit_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_user)
):
    """Increment visit counter for a page"""
    db_page = crud.get_page_by_id(db=db, page_id=page_id)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    kpi = crud.increment_page_visit(db=db, page_id=page_id)
    return {"message": "Visit recorded", "visits": kpi.visits}


@app.post("/pages/{page_id}/time")
def update_time_spent(
    page_id: int,
    time_data: schemas.TimeUpdate,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_user)
):
    """Update time spent on a page"""
    db_page = crud.get_page_by_id(db=db, page_id=page_id)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    kpi = crud.update_page_time(db=db, page_id=page_id, time_seconds=time_data.time_seconds)
    return {"message": "Time updated", "total_time_seconds": kpi.total_time_seconds}


@app.get("/kpi", response_model=list[schemas.PageWithKPI])
def get_all_kpi(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_admin_user)
):
    """Get KPI data for all pages"""
    return crud.get_all_pages_with_kpi(db=db)


@app.delete("/pages/{page_id}", status_code=status.HTTP_200_OK)
def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_admin_user)
):
    """Delete a page and its KPI data (admin only)"""
    deleted = crud.delete_page(db=db, page_id=page_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"message": f"Page with ID {page_id} deleted successfully"}


@app.get('/posts')
async def get_posts(current_user: db_models.User = Depends(auth.get_current_user)):
    if not os.path.exists(POSTS_PATH):
        data = requests.get(POSTS_URL).json()
        with open(POSTS_PATH, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    else:
        with open(POSTS_PATH, 'r') as f:
            data = json.load(f)

    return data


@app.post("/flip")
async def flip_image(
    file: UploadFile = File(...),
    current_user: db_models.User = Depends(auth.get_current_user)
):
    image = Image.open(file.file)
    converted = image.transpose(Image.FLIP_TOP_BOTTOM)

    buf = io.BytesIO()
    converted.save(buf, format=image.format or "PNG")
    buf.seek(0)

    filename = f"flipped_{file.filename}"
    encoded_filename = quote(filename.encode('utf-8'))

    return Response(
        buf.read(),
        media_type=f"image/{image.format.lower() if image.format else 'png'}",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
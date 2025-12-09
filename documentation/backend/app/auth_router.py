from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import schemas, db_models, auth

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserRegister, db: Session = Depends(auth.get_db)):
    """Register a new user"""
    existing_user = db.query(db_models.User).filter(db_models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user_role = db.query(db_models.Role).filter(db_models.Role.name == "user").first()
    if not user_role:
        user_role = db_models.Role(name="user")
        db.add(user_role)
        db.commit()
        db.refresh(user_role)

    hashed_password = auth.get_password_hash(user_data.password)
    new_user = db_models.User(
        email=user_data.email,
        password=hashed_password,
        role_id=user_role.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(auth.get_db)):
    """Login and get JWT token"""
    user = db.query(db_models.User).filter(db_models.User.email == form_data.username).first()

    # Verify user exists and password is correct
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: db_models.User = Depends(auth.get_current_user)):
    """Get current user information"""
    return current_user

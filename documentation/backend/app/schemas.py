from pydantic import BaseModel, EmailStr
from typing import Optional


# Auth
class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class RoleResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    email: str
    role: RoleResponse

    class Config:
        from_attributes = True


# Page
class PageCreate(BaseModel):
    name: str
    url: str


class PageResponse(BaseModel):
    id: int
    name: str
    url: str

    class Config:
        from_attributes = True


class KPIResponse(BaseModel):
    id: int
    page_id: int
    visits: int
    total_time_seconds: int

    class Config:
        from_attributes = True


class PageWithKPI(BaseModel):
    id: int
    name: str
    url: str
    kpi: KPIResponse

    class Config:
        from_attributes = True


class TimeUpdate(BaseModel):
    time_seconds: int

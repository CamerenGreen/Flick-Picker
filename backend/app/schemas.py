from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    name: str


class UserOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class ViewingCreate(BaseModel):
    tmdb_id: int
    rating: Optional[float] = None

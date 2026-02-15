"""Pydantic schemas for request/response validation."""
from typing import Optional
from pydantic import BaseModel, Field


# ----- Author -----
class AuthorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class AuthorResponse(AuthorBase):
    id: int

    class Config:
        from_attributes = True


class AuthorWithBooks(AuthorResponse):
    book_count: int = 0


# ----- Category -----
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# ----- Book -----
class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    isbn: Optional[str] = Field(None, max_length=20)
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    category_id: Optional[int] = None
    author_ids: list[int] = Field(default_factory=list)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    isbn: Optional[str] = Field(None, max_length=20)
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    category_id: Optional[int] = None
    author_ids: Optional[list[int]] = None


class AuthorRef(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CategoryRef(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class BookResponse(BaseModel):
    id: int
    title: str
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    category_id: Optional[int] = None
    category: Optional[CategoryRef] = None
    authors: list[AuthorRef] = []

    class Config:
        from_attributes = True

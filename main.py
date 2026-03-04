from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc

from database import engine, get_db, Base
from models import Book, Author, Category
from schemas import (
    BookCreate, BookResponse, AuthorRef, CategoryRef,
    AuthorCreate, AuthorResponse, CategoryCreate, CategoryResponse,
    BookUpdate, AuthorUpdate,
)
from auth import validate_credentials


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Library API", lifespan=lifespan)

# Routes that do NOT require authentication
NO_AUTH = {"/docs", "/redoc", "/openapi.json", "/"}

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication Middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):

    # Allow CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    # Allow public routes
    if request.url.path in NO_AUTH:
        return await call_next(request)

    # Validate auth
    if validate_credentials(request) is None:
        return JSONResponse(
            status_code=401,
            content={"detail": "Use Basic Auth: admin / admin123"}
        )

    return await call_next(request)


@app.get("/")
def root():
    return {"message": "Library API", "docs": "/docs"}


# ========================
# BOOKS
# ========================

@app.get("/books", response_model=list[BookResponse])
def list_books(
    author_id: Optional[int] = None,
    category_id: Optional[int] = None,
    year: Optional[int] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    limit: Optional[int] = Query(None, ge=1, le=1000),
    sort: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Book).options(joinedload(Book.authors), joinedload(Book.category))

    if author_id is not None:
        q = q.filter(Book.authors.any(Author.id == author_id))

    if category_id is not None:
        q = q.filter(Book.category_id == category_id)

    if year is not None:
        q = q.filter(Book.publication_year == year)
    else:
        if year_min is not None:
            q = q.filter(Book.publication_year >= year_min)
        if year_max is not None:
            q = q.filter(Book.publication_year <= year_max)

    if sort == "title_asc":
        q = q.order_by(asc(Book.title))

    if limit is not None:
        q = q.limit(limit)

    books = q.all()
    return [_to_book_response(b) for b in books]


@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).options(joinedload(Book.authors), joinedload(Book.category)).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(404, "Book not found")

    return _to_book_response(book)


@app.post("/books", response_model=BookResponse)
def create_book(body: BookCreate, db: Session = Depends(get_db)):

    authors = db.query(Author).filter(Author.id.in_(body.author_ids or [])).all() if body.author_ids else []

    if body.author_ids and len(authors) != len(body.author_ids):
        raise HTTPException(400, "Invalid author IDs")

    category = db.query(Category).filter(Category.id == body.category_id).first() if body.category_id else None

    if body.category_id and not category:
        raise HTTPException(404, "Category not found")

    book = Book(
        title=body.title,
        isbn=body.isbn,
        publication_year=body.publication_year,
        category_id=body.category_id
    )

    db.add(book)
    db.flush()

    for a in authors:
        book.authors.append(a)

    db.commit()
    db.refresh(book)

    return _to_book_response(book)


@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, body: BookUpdate, db: Session = Depends(get_db)):

    book = db.query(Book).options(joinedload(Book.authors)).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(404, "Book not found")

    if body.title is not None:
        book.title = body.title

    if body.isbn is not None:
        book.isbn = body.isbn

    if body.publication_year is not None:
        book.publication_year = body.publication_year

    if body.category_id is not None:
        if body.category_id:
            category = db.query(Category).filter(Category.id == body.category_id).first()
            if not category:
                raise HTTPException(404, "Category not found")

        book.category_id = body.category_id

    if body.author_ids is not None:
        authors = db.query(Author).filter(Author.id.in_(body.author_ids)).all() if body.author_ids else []

        if body.author_ids and len(authors) != len(body.author_ids):
            raise HTTPException(400, "Invalid author IDs")

        book.authors = authors

    db.commit()
    db.refresh(book)

    return _to_book_response(book)


@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):

    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(404, "Book not found")

    db.delete(book)
    db.commit()

    return {"status": "deleted", "id": book_id}


def _to_book_response(b: Book) -> BookResponse:

    return BookResponse(
        id=b.id,
        title=b.title,
        isbn=b.isbn,
        publication_year=b.publication_year,
        category_id=b.category_id,
        category=CategoryRef(id=c.id, name=c.name) if (c := b.category) else None,
        authors=[AuthorRef(id=a.id, name=a.name) for a in b.authors],
    )


# ========================
# AUTHORS
# ========================

@app.get("/authors", response_model=list[AuthorResponse])
def list_authors(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    sort: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Author)
    if sort == "name_asc":
        q = q.order_by(asc(Author.name))
    if limit is not None:
        q = q.limit(limit)
    return q.all()


@app.get("/authors/{author_id}", response_model=AuthorResponse)
def get_author(author_id: int, db: Session = Depends(get_db)):
    a = db.query(Author).filter(Author.id == author_id).first()

    if not a:
        raise HTTPException(404, "Author not found")

    return a


@app.post("/authors", response_model=AuthorResponse)
def create_author(body: AuthorCreate, db: Session = Depends(get_db)):

    author = Author(name=body.name)

    db.add(author)
    db.commit()
    db.refresh(author)

    return author


@app.put("/authors/{author_id}", response_model=AuthorResponse)
def update_author(author_id: int, body: AuthorUpdate, db: Session = Depends(get_db)):

    a = db.query(Author).filter(Author.id == author_id).first()

    if not a:
        raise HTTPException(404, "Author not found")

    if body.name is not None:
        a.name = body.name

    db.commit()
    db.refresh(a)

    return a


@app.delete("/authors/{author_id}")
def delete_author(author_id: int, db: Session = Depends(get_db)):

    a = db.query(Author).filter(Author.id == author_id).first()

    if not a:
        raise HTTPException(404, "Author not found")

    db.delete(a)
    db.commit()

    return {"status": "deleted", "id": author_id}


# ========================
# CATEGORIES
# ========================

@app.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@app.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):

    c = db.query(Category).filter(Category.id == category_id).first()

    if not c:
        raise HTTPException(404, "Category not found")

    return c


@app.post("/categories", response_model=CategoryResponse)
def create_category(body: CategoryCreate, db: Session = Depends(get_db)):

    if db.query(Category).filter(Category.name == body.name).first():
        raise HTTPException(400, "Category already exists")

    cat = Category(name=body.name)

    db.add(cat)
    db.commit()
    db.refresh(cat)

    return cat


# ========================
# STATS
# ========================

@app.get("/stats/summary")
def stats_summary(db: Session = Depends(get_db)):

    books = db.query(Book).options(joinedload(Book.authors), joinedload(Book.category)).all()

    total = len(books)

    years = [b.publication_year for b in books if b.publication_year is not None]

    avg_year = int(round(sum(years) / len(years))) if years else None

    per_author = {}
    for b in books:
        for a in b.authors:
            per_author[a.name] = per_author.get(a.name, 0) + 1

    per_category = {}
    for b in books:
        if b.category:
            per_category[b.category.name] = per_category.get(b.category.name, 0) + 1

    return {
        "total_books": total,
        "average_year": avg_year,
        "books_per_author": sorted(
            [{"name": k, "count": v} for k, v in per_author.items()],
            key=lambda x: -x["count"]
        ),
        "books_per_category": sorted(
            [{"name": k, "count": v} for k, v in per_category.items()],
            key=lambda x: -x["count"]
        ),
    }

@app.get("/stats/author/{author_id}/earliest_latest")
def author_earliest_latest(author_id: int, db: Session = Depends(get_db)):
    a = db.query(Author).filter(Author.id == author_id).first()
    if not a:
        raise HTTPException(404, "Author not found")
    books = (
        db.query(Book)
        .join(Book.authors)
        .filter(Author.id == author_id)
        .order_by(asc(Book.publication_year))
        .all()
    )
    if not books:
        return {"author_id": author_id, "earliest": None, "latest": None}
    earliest = {"title": books[0].title, "year": books[0].publication_year}
    latest = {"title": books[-1].title, "year": books[-1].publication_year}
    return {"author_id": author_id, "earliest": earliest, "latest": latest}

@app.get("/authors/{author_id}/books", response_model=list[BookResponse])
def author_books(author_id: int, db: Session = Depends(get_db)):
    a = db.query(Author).filter(Author.id == author_id).first()
    if not a:
        raise HTTPException(404, "Author not found")
    books = (
        db.query(Book)
        .join(Book.authors)
        .options(joinedload(Book.authors), joinedload(Book.category))
        .filter(Author.id == author_id)
        .order_by(asc(Book.publication_year))
        .all()
    )
    return [_to_book_response(b) for b in books]

@app.get("/stats/category/{category_id}/all_have_year")
def category_all_have_year(category_id: int, db: Session = Depends(get_db)):
    c = db.query(Category).filter(Category.id == category_id).first()
    if not c:
        raise HTTPException(404, "Category not found")
    total = db.query(Book).filter(Book.category_id == category_id).count()
    missing = db.query(Book).filter(Book.category_id == category_id, Book.publication_year.is_(None)).count()
    return {"category_id": category_id, "all_have_year": missing == 0, "total": total, "missing": missing}

@app.get("/stats/author/{author_id}/has_books")
def author_has_books(author_id: int, db: Session = Depends(get_db)):
    a = db.query(Author).filter(Author.id == author_id).first()
    if not a:
        raise HTTPException(404, "Author not found")
    count = db.query(Book).join(Book.authors).filter(Author.id == author_id).count()
    return {"author_id": author_id, "has_books": count > 0, "count": count}

@app.get("/stats/category/{category_id}/has_books")
def category_has_books(category_id: int, db: Session = Depends(get_db)):
    c = db.query(Category).filter(Category.id == category_id).first()
    if not c:
        raise HTTPException(404, "Category not found")
    count = db.query(Book).filter(Book.category_id == category_id).count()
    return {"category_id": category_id, "has_books": count > 0, "count": count}

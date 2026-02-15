"""FastAPI Library API - main application."""
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from database import engine, get_db, Base
from models import Book, Author, Category, book_author
from schemas import (
    BookCreate, BookUpdate, BookResponse, AuthorRef, CategoryRef,
    AuthorCreate, AuthorUpdate, AuthorResponse,
    CategoryCreate, CategoryResponse,
)
from auth import validate_credentials


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield
    # shutdown if needed


app = FastAPI(title="Library API", lifespan=lifespan)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="Library API. All endpoints require Basic Auth (admin / admin123).",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "httpBasic": {
            "type": "http",
            "scheme": "basic",
            "description": "Use username: admin, password: admin123",
        }
    }
    openapi_schema["security"] = [{"httpBasic": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Paths that do not require authentication (docs so users can open /docs and use Authorize)
NO_AUTH_PATHS = {"/docs", "/redoc", "/openapi.json", "/"}


# ----- Authentication Middleware (all routes protected except docs) -----
@app.middleware("http")
async def auth_middleware(request, call_next):
    if request.url.path in NO_AUTH_PATHS:
        response = await call_next(request)
        return response
    user = validate_credentials(request)
    if user is None:
        return JSONResponse(
            status_code=401,
            content={
                "detail": "Unauthorized",
                "message": "All API endpoints require Basic Auth. Use username 'admin' / password 'admin123'. Open /docs to explore.",
            },
        )
    request.state.user = user
    response = await call_next(request)
    return response


@app.get("/")
def root():
    """Welcome message. Requires Basic Auth."""
    return {
        "message": "Library API",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


# ----- Books -----
@app.get("/books", response_model=list[BookResponse])
def list_books(
    db: Session = Depends(get_db),
    author_id: Optional[int] = None,
    category_id: Optional[int] = None,
    publication_year: Optional[int] = None,
    sort: Optional[str] = Query(None, description="title or year"),
    limit: Optional[int] = Query(None, ge=1, le=100),
):
    """List books with optional filters and limit. Sort by title (A-Z) or year."""
    q = db.query(Book).options(
        joinedload(Book.authors),
        joinedload(Book.category),
    )
    if author_id is not None:
        q = q.join(Book.authors).filter(Author.id == author_id)
    if category_id is not None:
        q = q.filter(Book.category_id == category_id)
    if publication_year is not None:
        q = q.filter(Book.publication_year == publication_year)
    if sort == "title":
        q = q.order_by(Book.title.asc())
    elif sort == "year":
        q = q.order_by(Book.publication_year.asc().nullslast())
    if limit is not None:
        q = q.limit(limit)
    books = q.distinct().all()
    return [_book_to_response(b) for b in books]


@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    b = db.query(Book).options(
        joinedload(Book.authors),
        joinedload(Book.category),
    ).filter(Book.id == book_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Book not found")
    return _book_to_response(b)


@app.post("/books", response_model=BookResponse)
def create_book(body: BookCreate, db: Session = Depends(get_db)):
    authors = db.query(Author).filter(Author.id.in_(body.author_ids or [])).all()
    if (body.author_ids or []) and len(authors) != len(body.author_ids or []):
        raise HTTPException(status_code=400, detail="One or more author IDs not found")
    category = None
    if body.category_id is not None:
        category = db.query(Category).filter(Category.id == body.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    if body.isbn and db.query(Book).filter(Book.isbn == body.isbn).first():
        raise HTTPException(status_code=400, detail="ISBN already exists")
    book = Book(
        title=body.title,
        isbn=body.isbn,
        publication_year=body.publication_year,
        category_id=body.category_id,
    )
    db.add(book)
    db.flush()
    for a in authors:
        book.authors.append(a)
    db.commit()
    db.refresh(book)
    return _book_to_response(book)


@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, body: BookUpdate, db: Session = Depends(get_db)):
    book = db.query(Book).options(
        joinedload(Book.authors),
        joinedload(Book.category),
    ).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if body.title is not None:
        book.title = body.title
    if body.isbn is not None:
        existing = db.query(Book).filter(Book.isbn == body.isbn, Book.id != book_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="ISBN already exists")
        book.isbn = body.isbn
    if body.publication_year is not None:
        book.publication_year = body.publication_year
    if body.category_id is not None:
        cat = db.query(Category).filter(Category.id == body.category_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        book.category_id = body.category_id
    if body.author_ids is not None:
        book.authors.clear()
        authors = db.query(Author).filter(Author.id.in_(body.author_ids)).all()
        if len(authors) != len(body.author_ids):
            raise HTTPException(status_code=400, detail="One or more author IDs not found")
        for a in authors:
            book.authors.append(a)
    db.commit()
    db.refresh(book)
    return _book_to_response(book)


@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return {"detail": "Deleted"}


def _book_to_response(b: Book) -> BookResponse:
    return BookResponse(
        id=b.id,
        title=b.title,
        isbn=b.isbn,
        publication_year=b.publication_year,
        category_id=b.category_id,
        category=CategoryRef(id=c.id, name=c.name) if (c := b.category) else None,
        authors=[AuthorRef(id=a.id, name=a.name) for a in b.authors],
    )


# ----- Authors -----
@app.get("/authors", response_model=list[AuthorResponse])
def list_authors(
    db: Session = Depends(get_db),
    sort: Optional[str] = Query(None, description="name"),
    limit: Optional[int] = Query(None, ge=1, le=100),
):
    """List authors. Sort by name (A-Z)."""
    q = db.query(Author)
    if sort == "name":
        q = q.order_by(Author.name.asc())
    if limit is not None:
        q = q.limit(limit)
    return q.all()


@app.get("/authors/{author_id}", response_model=AuthorResponse)
def get_author(author_id: int, db: Session = Depends(get_db)):
    a = db.query(Author).filter(Author.id == author_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Author not found")
    return a


@app.get("/authors/{author_id}/books", response_model=list[BookResponse])
def list_books_by_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    books = db.query(Book).options(
        joinedload(Book.authors),
        joinedload(Book.category),
    ).join(Book.authors).filter(Author.id == author_id).all()
    return [_book_to_response(b) for b in books]


@app.post("/authors", response_model=AuthorResponse)
def create_author(body: AuthorCreate, db: Session = Depends(get_db)):
    author = Author(name=body.name)
    db.add(author)
    db.commit()
    db.refresh(author)
    return author


@app.put("/authors/{author_id}", response_model=AuthorResponse)
def update_author(author_id: int, body: AuthorUpdate, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    if body.name is not None:
        author.name = body.name
    db.commit()
    db.refresh(author)
    return author


@app.delete("/authors/{author_id}")
def delete_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    db.delete(author)
    db.commit()
    return {"detail": "Deleted"}


# ----- Categories -----
@app.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@app.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    c = db.query(Category).filter(Category.id == category_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    return c


@app.get("/categories/{category_id}/books", response_model=list[BookResponse])
def list_books_by_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    books = db.query(Book).options(
        joinedload(Book.authors),
        joinedload(Book.category),
    ).filter(Book.category_id == category_id).all()
    return [_book_to_response(b) for b in books]


@app.post("/categories", response_model=CategoryResponse)
def create_category(body: CategoryCreate, db: Session = Depends(get_db)):
    if db.query(Category).filter(Category.name == body.name).first():
        raise HTTPException(status_code=400, detail="Category name already exists")
    cat = Category(name=body.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
    return {"detail": "Deleted"}


# ----- Stats & Checks (at least 4) -----
@app.get("/stats/books/count")
def stats_books_count(db: Session = Depends(get_db)):
    """How many books do we have in the library?"""
    count = db.query(func.count(Book.id)).scalar() or 0
    return {"count": count}


@app.get("/stats/books/average-publication-year")
def stats_average_publication_year(db: Session = Depends(get_db)):
    """Average publication year. Zero or clear message if no books."""
    result = db.query(func.avg(Book.publication_year)).filter(
        Book.publication_year.isnot(None),
    ).scalar()
    if result is None:
        total = db.query(func.count(Book.id)).scalar() or 0
        if total == 0:
            return {"average_publication_year": None, "message": "No books in the library."}
        return {"average_publication_year": None, "message": "No books with publication year."}
    return {"average_publication_year": round(result, 2)}


@app.get("/stats/authors/{author_id}/earliest-latest-books")
def stats_author_earliest_latest(author_id: int, db: Session = Depends(get_db)):
    """Earliest and latest book (by publication year) for a given author."""
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    sub = db.query(Book).join(Book.authors).filter(Author.id == author_id).filter(
        Book.publication_year.isnot(None),
    )
    earliest = sub.order_by(Book.publication_year.asc()).first()
    latest = sub.order_by(Book.publication_year.desc()).first()
    return {
        "author_id": author_id,
        "author_name": author.name,
        "earliest_book": {"id": earliest.id, "title": earliest.title, "publication_year": earliest.publication_year} if earliest else None,
        "latest_book": {"id": latest.id, "title": latest.title, "publication_year": latest.publication_year} if latest else None,
    }


@app.get("/stats/categories/{category_id}/all-books-have-year")
def stats_category_all_books_have_year(category_id: int, db: Session = Depends(get_db)):
    """Do all books in a category have a publication year?"""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    total = db.query(func.count(Book.id)).filter(Book.category_id == category_id).scalar() or 0
    with_year = db.query(func.count(Book.id)).filter(
        Book.category_id == category_id,
        Book.publication_year.isnot(None),
    ).scalar() or 0
    return {
        "category_id": category_id,
        "category_name": cat.name,
        "all_books_have_publication_year": total > 0 and total == with_year,
        "total_books": total,
        "books_with_year": with_year,
    }


@app.get("/stats/author-has-books/{author_id}")
def stats_author_has_books(author_id: int, db: Session = Depends(get_db)):
    """Do we have at least one book from this author? Yes/no."""
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    count = db.query(func.count(Book.id)).join(Book.authors).filter(Author.id == author_id).scalar() or 0
    return {"author_id": author_id, "has_books": count >= 1}


@app.get("/stats/category-has-books/{category_id}")
def stats_category_has_books(category_id: int, db: Session = Depends(get_db)):
    """Do we have at least one book in this category? Yes/no."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    count = db.query(func.count(Book.id)).filter(Book.category_id == category_id).scalar() or 0
    return {"category_id": category_id, "has_books": count >= 1}


@app.get("/stats/books-per-author")
def stats_books_per_author(db: Session = Depends(get_db)):
    """How many books does each author have? Author name + count."""
    rows = (
        db.query(Author.name, func.count(Book.id).label("count"))
        .outerjoin(book_author, Author.id == book_author.c.author_id)
        .outerjoin(Book, book_author.c.book_id == Book.id)
        .group_by(Author.id, Author.name)
    )
    return {"books_per_author": [{"author_name": r.name, "count": r.count} for r in rows]}


@app.get("/stats/books-per-category")
def stats_books_per_category(db: Session = Depends(get_db)):
    """How many books per category? Category name + count."""
    rows = (
        db.query(Category.name, func.count(Book.id).label("count"))
        .outerjoin(Book, Category.id == Book.category_id)
        .group_by(Category.id, Category.name)
    )
    return {"books_per_category": [{"category_name": r.name, "count": r.count} for r in rows]}


@app.get("/stats/authors/sorted-by-earliest")
def stats_authors_sorted_earliest(db: Session = Depends(get_db)):
    """List of author names sorted by earliest publication year first."""
    rows = (
        db.query(Author.id, Author.name, func.min(Book.publication_year).label("min_year"))
        .join(book_author, Author.id == book_author.c.author_id)
        .join(Book, book_author.c.book_id == Book.id)
        .filter(Book.publication_year.isnot(None))
        .group_by(Author.id, Author.name)
        .all()
    )
    # Authors with no books: add with null year at end
    with_year = {r.id: (r.name, r.min_year) for r in rows}
    all_authors = db.query(Author).all()
    result = []
    for r in rows:
        result.append({"author_name": r.name, "earliest_publication_year": r.min_year})
    for a in all_authors:
        if a.id not in with_year:
            result.append({"author_name": a.name, "earliest_publication_year": None})
    result.sort(key=lambda x: (x["earliest_publication_year"] or 9999, x["author_name"]))
    return {"authors": result}


# ----- Bonus: Insights report -----
@app.get("/books/insights")
def books_insights(db: Session = Depends(get_db)):
    """
    Insights report: load books, filter valid (non-empty author, year 1900-2100),
    top 5 authors by count, busy years (>=2 books) with book titles.
    """
    books = db.query(Book).options(
        joinedload(Book.authors),
        joinedload(Book.category),
    ).all()
    if not books:
        return {"top_authors": [], "busy_years": []}

    valid_books = []
    for b in books:
        if not b.authors:
            continue
        if b.publication_year is None or not (1900 <= b.publication_year <= 2100):
            continue
        valid_books.append(b)

    # Top 5 authors by book count
    author_count = {}
    for b in valid_books:
        for a in b.authors:
            author_count[a.name] = author_count.get(a.name, 0) + 1
    top_authors = sorted(
        [{"name": name, "book_count": c} for name, c in author_count.items()],
        key=lambda x: -x["book_count"],
    )[:5]

    # Busy years: year -> list of book titles
    year_books = {}
    for b in valid_books:
        y = b.publication_year
        if y not in year_books:
            year_books[y] = []
        year_books[y].append(b.title)
    busy_years = [
        {"year": year, "books": titles}
        for year, titles in sorted(year_books.items())
        if len(titles) >= 2
    ]

    return {"top_authors": top_authors, "busy_years": busy_years}


# ----- Health (optional) -----
@app.get("/health")
def health():
    return {"status": "ok"}

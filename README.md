# Library API – FastAPI + SQLite

A runnable FastAPI application for a library system using SQLite and SQLAlchemy ORM.

## Tech Stack

- **Framework:** FastAPI
- **Server:** Uvicorn
- **Database:** SQLite (`library.db`)
- **ORM:** SQLAlchemy
- **Validation:** Pydantic

## Database Design

- **authors** – id, name, created_at
- **categories** – id, name (e.g. Fiction, Non-Fiction, Reference)
- **books** – id, title, isbn, publication_year, category_id (FK), created_at
- **book_author** – association table (book_id, author_id) for many-to-many between books and authors

Tables and schema are created automatically on application startup via `Base.metadata.create_all(bind=engine)`.

## How to Run

1. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the application:**
   ```bash
   uvicorn main:app --reload
   ```

4. **Database:** On first run, `library.db` is created in the project directory and all tables are created. No separate migration or init step is required.

5. **API docs:** Open http://127.0.0.1:8000/docs for Swagger UI.

## Authentication

All routes are protected by HTTP middleware. Every request must include valid credentials.

- **Method:** Basic Auth
- **Header:** `Authorization: Basic <base64(username:password)>`
- **Valid credentials (for testing):** `admin` / `admin123` or `user` / `password`
- **Invalid/missing credentials:** Response is `401 Unauthorized` with `{"detail": "Unauthorized"}`

Example with curl:
```bash
curl -u admin:admin123 http://127.0.0.1:8000/books
```

## API Endpoints

### Books
- `GET /books` – List books (optional: `author_id`, `category_id`, `publication_year`, `sort=title|year`, `limit`)
- `GET /books/{book_id}` – Get one book (404 if not found)
- `POST /books` – Create book (body: title, isbn?, publication_year?, category_id?, author_ids?)
- `PUT /books/{book_id}` – Update book (404 if not found)
- `DELETE /books/{book_id}` – Delete book (404 if not found)

### Authors
- `GET /authors` – List authors (optional: `sort=name`, `limit`)
- `GET /authors/{author_id}` – Get one author (404 if not found)
- `GET /authors/{author_id}/books` – List books by author (404 if author not found)
- `POST /authors` – Create author
- `PUT /authors/{author_id}` – Update author (404 if not found)
- `DELETE /authors/{author_id}` – Delete author (404 if not found)

### Categories
- `GET /categories` – List categories
- `GET /categories/{category_id}` – Get one category (404 if not found)
- `GET /categories/{category_id}/books` – List books by category (404 if not found)
- `POST /categories` – Create category
- `DELETE /categories/{category_id}` – Delete category (404 if not found)

### Stats & Checks
- `GET /stats/books/count` – Total number of books
- `GET /stats/books/average-publication-year` – Average publication year (handles no books / no years)
- `GET /stats/authors/{author_id}/earliest-latest-books` – Earliest and latest book by year for an author
- `GET /stats/categories/{category_id}/all-books-have-year` – Whether all books in category have a publication year
- `GET /stats/author-has-books/{author_id}` – Yes/no: at least one book from author
- `GET /stats/category-has-books/{category_id}` – Yes/no: at least one book in category
- `GET /stats/books-per-author` – List author name + book count
- `GET /stats/books-per-category` – List category name + book count
- `GET /stats/authors/sorted-by-earliest` – Author names sorted by earliest publication year

First N books by title or N authors by name: use `GET /books?sort=title&limit=N` and `GET /authors?sort=name&limit=N`.

### Bonus
- `GET /books/insights` – Report: top 5 authors by book count, and “busy years” (years with ≥2 books) with book titles.

## 404 Handling

Endpoints that fetch a single resource by ID return `404 Not Found` with a descriptive `detail` when the resource does not exist (e.g. book, author, category).

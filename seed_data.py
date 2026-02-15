"""Seed the database with example authors, categories, and books."""
import sys
from database import SessionLocal
from models import Author, Category, Book


def seed():
    db = SessionLocal()
    try:
        if db.query(Book).first():
            print("Data already exists. Skipping seed.")
            return
        categories = [
            Category(name="Fiction"),
            Category(name="Non-Fiction"),
            Category(name="Reference"),
        ]
        for c in categories:
            db.add(c)
        db.flush()
        authors = [
            Author(name="Jane Austen"),
            Author(name="Agatha Christie"),
            Author(name="George Orwell"),
            Author(name="J.K. Rowling"),
            Author(name="Charles Dickens"),
        ]
        for a in authors:
            db.add(a)
        db.flush()
        books_data = [
            ("Pride and Prejudice", "978-0141439518", 1813, 1, [1]),
            ("Sense and Sensibility", "978-0141439662", 1811, 1, [1]),
            ("Murder on the Orient Express", "978-0062693662", 1934, 1, [2]),
            ("1984", "978-0451524935", 1949, 1, [3]),
            ("Animal Farm", "978-0451526342", 1945, 1, [3]),
            ("Harry Potter and the Philosopher's Stone", "978-0747532699", 1997, 1, [4]),
            ("A Tale of Two Cities", "978-0141439600", 1859, 1, [5]),
            ("Python Programming Guide", "978-0131111111", 2020, 2, []),
            ("World Atlas", None, 2022, 3, []),
        ]
        for title, isbn, year, cat_id, author_ids in books_data:
            book = Book(title=title, isbn=isbn, publication_year=year, category_id=cat_id)
            db.add(book)
            db.flush()
            for aid in author_ids:
                author = db.get(Author, aid)
                if author:
                    book.authors.append(author)
        db.commit()
        print("Seed complete: added categories, authors, and books.")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

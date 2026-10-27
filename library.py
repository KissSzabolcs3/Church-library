"""Core logic for the Church Library app.

All data is stored in a local SQLite database. This module has no
user interface: it only contains the rules (add a book, lend it, return it, ...).
The command-line menu in main.py uses these functions.
"""

import sqlite3
from datetime import date, timedelta
from typing import Optional

DEFAULT_LOAN_DAYS = 28


class LibraryError(Exception):
    """Raised when an action is not allowed (e.g. book already on loan)."""


class Library:
    def __init__(self, db_path: str = "library.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS books (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT NOT NULL,
                author    TEXT NOT NULL,
                category  TEXT NOT NULL DEFAULT '',
                isbn      TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS members (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                name   TEXT NOT NULL,
                phone  TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS loans (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id       INTEGER NOT NULL REFERENCES books(id),
                member_id     INTEGER NOT NULL REFERENCES members(id),
                loan_date     TEXT NOT NULL,
                due_date      TEXT NOT NULL,
                return_date   TEXT
            );
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------ books
    def add_book(self, title: str, author: str, category: str = "", isbn: str = "") -> int:
        title, author = title.strip(), author.strip()
        if not title or not author:
            raise LibraryError("Title and author are required.")
        cur = self.conn.execute(
            "INSERT INTO books (title, author, category, isbn) VALUES (?, ?, ?, ?)",
            (title, author, category.strip(), isbn.strip()),
        )
        self.conn.commit()
        return cur.lastrowid

    def remove_book(self, book_id: int) -> None:
        self._get_book(book_id)
        if self.is_on_loan(book_id):
            raise LibraryError("This book is currently on loan and cannot be removed.")
        self.conn.execute("DELETE FROM loans WHERE book_id = ?", (book_id,))
        self.conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.conn.commit()

    def search_books(self, query: str = "") -> list[sqlite3.Row]:
        """Search by title, author, category or ISBN. Empty query lists all books."""
        like = f"%{query.strip()}%"
        return self.conn.execute(
            """
            SELECT b.*,
                   EXISTS (SELECT 1 FROM loans l
                           WHERE l.book_id = b.id AND l.return_date IS NULL) AS on_loan
            FROM books b
            WHERE b.title LIKE ? OR b.author LIKE ? OR b.category LIKE ? OR b.isbn LIKE ?
            ORDER BY b.title COLLATE NOCASE
            """,
            (like, like, like, like),
        ).fetchall()

    def is_on_loan(self, book_id: int) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM loans WHERE book_id = ? AND return_date IS NULL", (book_id,)
        ).fetchone()
        return row is not None

    def _get_book(self, book_id: int) -> sqlite3.Row:
        row = self.conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if row is None:
            raise LibraryError(f"No book with ID {book_id}.")
        return row

    # ---------------------------------------------------------------- members
    def add_member(self, name: str, phone: str = "") -> int:
        name = name.strip()
        if not name:
            raise LibraryError("Member name is required.")
        cur = self.conn.execute(
            "INSERT INTO members (name, phone) VALUES (?, ?)", (name, phone.strip())
        )
        self.conn.commit()
        return cur.lastrowid

    def list_members(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM members ORDER BY name COLLATE NOCASE"
        ).fetchall()

    def _get_member(self, member_id: int) -> sqlite3.Row:
        row = self.conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
        if row is None:
            raise LibraryError(f"No member with ID {member_id}.")
        return row

    # round-trip helper used by the menu
    def get_member(self, member_id: int) -> sqlite3.Row:
        return self._get_member(member_id)

    def get_book(self, book_id: int) -> sqlite3.Row:
        return self._get_book(book_id)

    # ------------------------------------------------------------------ loans
    def lend_book(
        self,
        book_id: int,
        member_id: int,
        loan_days: int = DEFAULT_LOAN_DAYS,
        today: Optional[date] = None,
    ) -> date:
        """Lend a book to a member. Returns the due date."""
        self._get_book(book_id)
        self._get_member(member_id)
        if self.is_on_loan(book_id):
            raise LibraryError("This book is already on loan.")
        if loan_days < 1:
            raise LibraryError("Loan period must be at least 1 day.")
        today = today or date.today()
        due = today + timedelta(days=loan_days)
        self.conn.execute(
            "INSERT INTO loans (book_id, member_id, loan_date, due_date) VALUES (?, ?, ?, ?)",
            (book_id, member_id, today.isoformat(), due.isoformat()),
        )
        self.conn.commit()
        return due

    def return_book(self, book_id: int, today: Optional[date] = None) -> bool:
        """Mark a book as returned. Returns True if it was overdue."""
        self._get_book(book_id)
        loan = self.conn.execute(
            "SELECT * FROM loans WHERE book_id = ? AND return_date IS NULL", (book_id,)
        ).fetchone()
        if loan is None:
            raise LibraryError("This book is not currently on loan.")
        today = today or date.today()
        self.conn.execute(
            "UPDATE loans SET return_date = ? WHERE id = ?", (today.isoformat(), loan["id"])
        )
        self.conn.commit()
        return today > date.fromisoformat(loan["due_date"])

    def current_loans(self, today: Optional[date] = None) -> list[dict]:
        """All books that are out right now, with an 'overdue' flag."""
        today = today or date.today()
        rows = self.conn.execute(
            """
            SELECT l.book_id, b.title, b.author, m.name AS member, m.phone,
                   l.loan_date, l.due_date
            FROM loans l
            JOIN books b ON b.id = l.book_id
            JOIN members m ON m.id = l.member_id
            WHERE l.return_date IS NULL
            ORDER BY l.due_date
            """
        ).fetchall()
        result = []
        for r in rows:
            item = dict(r)
            item["overdue"] = date.fromisoformat(r["due_date"]) < today
            result.append(item)
        return result

    def member_history(self, member_id: int) -> list[sqlite3.Row]:
        self._get_member(member_id)
        return self.conn.execute(
            """
            SELECT b.title, b.author, l.loan_date, l.due_date, l.return_date
            FROM loans l JOIN books b ON b.id = l.book_id
            WHERE l.member_id = ?
            ORDER BY l.loan_date DESC
            """,
            (member_id,),
        ).fetchall()

    def close(self) -> None:
        self.conn.close()

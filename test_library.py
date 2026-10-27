import unittest
from datetime import date

from library import Library, LibraryError


class LibraryTests(unittest.TestCase):
    def setUp(self):
        # ":memory:" creates a temporary database that disappears after each test
        self.lib = Library(":memory:")
        self.book = self.lib.add_book("Mere Christianity", "C.S. Lewis", "Faith")
        self.member = self.lib.add_member("Anna Kovacs", "0700 000 000")

    def tearDown(self):
        self.lib.close()

    def test_add_book_requires_title_and_author(self):
        with self.assertRaises(LibraryError):
            self.lib.add_book("", "Someone")

    def test_search_finds_by_author(self):
        results = self.lib.search_books("lewis")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Mere Christianity")

    def test_lend_and_return(self):
        due = self.lib.lend_book(self.book, self.member, 14, today=date(2026, 1, 1))
        self.assertEqual(due, date(2026, 1, 15))
        self.assertTrue(self.lib.is_on_loan(self.book))
        overdue = self.lib.return_book(self.book, today=date(2026, 1, 10))
        self.assertFalse(overdue)
        self.assertFalse(self.lib.is_on_loan(self.book))

    def test_cannot_lend_twice(self):
        self.lib.lend_book(self.book, self.member)
        with self.assertRaises(LibraryError):
            self.lib.lend_book(self.book, self.member)

    def test_overdue_detection(self):
        self.lib.lend_book(self.book, self.member, 7, today=date(2026, 1, 1))
        loans = self.lib.current_loans(today=date(2026, 2, 1))
        self.assertTrue(loans[0]["overdue"])
        self.assertTrue(self.lib.return_book(self.book, today=date(2026, 2, 1)))

    def test_cannot_return_book_not_on_loan(self):
        with self.assertRaises(LibraryError):
            self.lib.return_book(self.book)

    def test_cannot_remove_book_on_loan(self):
        self.lib.lend_book(self.book, self.member)
        with self.assertRaises(LibraryError):
            self.lib.remove_book(self.book)

    def test_member_history(self):
        self.lib.lend_book(self.book, self.member, today=date(2026, 1, 1))
        self.lib.return_book(self.book, today=date(2026, 1, 5))
        history = self.lib.member_history(self.member)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["return_date"], "2026-01-05")


if __name__ == "__main__":
    unittest.main()

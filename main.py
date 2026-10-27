"""Command-line menu for the Church Library app.

Run with:  python main.py
"""

from library import Library, LibraryError, DEFAULT_LOAN_DAYS

MENU = """
=== Church Library ===
1) Add a book
2) Search / list books
3) Remove a book
4) Add a member
5) List members
6) Lend a book
7) Return a book
8) Show current loans
9) Show a member's loan history
0) Quit
"""


def ask(prompt: str) -> str:
    return input(prompt).strip()


def ask_int(prompt: str) -> int:
    while True:
        value = ask(prompt)
        if value.isdigit():
            return int(value)
        print("Please enter a number.")


def show_books(books) -> None:
    if not books:
        print("No books found.")
        return
    print(f"{'ID':<5}{'Title':<35}{'Author':<25}{'Category':<15}Status")
    for b in books:
        status = "ON LOAN" if b["on_loan"] else "available"
        print(f"{b['id']:<5}{b['title'][:33]:<35}{b['author'][:23]:<25}{b['category'][:13]:<15}{status}")


def add_book(lib: Library) -> None:
    book_id = lib.add_book(
        ask("Title: "), ask("Author: "), ask("Category (optional): "), ask("ISBN (optional): ")
    )
    print(f"Book added with ID {book_id}.")


def search_books(lib: Library) -> None:
    show_books(lib.search_books(ask("Search (leave empty to list all): ")))


def remove_book(lib: Library) -> None:
    book_id = ask_int("Book ID to remove: ")
    book = lib.get_book(book_id)
    if ask(f"Remove '{book['title']}'? (y/n): ").lower() == "y":
        lib.remove_book(book_id)
        print("Book removed.")


def add_member(lib: Library) -> None:
    member_id = lib.add_member(ask("Name: "), ask("Phone (optional): "))
    print(f"Member added with ID {member_id}.")


def list_members(lib: Library) -> None:
    members = lib.list_members()
    if not members:
        print("No members yet.")
    for m in members:
        print(f"{m['id']:<5}{m['name']:<30}{m['phone']}")


def lend_book(lib: Library) -> None:
    book_id = ask_int("Book ID: ")
    member_id = ask_int("Member ID: ")
    days_text = ask(f"Loan period in days (default {DEFAULT_LOAN_DAYS}): ")
    days = int(days_text) if days_text.isdigit() else DEFAULT_LOAN_DAYS
    due = lib.lend_book(book_id, member_id, days)
    print(f"Book lent. Due back on {due.isoformat()}.")


def return_book(lib: Library) -> None:
    overdue = lib.return_book(ask_int("Book ID: "))
    print("Book returned (it was overdue)." if overdue else "Book returned. Thank you!")


def show_loans(lib: Library) -> None:
    loans = lib.current_loans()
    if not loans:
        print("No books are on loan.")
        return
    for loan in loans:
        flag = "  <-- OVERDUE" if loan["overdue"] else ""
        print(
            f"[{loan['book_id']}] {loan['title']} -> {loan['member']} "
            f"({loan['phone'] or 'no phone'}), due {loan['due_date']}{flag}"
        )


def show_history(lib: Library) -> None:
    history = lib.member_history(ask_int("Member ID: "))
    if not history:
        print("No loans yet.")
    for h in history:
        returned = h["return_date"] or "not returned yet"
        print(f"{h['title']} by {h['author']} | lent {h['loan_date']} | returned: {returned}")


ACTIONS = {
    "1": add_book,
    "2": search_books,
    "3": remove_book,
    "4": add_member,
    "5": list_members,
    "6": lend_book,
    "7": return_book,
    "8": show_loans,
    "9": show_history,
}


def main() -> None:
    lib = Library()
    try:
        while True:
            print(MENU)
            choice = ask("Choose an option: ")
            if choice == "0":
                print("Goodbye!")
                break
            action = ACTIONS.get(choice)
            if action is None:
                print("Unknown option.")
                continue
            try:
                action(lib)
            except LibraryError as error:
                print(f"Error: {error}")
    finally:
        lib.close()


if __name__ == "__main__":
    main()

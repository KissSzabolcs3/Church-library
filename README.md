# Church Library

A simple command-line app for managing a church community's book library:
register books, register members, lend books and track returns and overdue loans.

Built with **Python 3.9+** and **SQLite**. No external packages needed.

## Features

* Add, search and remove books (search by title, author, category or ISBN)
* Register community members (name and optional phone number)
* Lend a book to a member with a due date (default: 28 days)
* Return a book and see whether it was overdue
* List all current loans, with overdue loans highlighted
* View the loan history of each member
* Rules enforced automatically: a book can't be lent twice, can't be removed while on loan, and can't be returned if it isn't out

## Getting started

```bash
git clone https://github.com/KissSzabolcs3/church-library.git
cd church-library
python main.py
```

The first run creates a `library.db` file next to the program. This file holds all your data, so back it up from time to time. It is excluded from Git via `.gitignore`.

## How to use it

When you start the program, a numbered menu appears:

```
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
```

Type the number and press Enter. The program then asks for the details it needs.

**Example workflow**

1. Choose `1` and add a book. The program shows its ID, for example `1`.
2. Choose `4` and add a member. The program shows their ID, for example `1`.
3. Choose `6`, enter book ID `1` and member ID `1`. The program shows the due date.
4. Choose `8` to see who has which book and what is overdue.
5. When the book comes back, choose `7` and enter the book ID.

## Project structure

|File|Purpose|
|-|-|
|`library.py`|Core logic and database access (no user interface)|
|`main.py`|Interactive command-line menu|
|`test\_library.py`|Automated tests|
|`library.db`|Created on first run; your data (not in Git)|

### How it works

* `library.py` contains one class, `Library`. It creates three SQLite tables:

  * `books`: title, author, category, ISBN
  * `members`: name, phone
  * `loans`: which book, which member, loan date, due date, return date
* A loan with an empty `return\_date` means the book is currently out.
* Business rules live in `Library` and raise a `LibraryError` with a clear message when an action is not allowed. The menu in `main.py` catches these errors and shows them to the user.
* Keeping logic and interface separate makes the code easy to test and easy to extend later (for example with a web interface).

## Running the tests

```bash
python -m unittest -v
```

The tests use a temporary in-memory database, so they never touch your real data.

## Ideas for future improvements

* Export the book list or loans to CSV
* Reminder list of overdue loans for each member
* Web interface (e.g. Flask)
* Multiple copies of the same book

## License

MIT. Free to use and modify.


# Library-Management-System

A simple, yet effective, library management system that runs entirely in the command line. This application allows users to manage a collection of books, track issued books, and handle returns without the need for a database or external dependencies beyond the `pandas` library.

  

## Demonstration

Here's a quick look at the application's main menu and how to interact with it:

```
📚 Library Management System 📚
---------------------------------
1. View All Books
2. Add New Book
3. Issue Book
4. Return Book
5. View Issued Books
6. Delete Book
7. Exit
---------------------------------
Enter your choice (1-7): 1

--- Complete Library Catalog ---
  Book ID                  Title               Author Status
     B001       The Great Gatsby  F. Scott Fitzgerald    YES
     B002  To Kill a Mockingbird           Harper Lee    YES
     B003                   1984        George Orwell     NO
     B004    Pride and Prejudice          Jane Austen    YES
     B005  The Catcher in the Rye        J.D. Salinger     NO

Press Enter to return to the menu...
```

-----

## ✨ Features

  * **View All Books**: Displays a complete list of all books in the library, including their ID, title, author, and availability status.
  * **Add New Book**: Easily add new books to the library collection.
  * **Issue Book**: Track which books are loaned out to which students.
  * **Return Book**: Process the return of an issued book, making it available again.
  * **View Issued Books**: Get a quick overview of all books currently checked out.
  * **Delete Book**: Remove books from the library collection.
  * **In-Memory Data**: Uses Pandas DataFrames to manage data, meaning no database setup is required. The data persists as long as the application is running.

-----

## 🚀 Getting Started

### Prerequisites

Make sure you have Python 3.6 or newer installed on your system. You will also need the `pandas` library. You can install it using pip:

```bash
pip install pandas
```

### Running the Application

1.  Save the code as a Python file (e.g., `library_cli.py`).
2.  Open your terminal or command prompt.
3.  Navigate to the directory where you saved the file.
4.  Run the application with the following command:

<!-- end list -->

```bash
python library_cli.py
```

-----

## 📖 How to Use

Once the application is running, you will see a menu with the following options:

1.  **View All Books**: Shows a table of all books.
2.  **Add New Book**: Prompts you to enter the ID, title, and author for a new book.
3.  **Issue Book**: Asks for the Book ID and the name of the student who is borrowing it.
4.  **Return Book**: Asks for the Book ID of the book being returned.
5.  **View Issued Books**: Shows a table of all books currently on loan.
6.  **Delete Book**: Prompts you for the ID of the book you wish to remove permanently.
7.  **Exit**: Closes the application.

Simply type the number corresponding to your choice and press `Enter` to proceed.

-----

## 🤝 Contributing

Contributions are welcome\! If you have ideas for improvements or find a bug, feel free to open an issue or submit a pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

-----

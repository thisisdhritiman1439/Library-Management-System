import pandas as pd
import os

# ------------------------------------------------------------------------------------------------
# In-Memory "Database" Initialization
# ------------------------------------------------------------------------------------------------
# Using global variables to act as our in-memory database.
initial_books = {
    'Book ID': ['B001', 'B002', 'B003', 'B004', 'B005'],
    'Title': ['The Great Gatsby', 'To Kill a Mockingbird', '1984', 'Pride and Prejudice', 'The Catcher in the Rye'],
    'Author': ['F. Scott Fitzgerald', 'Harper Lee', 'George Orwell', 'Jane Austen', 'J.D. Salinger'],
    'Status': ['YES', 'YES', 'NO', 'YES', 'NO']  # YES = Available, NO = Issued
}
books_df = pd.DataFrame(initial_books)

initial_issued = {
    'Book ID': ['B003', 'B005'],
    'Title': ['1984', 'The Catcher in the Rye'],
    'Issued To': ['Alice', 'Bob']
}
issued_df = pd.DataFrame(initial_issued)


# ------------------------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------------------------
def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def wait_for_enter():
    """Pauses execution until the user presses Enter."""
    input("\nPress Enter to return to the menu...")


# ------------------------------------------------------------------------------------------------
# Core Library Functions (Operating on Global DataFrames)
# ------------------------------------------------------------------------------------------------
def add_book():
    """Prompts user for book details and adds it to the library."""
    global books_df
    clear_screen()
    print("--- Add a New Book ---")
    bid = input("Enter Book ID (e.g., 'B006'): ")
    
    if bid in books_df['Book ID'].values:
        print(f"\nError: A book with ID '{bid}' already exists.")
        return

    title = input("Enter Book Title: ")
    author = input("Enter Author Name: ")

    new_book = pd.DataFrame({
        'Book ID': [bid], 'Title': [title], 'Author': [author], 'Status': ['YES']
    })
    books_df = pd.concat([books_df, new_book], ignore_index=True)
    print(f"\nSuccess: Book '{title}' added successfully!")


def delete_book():
    """Prompts user for a Book ID and deletes the book."""
    global books_df
    clear_screen()
    print("--- Delete a Book ---")
    bid = input("Enter the Book ID to delete: ")

    if bid in issued_df['Book ID'].values:
        print("\nError: Cannot delete the book. It is currently issued to a student.")
        return

    if bid not in books_df['Book ID'].values:
        print(f"\nError: Book with ID '{bid}' not found.")
        return

    books_df = books_df[books_df['Book ID'] != bid]
    print(f"\nSuccess: Book with ID '{bid}' deleted successfully!")


def issue_book():
    """Prompts user for Book ID and student name to issue a book."""
    global books_df, issued_df
    clear_screen()
    print("--- Issue a Book ---")
    bid = input("Enter Book ID to issue: ")
    
    book_row = books_df[books_df['Book ID'] == bid]
    if book_row.empty:
        print(f"\nError: Book with ID '{bid}' not found.")
        return

    if book_row['Status'].iloc[0] == 'NO':
        title = book_row['Title'].iloc[0]
        print(f"\nError: Book '{title}' is already issued.")
        return

    student_name = input("Enter Student Name: ")
    
    books_df.loc[books_df['Book ID'] == bid, 'Status'] = 'NO'
    
    title = book_row['Title'].iloc[0]
    new_issue = pd.DataFrame({
        'Book ID': [bid], 'Title': [title], 'Issued To': [student_name]
    })
    issued_df = pd.concat([issued_df, new_issue], ignore_index=True)
    print(f"\nSuccess: Book '{title}' issued to {student_name}.")


def return_book():
    """Prompts user for a Book ID to return."""
    global books_df, issued_df
    clear_screen()
    print("--- Return a Book ---")
    bid = input("Enter Book ID to return: ")

    if bid not in issued_df['Book ID'].values:
        print(f"\nError: Book with ID '{bid}' has not been issued or the ID is incorrect.")
        return

    issued_df = issued_df[issued_df['Book ID'] != bid]
    books_df.loc[books_df['Book ID'] == bid, 'Status'] = 'YES'
    print(f"\nSuccess: Book with ID '{bid}' returned successfully!")


def view_all_books():
    """Displays the complete library catalog."""
    clear_screen()
    print("--- Complete Library Catalog ---")
    if books_df.empty:
        print("The library is currently empty.")
    else:
        print(books_df.to_string(index=False))


def view_issued_books():
    """Displays all currently issued books."""
    clear_screen()
    print("--- Currently Issued Books ---")
    if issued_df.empty:
        print("No books are currently issued.")
    else:
        print(issued_df.to_string(index=False))


# ------------------------------------------------------------------------------------------------
# Main Application Loop
# ------------------------------------------------------------------------------------------------
def main():
    """The main function to run the command-line interface."""
    while True:
        clear_screen()
        print("📚 Library Management System 📚")
        print("---------------------------------")
        print("1. View All Books")
        print("2. Add New Book")
        print("3. Issue Book")
        print("4. Return Book")
        print("5. View Issued Books")
        print("6. Delete Book")
        print("7. Exit")
        print("---------------------------------")
        
        choice = input("Enter your choice (1-7): ")

        if choice == '1':
            view_all_books()
            wait_for_enter()
        elif choice == '2':
            add_book()
            wait_for_enter()
        elif choice == '3':
            issue_book()
            wait_for_enter()
        elif choice == '4':
            return_book()
            wait_for_enter()
        elif choice == '5':
            view_issued_books()
            wait_for_enter()
        elif choice == '6':
            delete_book()
            wait_for_enter()
        elif choice == '7':
            print("\nThank you for using the Library Management System. Goodbye!")
            break
        else:
            print("\nInvalid choice. Please enter a number between 1 and 7.")
            wait_for_enter()

if __name__ == "__main__":
    # To run the application, you need pandas: pip install pandas
    main()

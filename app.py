import streamlit as st
import pandas as pd
import os

# ------------------------------------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide", # Use wide layout for better table display
    initial_sidebar_state="auto",
)

# ------------------------------------------------------------------------------------------------
# Function to Load and Prepare Data from JSON
# - This function is cached to improve performance on reloads.
# ------------------------------------------------------------------------------------------------
@st.cache_data
def load_data(file_path="books.json"):
    """Loads book data from a JSON file and prepares it for the app."""
    try:
        df = pd.read_json(file_path)
        # Standardize column names for consistency within the app
        df.rename(columns={
            'bid': 'Book ID',
            'title': 'Title',
            'author': 'Author',
            'category': 'Category',
            'status': 'Status'
        }, inplace=True)
        # Convert status to a more usable format (YES/NO) for internal logic
        df['Status'] = df['Status'].apply(lambda x: 'NO' if x == 'issued' else 'YES')
        return df
    except FileNotFoundError:
        st.error(f"Error: The data file '{file_path}' was not found. Please make sure it's in the same directory as the app.")
        return pd.DataFrame() # Return an empty dataframe on error
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return pd.DataFrame()

# ------------------------------------------------------------------------------------------------
# Session State Initialization
# - This block runs only once per session to set up the in-memory "database".
# ------------------------------------------------------------------------------------------------
if 'books_df' not in st.session_state:
    # Load the main book data from the JSON file
    st.session_state.books_df = load_data()
    
    # Create the initial issued books DataFrame based on the loaded data
    if not st.session_state.books_df.empty:
        issued_books_initial = st.session_state.books_df[st.session_state.books_df['Status'] == 'NO'].copy()
        # Add a placeholder for who the book was issued to initially
        issued_books_initial['Issued To'] = 'Pre-issued' 
        st.session_state.issued_df = issued_books_initial[['Book ID', 'Title', 'Issued To']]
    else:
        # If loading fails, initialize with an empty DataFrame
        st.session_state.issued_df = pd.DataFrame(columns=['Book ID', 'Title', 'Issued To'])


# ------------------------------------------------------------------------------------------------
# Core Library Functions (Operating on Session State)
# ------------------------------------------------------------------------------------------------

def add_book(bid, title, author, category):
    """Adds a new book to the session state DataFrame."""
    if bid in st.session_state.books_df['Book ID'].values:
        st.error(f"Error: A book with ID '{bid}' already exists.")
        return

    new_book = pd.DataFrame({
        'Book ID': [bid], 'Title': [title], 'Author': [author], 'Category': [category], 'Status': ['YES']
    })
    st.session_state.books_df = pd.concat([st.session_state.books_df, new_book], ignore_index=True)
    st.success(f"Book '{title}' added successfully!")

def delete_book(bid):
    """Deletes a book from the session state DataFrame."""
    if bid in st.session_state.issued_df['Book ID'].values:
        st.error("Cannot delete the book. It is currently issued.")
        return

    if bid not in st.session_state.books_df['Book ID'].values:
        st.warning(f"Book with ID '{bid}' not found.")
        return

    st.session_state.books_df = st.session_state.books_df[st.session_state.books_df['Book ID'] != bid]
    st.success(f"Book with ID '{bid}' deleted successfully!")

def issue_book(bid, student_name):
    """Issues a book to a student."""
    book_row = st.session_state.books_df[st.session_state.books_df['Book ID'] == bid]
    if book_row.empty:
        st.error(f"Book with ID '{bid}' not found.")
        return

    if book_row['Status'].iloc[0] == 'NO':
        title = book_row['Title'].iloc[0]
        st.error(f"Book '{title}' is already issued.")
        return

    st.session_state.books_df.loc[st.session_state.books_df['Book ID'] == bid, 'Status'] = 'NO'
    title = book_row['Title'].iloc[0]
    new_issue = pd.DataFrame({'Book ID': [bid], 'Title': [title], 'Issued To': [student_name]})
    st.session_state.issued_df = pd.concat([st.session_state.issued_df, new_issue], ignore_index=True)
    st.success(f"Book '{title}' issued to {student_name}.")

def return_book(bid):
    """Returns a previously issued book."""
    if bid not in st.session_state.issued_df['Book ID'].values:
        st.error(f"Error: Book with ID '{bid}' is not currently issued.")
        return

    st.session_state.issued_df = st.session_state.issued_df[st.session_state.issued_df['Book ID'] != bid]
    st.session_state.books_df.loc[st.session_state.books_df['Book ID'] == bid, 'Status'] = 'YES'
    st.success(f"Book with ID '{bid}' returned successfully!")

# ------------------------------------------------------------------------------------------------
# Streamlit User Interface
# ------------------------------------------------------------------------------------------------
st.title("📚 Library Management System")
st.caption("Powered by Streamlit and Pandas, using your custom JSON dataset.")

st.sidebar.title("Menu")
choice = st.sidebar.radio(
    "Select an option",
    ["View All Books", "Add New Book", "Issue Book", "Return Book", "View Issued Books", "Delete Book"],
    captions=[
        "See the full library catalog.", "Add a new book to the collection.", "Lend a book to a student.",
        "Process a returned book.", "See all currently checked-out books.", "Remove a book from the library."
    ]
)

if choice == "View All Books":
    st.header("Complete Library Catalog")
    st.dataframe(st.session_state.books_df, use_container_width=True)

elif choice == "Add New Book":
    st.header("Add a New Book")
    with st.form("add_form", clear_on_submit=True):
        # Find the max existing ID to suggest the next one
        next_id = st.session_state.books_df['Book ID'].max() + 1
        bid = st.number_input("Book ID", min_value=1, value=next_id, help="Must be a unique ID.")
        title = st.text_input("Book Title")
        author = st.text_input("Author Name")
        category = st.text_input("Category")
        if st.form_submit_button("Add Book"):
            if bid and title and author and category:
                add_book(int(bid), title, author, category)
            else:
                st.warning("Please fill out all fields.")

elif choice == "Issue Book":
    st.header("Issue a Book")
    with st.form("issue_form", clear_on_submit=True):
        available_books = st.session_state.books_df[st.session_state.books_df['Status'] == 'YES']
        if not available_books.empty:
            bid = st.selectbox("Select Book to Issue", options=available_books['Book ID'],
                               format_func=lambda x: f"{x} - {available_books[available_books['Book ID'] == x]['Title'].iloc[0]}")
            student_name = st.text_input("Student Name")
            if st.form_submit_button("Issue Book"):
                if bid and student_name:
                    issue_book(bid, student_name)
                else:
                    st.warning("Please select a book and enter a student name.")
        else:
            st.info("There are no available books to issue.")


elif choice == "Return Book":
    st.header("Return a Book")
    with st.form("return_form", clear_on_submit=True):
        if not st.session_state.issued_df.empty:
            issued_books_ids = st.session_state.issued_df['Book ID'].tolist()
            bid = st.selectbox("Select Book to Return", options=issued_books_ids,
                               format_func=lambda x: f"{x} - {st.session_state.issued_df[st.session_state.issued_df['Book ID'] == x]['Title'].iloc[0]}")
            if st.form_submit_button("Return Book"):
                return_book(bid)
        else:
            st.info("No books are currently issued to be returned.")

elif choice == "View Issued Books":
    st.header("Currently Issued Books")
    if st.session_state.issued_df.empty:
        st.info("No books are currently issued.")
    else:
        st.dataframe(st.session_state.issued_df, use_container_width=True)

elif choice == "Delete Book":
    st.header("Delete a Book")
    st.warning("⚠️ Deleting a book is a permanent action.", icon="🚨")
    with st.form("delete_form", clear_on_submit=True):
        all_book_ids = st.session_state.books_df['Book ID'].tolist()
        bid = st.selectbox("Select Book to Delete", options=all_book_ids,
                           format_func=lambda x: f"{x} - {st.session_state.books_df[st.session_state.books_df['Book ID'] == x]['Title'].iloc[0]}")
        if st.form_submit_button("Delete Book"):
            if bid:
                delete_book(bid)
            else:
                st.warning("Please select a book to delete.")

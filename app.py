import streamlit as st
import pandas as pd
import os
import json

# ---------------------------------------------
# File paths
# ---------------------------------------------
DATA_FILE = "books_data.json"
ISSUE_FILE = "issued_books.csv"

# ---------------------------------------------
# Sample Initial Data
# ---------------------------------------------
SAMPLE_BOOKS = [
    {"bid": "101", "title": "Python Basics", "author": "John Doe", "available": "YES"},
    {"bid": "102", "title": "Data Science", "author": "Jane Smith", "available": "YES"},
]

# ---------------------------------------------
# Load or initialize the dataset from JSON
# ---------------------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
                df = pd.DataFrame(data)
            except Exception:
                df = pd.DataFrame(columns=["bid", "title", "author", "available"])
    else:
        df = pd.DataFrame(SAMPLE_BOOKS)
        save_data(df)
    return df

def save_data(df):
    with open(DATA_FILE, "w") as f:
        json.dump(df.to_dict(orient="records"), f, indent=4)

# ---------------------------------------------
# Load or initialize issued data from CSV
# ---------------------------------------------
def load_issued_data():
    if os.path.exists(ISSUE_FILE):
        try:
            return pd.read_csv(ISSUE_FILE)
        except Exception:
            return pd.DataFrame(columns=["bid", "student"])
    else:
        return pd.DataFrame(columns=["bid", "student"])

def save_issued_data(df):
    df.to_csv(ISSUE_FILE, index=False)

# ---------------------------------------------
# Streamlit App Interface
# ---------------------------------------------
st.set_page_config(page_title="Library Management System", page_icon="📚", layout="wide")
st.title("📚 ProjectGurukul Library Management System")

# Sidebar Menu
menu = st.sidebar.selectbox(
    "Select Action",
    ["View Books", "Add Book", "Delete Book", "Issue Book", "Return Book", "View Issued Books"]
)

# Load data into session
books_df = load_data()
issued_df = load_issued_data()

# ---------------------------------------------
# View Books
# ---------------------------------------------
if menu == "View Books":
    st.header("📖 View All Books")
    if not books_df.empty:
        st.dataframe(books_df)
    else:
        st.info("No books found.")

# ---------------------------------------------
# Add Book
# ---------------------------------------------
elif menu == "Add Book":
    st.header("➕ Add a New Book")
    bid = st.text_input("Enter Book ID")
    title = st.text_input("Enter Title")
    author = st.text_input("Enter Author")
    available = st.selectbox("Available", ["YES", "NO"])

    if st.button("Add Book"):
        if bid and title and author:
            if bid in books_df["bid"].values:
                st.warning("Book with this ID already exists.")
            else:
                new_book = pd.DataFrame([[bid, title, author, available]], columns=["bid", "title", "author", "available"])
                books_df = pd.concat([books_df, new_book], ignore_index=True)
                save_data(books_df)
                st.success("Book added successfully!")
        else:
            st.error("Please fill all fields.")

# ---------------------------------------------
# Delete Book
# ---------------------------------------------
elif menu == "Delete Book":
    st.header("❌ Delete a Book")
    bid = st.text_input("Enter Book ID to delete")

    if st.button("Delete Book"):
        if bid in books_df["bid"].values:
            books_df = books_df[books_df["bid"] != bid]
            save_data(books_df)
            st.success("Book deleted successfully!")
        else:
            st.error("Book with given ID does not exist.")

# ---------------------------------------------
# Issue Book (Dropdown)
# ---------------------------------------------
elif menu == "Issue Book":
    st.header("📤 Issue a Book")

    if "available" not in books_df.columns:
        st.error("❌ 'available' column missing. Please re-add books properly.")
        st.stop()

    available_books = books_df[books_df["available"] == "YES"]

    if available_books.empty:
        st.warning("No books available for issuing.")
    else:
        bid = st.selectbox(
            "Select Book to Issue",
            options=available_books["bid"],
            format_func=lambda x: f"{x} - {available_books[available_books['bid'] == x]['title'].values[0]}"
        )

        student = st.text_input("Enter Student Name")

        if st.button("Issue Book"):
            if student:
                book_index = books_df[books_df["bid"] == bid].index[0]
                books_df.at[book_index, "available"] = "NO"
                save_data(books_df)

                issued_df = pd.concat(
                    [issued_df, pd.DataFrame([[bid, student]], columns=["bid", "student"])],
                    ignore_index=True
                )
                save_issued_data(issued_df)

                st.success(f"Book issued to {student} successfully!")
            else:
                st.warning("Please enter the student name.")

# ---------------------------------------------
# Return Book (Dropdown)
# ---------------------------------------------
elif menu == "Return Book":
    st.header("📥 Return a Book")

    if issued_df.empty:
        st.info("No books currently issued.")
    else:
        bid = st.selectbox(
            "Select Book to Return",
            options=issued_df["bid"],
            format_func=lambda x: f"{x} - {books_df[books_df['bid'] == x]['title'].values[0]}"
        )

        if st.button("Return Book"):
            book_index = books_df[books_df["bid"] == bid].index[0]
            books_df.at[book_index, "available"] = "YES"
            save_data(books_df)

            issued_df = issued_df[issued_df["bid"] != bid]
            save_issued_data(issued_df)

            st.success("Book returned successfully!")

# ---------------------------------------------
# View Issued Books
# ---------------------------------------------
elif menu == "View Issued Books":
    st.header("📋 Issued Books")
    if not issued_df.empty:
        st.dataframe(issued_df)
    else:
        st.info("No books currently issued.")

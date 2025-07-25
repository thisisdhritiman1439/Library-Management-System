import streamlit as st
import pandas as pd
import os
import json

# File path
DATA_FILE = "books_data.json"

# Sample default books
SAMPLE_BOOKS = [
    {"bid": "101", "title": "Python Basics", "author": "John Doe", "available": "YES", "issued_to": ""},
    {"bid": "102", "title": "Data Science", "author": "Jane Smith", "available": "YES", "issued_to": ""}
]

# Initialize or reset book data
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            if "available" not in df.columns or "issued_to" not in df.columns:
                raise ValueError("Missing required columns")
        except:
            df = pd.DataFrame(SAMPLE_BOOKS)
            save_data(df)
    else:
        df = pd.DataFrame(SAMPLE_BOOKS)
        save_data(df)
    return df

def save_data(df):
    with open(DATA_FILE, "w") as f:
        json.dump(df.to_dict(orient="records"), f, indent=4)

# Streamlit UI
st.set_page_config(page_title="Library Management", page_icon="📚", layout="wide")
st.title("📚 Library Management System (JSON-only)")

menu = st.sidebar.radio("Menu", ["View Books", "Add Book", "Delete Book", "Issue Book", "Return Book", "View Issued Books"])
books_df = load_data()

# View all books
if menu == "View Books":
    st.header("📘 All Books")
    st.dataframe(books_df)

# Add a book
elif menu == "Add Book":
    st.header("➕ Add Book")
    bid = st.text_input("Book ID")
    title = st.text_input("Title")
    author = st.text_input("Author")

    if st.button("Add Book"):
        if bid and title and author:
            if bid in books_df["bid"].values:
                st.error("Book ID already exists.")
            else:
                new_book = pd.DataFrame([{
                    "bid": bid,
                    "title": title,
                    "author": author,
                    "available": "YES",
                    "issued_to": ""
                }])
                books_df = pd.concat([books_df, new_book], ignore_index=True)
                save_data(books_df)
                st.success("Book added.")
        else:
            st.warning("Fill all fields.")

# Delete a book
elif menu == "Delete Book":
    st.header("❌ Delete Book")
    bid = st.selectbox("Select Book", options=books_df["bid"])

    if st.button("Delete"):
        books_df = books_df[books_df["bid"] != bid]
        save_data(books_df)
        st.success("Book deleted.")

# Issue a book
elif menu == "Issue Book":
    st.header("📤 Issue Book")
    available_books = books_df[books_df["available"] == "YES"]

    if available_books.empty:
        st.info("No books available.")
    else:
        bid = st.selectbox("Select Book", options=available_books["bid"],
                           format_func=lambda x: f"{x} - {available_books[available_books['bid'] == x]['title'].values[0]}")
        student = st.text_input("Student Name")
        if st.button("Issue Book"):
            idx = books_df[books_df["bid"] == bid].index[0]
            books_df.at[idx, "available"] = "NO"
            books_df.at[idx, "issued_to"] = student
            save_data(books_df)
            st.success(f"Issued to {student}.")

# Return a book
elif menu == "Return Book":
    st.header("📥 Return Book")
    issued_books = books_df[books_df["available"] == "NO"]

    if issued_books.empty:
        st.info("No issued books.")
    else:
        bid = st.selectbox("Select Book to Return", options=issued_books["bid"],
                           format_func=lambda x: f"{x} - {issued_books[issued_books['bid'] == x]['title'].values[0]} (to {issued_books[issued_books['bid'] == x]['issued_to'].values[0]})")
        if st.button("Return Book"):
            idx = books_df[books_df["bid"] == bid].index[0]
            books_df.at[idx, "available"] = "YES"
            books_df.at[idx, "issued_to"] = ""
            save_data(books_df)
            st.success("Book returned.")

# View issued books
elif menu == "View Issued Books":
    st.header("📋 Issued Books")
    issued_books = books_df[books_df["available"] == "NO"]
    if issued_books.empty:
        st.info("No books currently issued.")
    else:
        st.dataframe(issued_books[["bid", "title", "author", "issued_to"]])

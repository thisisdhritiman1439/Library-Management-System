import streamlit as st
import pandas as pd
import os
import json

# -----------------------------
# File path
# -----------------------------
DATA_FILE = "books_data.json"

# -----------------------------
# Load books data
# -----------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        # Ensure 'issued_to' exists
        if "issued_to" not in df.columns:
            df["issued_to"] = ""
    else:
        df = pd.DataFrame(columns=["bid", "title", "author", "category", "status", "issued_to"])
    return df

# -----------------------------
# Save books data
# -----------------------------
def save_data(df):
    with open(DATA_FILE, "w") as f:
        json.dump(df.to_dict(orient="records"), f, indent=4)

# -----------------------------
# App UI
# -----------------------------
st.set_page_config(page_title="Library System", page_icon="📚", layout="wide")
st.title("📚 Library Management System (JSON Only)")

menu = st.sidebar.radio("Menu", ["View Books", "Add Book", "Delete Book", "Issue Book", "Return Book", "View Issued Books"])
books_df = load_data()

# View all books
if menu == "View Books":
    st.header("📘 All Books")
    st.dataframe(books_df)

# Add book
elif menu == "Add Book":
    st.header("➕ Add Book")
    bid = st.number_input("Book ID", min_value=1, step=1)
    title = st.text_input("Title")
    author = st.text_input("Author")
    category = st.text_input("Category")

    if st.button("Add Book"):
        if bid and title and author and category:
            if bid in books_df["bid"].values:
                st.error("Book ID already exists.")
            else:
                new_book = pd.DataFrame([{
                    "bid": bid,
                    "title": title,
                    "author": author,
                    "category": category,
                    "status": "available",
                    "issued_to": ""
                }])
                books_df = pd.concat([books_df, new_book], ignore_index=True)
                save_data(books_df)
                st.success("Book added.")
        else:
            st.warning("Fill all fields.")

# Delete book
elif menu == "Delete Book":
    st.header("❌ Delete Book")
    bid = st.selectbox("Select Book ID to Delete", options=books_df["bid"])

    if st.button("Delete"):
        books_df = books_df[books_df["bid"] != bid]
        save_data(books_df)
        st.success("Book deleted.")

# Issue book
elif menu == "Issue Book":
    st.header("📤 Issue Book")

    available_books = books_df[books_df["status"] == "available"]

    if available_books.empty:
        st.info("No books available.")
    else:
        bid = st.selectbox(
            "Select Book",
            options=available_books["bid"],
            format_func=lambda x: f"{x} - {available_books[available_books['bid'] == x]['title'].values[0]}"
        )
        student = st.text_input("Student Name")

        if st.button("Issue Book"):
            idx = books_df[books_df["bid"] == bid].index[0]
            books_df.at[idx, "status"] = "issued"
            books_df.at[idx, "issued_to"] = student
            save_data(books_df)
            st.success(f"Issued to {student}.")

# Return book
elif menu == "Return Book":
    st.header("📥 Return Book")
    issued_books = books_df[books_df["status"] == "issued"]

    if issued_books.empty:
        st.info("No issued books.")
    else:
        bid = st.selectbox(
            "Select Book",
            options=issued_books["bid"],
            format_func=lambda x: f"{x} - {issued_books[issued_books['bid'] == x]['title'].values[0]} (to {issued_books[issued_books['bid'] == x]['issued_to'].values[0]})"
        )

        if st.button("Return Book"):
            idx = books_df[books_df["bid"] == bid].index[0]
            books_df.at[idx, "status"] = "available"
            books_df.at[idx, "issued_to"] = ""
            save_data(books_df)
            st.success("Book returned.")

# View issued books
elif menu == "View Issued Books":
    st.header("📋 Issued Books")
    issued = books_df[books_df["status"] == "issued"]
    if issued.empty:
        st.info("No books are issued.")
    else:
        st.dataframe(issued[["bid", "title", "author", "category", "issued_to"]])

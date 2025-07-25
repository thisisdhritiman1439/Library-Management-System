import streamlit as st
import pandas as pd
import os
import json
import datetime
import hashlib

# ----------------------
# File Paths
# ----------------------
BOOKS_FILE = "books_data.json"
USERS_FILE = "users.json"

# ----------------------
# Load/Save Books
# ----------------------
def load_books():
    if os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        for col in ["issued_to", "issue_date", "due_date"]:
            if col not in df.columns:
                df[col] = ""
    else:
        df = pd.DataFrame(columns=["bid", "title", "author", "category", "status", "issued_to", "issue_date", "due_date"])
    return df

def save_books(df):
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, indent=4, ensure_ascii=False)

# ----------------------
# Load/Save Users
# ----------------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    else:
        return []

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

# ----------------------
# Password Hashing
# ----------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ----------------------
# Authentication
# ----------------------
def login(username, password):
    users = load_users()
    hashed = hash_password(password)
    for user in users:
        if user["username"] == username and user["password"] == hashed:
            return user["role"]
    return None

def signup(username, password, role):
    users = load_users()
    for user in users:
        if user["username"] == username:
            return False  # User exists
    users.append({
        "username": username,
        "password": hash_password(password),
        "role": role
    })
    save_users(users)
    return True

# ----------------------
# Streamlit App
# ----------------------
st.set_page_config(page_title="Library System", page_icon="📚", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

if not st.session_state.logged_in:
    with st.container():
        st.markdown("""
            <h1 style='text-align: center; color: #4CAF50;'>📚 Library Management System</h1>
            <h4 style='text-align: center;'>Login as Student or Librarian</h4>
            <hr>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔐 Login")
            login_username = st.text_input("Username", key="login_user")
            login_password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login"):
                role = login(login_username, login_password)
                if role:
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.session_state.role = role
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

        with col2:
            st.subheader("📝 Sign Up")
            signup_username = st.text_input("New Username", key="signup_user")
            signup_password = st.text_input("New Password", type="password", key="signup_pass")
            role = st.selectbox("Role", ["student", "admin"])
            if st.button("Sign Up"):
                if signup(signup_username, signup_password, role):
                    st.success("Account created. Please log in.")
                else:
                    st.warning("Username already exists.")

# ----------------------
# Main Dashboard
# ----------------------
if st.session_state.logged_in:
    books_df = load_books()

    menu_options = ["View Books", "Issue Book", "Return Book", "View Issued Books", "Logout"]
    if st.session_state.role == "admin":
        menu_options = ["View Books", "Add Book", "Delete Book", "Issue Book", "Return Book", "View Issued Books", "Logout"]

    menu = st.sidebar.radio("Menu", menu_options)

    if menu == "View Books":
        st.header("📘 All Books")
        st.dataframe(books_df)

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
                    new_book = pd.DataFrame([{ "bid": bid, "title": title, "author": author, "category": category, "status": "available", "issued_to": "", "issue_date": "", "due_date": "" }])
                    books_df = pd.concat([books_df, new_book], ignore_index=True)
                    save_books(books_df)
                    st.success("Book added.")

    elif menu == "Delete Book":
        st.header("❌ Delete Book")
        bid = st.selectbox("Select Book ID", books_df["bid"])
        if st.button("Delete"):
            books_df = books_df[books_df["bid"] != bid]
            save_books(books_df)
            st.success("Book deleted.")

    elif menu == "Issue Book":
        st.header("📤 Issue Book")
        available_books = books_df[books_df["status"] == "available"]
        if available_books.empty:
            st.info("No books available.")
        else:
            bid = st.selectbox("Select Book", available_books["bid"], format_func=lambda x: f"{x} - {available_books[available_books['bid'] == x]['title'].values[0]}")
            student = st.session_state.username if st.session_state.role == "student" else st.text_input("Student Name")
            if st.button("Issue Book"):
                idx = books_df[books_df["bid"] == bid].index[0]
                today = datetime.date.today()
                due = today + datetime.timedelta(days=7)
                books_df.at[idx, "status"] = "issued"
                books_df.at[idx, "issued_to"] = student
                books_df.at[idx, "issue_date"] = str(today)
                books_df.at[idx, "due_date"] = str(due)
                save_books(books_df)
                st.success(f"Book issued to {student} (Due: {due})")

    elif menu == "Return Book":
        st.header("📥 Return Book")
        if st.session_state.role == "admin":
            issued_books = books_df[books_df["status"] == "issued"]
        else:
            issued_books = books_df[(books_df["status"] == "issued") & (books_df["issued_to"] == st.session_state.username)]

        if issued_books.empty:
            st.info("No issued books.")
        else:
            bid = st.selectbox("Select Book to Return", issued_books["bid"], format_func=lambda x: f"{x} - {issued_books[issued_books['bid'] == x]['title'].values[0]}")
            if st.button("Return Book"):
                idx = books_df[books_df["bid"] == bid].index[0]
                today = datetime.date.today()
                due_date = datetime.date.fromisoformat(books_df.at[idx, "due_date"])
                fine = max(0, (today - due_date).days * 5)
                books_df.at[idx, "status"] = "available"
                books_df.at[idx, "issued_to"] = ""
                books_df.at[idx, "issue_date"] = ""
                books_df.at[idx, "due_date"] = ""
                save_books(books_df)
                if fine > 0:
                    st.warning(f"Returned late! Fine: ₹{fine}")
                else:
                    st.success("Book returned on time.")

    elif menu == "View Issued Books":
        st.header("📋 Issued Books")
        if st.session_state.role == "admin":
            issued = books_df[books_df["status"] == "issued"]
        else:
            issued = books_df[(books_df["status"] == "issued") & (books_df["issued_to"] == st.session_state.username)]

        if issued.empty:
            st.info("No books issued.")
        else:
            st.dataframe(issued[["bid", "title", "author", "category", "issued_to", "issue_date", "due_date"]])

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.success("Logged out.")
        st.rerun()

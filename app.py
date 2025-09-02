import streamlit as st
import json
import os
import datetime

# =============================
# File Paths
# =============================
BOOKS_FILE = "books_data.json"
USERS_FILE = "users_data.json"
ISSUED_FILE = "issued_books.json"

# =============================
# Helper Functions
# =============================
def load_data(file, default_data):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default_data

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# Load Data
books = load_data(BOOKS_FILE, [])
users = load_data(USERS_FILE, [])
issued_books = load_data(ISSUED_FILE, [])

# =============================
# Authentication System
# =============================
def signup():
    st.subheader("Create Account")
    name = st.text_input("Full Name")
    mobile = st.text_input("Mobile Number")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Account Type", ["User", "Librarian"])

    if st.button("Sign Up"):
        if any(u["email"] == email for u in users):
            st.error("Email already exists!")
        else:
            users.append({"name": name, "mobile": mobile, "email": email, "password": password, "role": role, "favorites": []})
            save_data(USERS_FILE, users)
            st.success("Account created successfully! Please login.")

def login():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = next((u for u in users if u["email"] == email and u["password"] == password), None)
        if user:
            st.session_state["user"] = user
            st.session_state["logged_in"] = True
            st.success(f"Welcome {user['name']}! You are logged in as {user['role']}.")
        else:
            st.error("Invalid email or password")

# =============================
# Features
# =============================

def view_all_books():
    st.subheader("📚 All Books")
    for book in books:
        with st.container():
            st.image(book["cover_url"], width=100)
            st.write(f"**{book['title']}** by {book['author']}")
            st.write(book["description"])
            st.write("**Genre:**", book["genre"])
            st.write("**Available:**", "✅ Yes" if book["available"] else "❌ No")
            with st.expander("📖 View Index"):
                st.write("\n".join(book["index"]))

            if st.session_state["user"]["role"] == "User":
                if st.button(f"Add to Favorites {book['id']}"):
                    user = st.session_state["user"]
                    for u in users:
                        if u["email"] == user["email"]:
                            if book["id"] not in u["favorites"]:
                                u["favorites"].append(book["id"])
                                save_data(USERS_FILE, users)
                                st.success("Added to your favorites!")
                            else:
                                st.warning("Already in favorites!")


def view_favorites():
    st.subheader("⭐ Your Favorite Books")
    user = st.session_state["user"]
    fav_books = [book for book in books if book["id"] in user["favorites"]]
    for book in fav_books:
        st.write(f"**{book['title']}** by {book['author']}")

        if book["available"] and st.button(f"Issue {book['id']}"):
            issue_date = datetime.date.today()
            due_date = issue_date + datetime.timedelta(days=14)
            issued_books.append({"user_email": user["email"], "book_id": book["id"], "issue_date": str(issue_date), "due_date": str(due_date), "returned": False})
            save_data(ISSUED_FILE, issued_books)
            for b in books:
                if b["id"] == book["id"]:
                    b["available"] = False
            save_data(BOOKS_FILE, books)
            st.success(f"Book issued successfully! Due date: {due_date}")


def view_issued_books():
    st.subheader("📕 Your Issued Books")
    user = st.session_state["user"]
    today = datetime.date.today()
    user_issued = [ib for ib in issued_books if ib["user_email"] == user["email"] and not ib["returned"]]

    for ib in user_issued:
        book = next((b for b in books if b["id"] == ib["book_id"]), None)
        if book:
            st.write(f"**{book['title']}**")
            st.write(f"Issue Date: {ib['issue_date']} | Due Date: {ib['due_date']}")
            due_date = datetime.date.fromisoformat(ib["due_date"])
            fine = max((today - due_date).days * 10, 0) if today > due_date else 0
            st.write(f"Fine: ₹{fine}")

            if st.button(f"Return {book['id']}"):
                ib["returned"] = True
                book["available"] = True
                save_data(ISSUED_FILE, issued_books)
                save_data(BOOKS_FILE, books)
                st.success("Book returned successfully!")


def librarian_panel():
    st.subheader("📘 Librarian Panel")
    option = st.radio("Choose Action", ["Add Book", "Delete Book"])

    if option == "Add Book":
        title = st.text_input("Book Title")
        author = st.text_input("Author")
        cover_url = st.text_input("Cover Image URL")
        description = st.text_area("Description")
        genre = st.text_input("Genre")
        index = st.text_area("Index (comma separated)").split(",")
        
        if st.button("Add Book"):
            new_id = max([b["id"] for b in books], default=0) + 1
            books.append({"id": new_id, "title": title, "author": author, "cover_url": cover_url, "description": description, "index": index, "genre": genre, "available": True})
            save_data(BOOKS_FILE, books)
            st.success("Book added successfully!")

    elif option == "Delete Book":
        book_id = st.number_input("Enter Book ID to delete", min_value=1, step=1)
        if st.button("Delete Book"):
            global books
            books = [b for b in books if b["id"] != book_id]
            save_data(BOOKS_FILE, books)
            st.success("Book deleted successfully!")

# =============================
# Main App
# =============================

def main():
    st.title("📖 Library Management System")

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        menu = ["Login", "Sign Up"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Login":
            login()
        elif choice == "Sign Up":
            signup()
    else:
        user = st.session_state["user"]
        st.sidebar.write(f"👤 Logged in as {user['name']} ({user['role']})")

        if user["role"] == "User":
            action = st.sidebar.radio("Navigate", ["All Books", "Favorites", "Issued Books"])
            if action == "All Books":
                view_all_books()
            elif action == "Favorites":
                view_favorites()
            elif action == "Issued Books":
                view_issued_books()

        elif user["role"] == "Librarian":
            action = st.sidebar.radio("Navigate", ["All Books", "Librarian Panel"])
            if action == "All Books":
                view_all_books()
            elif action == "Librarian Panel":
                librarian_panel()

        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.success("Logged out successfully!")

if __name__ == "__main__":
    main()

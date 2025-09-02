import streamlit as st
import json
import os
import datetime

# ---------------------------
# File Paths
# ---------------------------
USERS_FILE = "users.json"
BOOKS_FILE = "books_data.json"

# ---------------------------
# Utility Functions
# ---------------------------
def load_json(file_path, default_data):
    """Load JSON data from file or return default."""
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        return default_data
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    """Save JSON data to file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# Load data
users = load_json(USERS_FILE, [])
books = load_json(BOOKS_FILE, [])

# ---------------------------
# User Management
# ---------------------------
def signup(username, password, role="user"):
    for user in users:
        if user["username"] == username:
            return False, "⚠ Username already exists!"
    users.append({
        "username": username,
        "password": password,
        "role": role,
        "favorites": [],
        "issued_books": []
    })
    save_json(USERS_FILE, users)
    return True, "✅ Account created successfully!"

def login(username, password):
    for user in users:
        if user["username"] == username and user["password"] == password:
            return True, user
    return False, None

# ---------------------------
# Book Management
# ---------------------------
def add_book(title, author, cover_url, description, genre):
    new_id = max([b["id"] for b in books], default=0) + 1
    new_book = {
        "id": new_id,
        "title": title,
        "author": author,
        "cover_url": cover_url,
        "description": description,
        "genre": genre,
        "available": True
    }
    books.append(new_book)
    save_json(BOOKS_FILE, books)

def delete_book(book_id):
    global books
    books = [b for b in books if b["id"] != book_id]
    save_json(BOOKS_FILE, books)

# ---------------------------
# Book Issuing System
# ---------------------------
def issue_book(user, book_id):
    for book in books:
        if book["id"] == book_id and book["available"]:
            book["available"] = False
            due_date = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
            user["issued_books"].append({
                "id": book_id,
                "title": book["title"],
                "due_date": due_date
            })
            save_json(USERS_FILE, users)
            save_json(BOOKS_FILE, books)
            return f"✅ Book issued! Due date: {due_date}"
    return "⚠ Book not available."

def return_book(user, book_id):
    for book in books:
        if book["id"] == book_id:
            book["available"] = True
            user["issued_books"] = [b for b in user["issued_books"] if b["id"] != book_id]
            save_json(USERS_FILE, users)
            save_json(BOOKS_FILE, books)
            return "✅ Book returned successfully!"
    return "⚠ Error returning book."

def calculate_fine(due_date):
    today = datetime.date.today()
    due = datetime.date.fromisoformat(due_date)
    days_late = (today - due).days
    return max(0, days_late * 10)  # ₹10 per late day

# ---------------------------
# Favorites
# ---------------------------
def toggle_favorite(user, book_id):
    if book_id in user["favorites"]:
        user["favorites"].remove(book_id)
    else:
        user["favorites"].append(book_id)
    save_json(USERS_FILE, users)

# ---------------------------
# AI Recommender
# ---------------------------
def recommend_books(query):
    query = query.lower()
    results = []
    for book in books:
        if query in book["title"].lower() or query in book["author"].lower() or query in book["genre"].lower():
            results.append(book)
    return results

# ---------------------------
# UI Components
# ---------------------------
def book_card(book, user=None):
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(book["cover_url"], width=120)
    with col2:
        st.subheader(book["title"])
        st.write(f"👨‍💻 Author: {book['author']}")
        st.write(f"📚 Genre: {book['genre']}")
        st.caption(book["description"])
        st.write("✅ Available" if book["available"] else "❌ Not Available")

        if user:
            if user["role"] == "user":
                if book["available"]:
                    if st.button(f"Issue: {book['title']}", key=f"issue_{book['id']}"):
                        st.success(issue_book(user, book["id"]))
                else:
                    st.write("⚠ Already issued.")
                if book["id"] in user["favorites"]:
                    if st.button(f"Unfavorite: {book['title']}", key=f"fav_{book['id']}"):
                        toggle_favorite(user, book["id"])
                else:
                    if st.button(f"Favorite: {book['title']}", key=f"fav_{book['id']}"):
                        toggle_favorite(user, book["id"])


# ---------------------------
# Main App
# ---------------------------
def app():
    st.set_page_config(page_title="📚 Library Management System", layout="wide")

    if "user" not in st.session_state:
        st.session_state.user = None

    st.title("📚 Library Management System")

    # Authentication
    if not st.session_state.user:
        choice = st.sidebar.radio("Menu", ["Login", "Signup"])
        if choice == "Signup":
            st.subheader("Create Account")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["user", "librarian"])
            if st.button("Signup"):
                success, msg = signup(username, password, role)
                st.info(msg)

        elif choice == "Login":
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                success, user = login(username, password)
                if success:
                    st.session_state.user = user
                    st.experimental_rerun()
                else:
                    st.error("❌ Invalid credentials")

    else:
        user = st.session_state.user
        st.sidebar.success(f"👋 Welcome, {user['username']} ({user['role']})")
        page = st.sidebar.radio("Navigate", ["All Books", "My Issued Books", "Favorites", "Search Books", "AI Recommender"])

        if user["role"] == "librarian":
            page = st.sidebar.radio("Librarian Tools", ["Add Book", "Delete Book"], index=0)

        if page == "All Books":
            st.subheader("📚 All Books")
            for book in books:
                book_card(book, user)

        elif page == "My Issued Books":
            st.subheader("📖 My Issued Books")
            for b in user["issued_books"]:
                fine = calculate_fine(b["due_date"])
                st.write(f"📘 {b['title']} | Due: {b['due_date']} | Fine: ₹{fine}")
                if st.button(f"Return: {b['title']}", key=f"return_{b['id']}"):
                    st.success(return_book(user, b["id"]))

        elif page == "Favorites":
            st.subheader("⭐ My Favorite Books")
            fav_books = [b for b in books if b["id"] in user["favorites"]]
            for book in fav_books:
                book_card(book, user)

        elif page == "Search Books":
            st.subheader("🔍 Search & Filter Books")
            query = st.text_input("Enter title, author, or genre")
            if query:
                results = recommend_books(query)
                if results:
                    for book in results:
                        book_card(book, user)
                else:
                    st.warning("No books found.")

        elif page == "AI Recommender":
            st.subheader("🤖 AI Book Recommender")
            query = st.text_input("Ask me for a book recommendation")
            if query:
                results = recommend_books(query)
                if results:
                    st.success(f"Found {len(results)} recommendations!")
                    for book in results:
                        book_card(book, user)
                else:
                    st.error("No matching books found.")

        elif page == "Add Book" and user["role"] == "librarian":
            st.subheader("➕ Add Book")
            title = st.text_input("Title")
            author = st.text_input("Author")
            cover_url = st.text_input("Cover Image URL")
            description = st.text_area("Description")
            genre = st.text_input("Genre")
            if st.button("Add"):
                add_book(title, author, cover_url, description, genre)
                st.success("✅ Book added successfully!")

        elif page == "Delete Book" and user["role"] == "librarian":
            st.subheader("🗑 Delete Book")
            book_id = st.number_input("Book ID", min_value=1)
            if st.button("Delete"):
                delete_book(book_id)
                st.success("✅ Book deleted!")

        if st.sidebar.button("🚪 Logout"):
            st.session_state.user = None
            st.experimental_rerun()


if __name__ == "__main__":
    app()

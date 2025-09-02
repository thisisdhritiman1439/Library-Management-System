import streamlit as st
import json
import os
import hashlib

USER_FILE = "users.json"
BOOK_FILE = "books.json"

# ------------------ Utility Functions ------------------
def load_users():
    if not os.path.exists(USER_FILE):
        return []
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def find_user(email, password=None):
    users = load_users()
    for user in users:
        if user["email"] == email:
            if password:
                return user if user["password"] == hash_password(password) else None
            return user
    return None

# ------------------ Authentication UI ------------------
def authentication_ui():
    st.title("📚 Library Management System")
    st.markdown("### Welcome! Please Login or Signup to continue.")

    tab_login, tab_signup = st.tabs(["🔑 Login", "🆕 Signup"])

    # ------------------ Login ------------------
    with tab_login:
        st.subheader("Login to your account")
        email = st.text_input("📧 Email", key="login_email")
        password = st.text_input("🔒 Password", type="password", key="login_password")

        if st.button("Login", type="primary"):
            user = find_user(email, password)
            if user:
                st.session_state["authenticated"] = True
                st.session_state["user"] = user
                st.success(f"✅ Logged in as {user['name']} ({user['role']})")
                st.rerun()
            else:
                st.error("❌ Invalid email or password")

    # ------------------ Signup ------------------
    with tab_signup:
        st.subheader("Create a new account")
        name = st.text_input("👤 Full Name", key="signup_name")
        mobile = st.text_input("📱 Mobile Number", key="signup_mobile")
        email = st.text_input("📧 Email", key="signup_email")
        password = st.text_input("🔒 Password", type="password", key="signup_password")
        role = st.selectbox("🎭 Role", ["User", "Librarian"], key="signup_role")

        if st.button("Signup", type="primary"):
            if find_user(email):
                st.warning("⚠️ Email already registered. Try logging in.")
            else:
                users = load_users()
                users.append({
                    "name": name,
                    "mobile": mobile,
                    "email": email,
                    "password": hash_password(password),
                    "role": role
                })
                save_users(users)
                st.success("🎉 Account created successfully! Please login now.")

# ------------------ Dashboard after Login ------------------
def dashboard():
    user = st.session_state["user"]

    # Sidebar Profile Section
    with st.sidebar:
        st.success(f"👋 Welcome, {user['name']} ({user['role']})")
        st.write("📧", user["email"])
        st.write("📱", user["mobile"])

        if st.button("🚪 Logout"):
            st.session_state["authenticated"] = False
            st.session_state.pop("user", None)
            st.rerun()

    # Role-based Dashboard
    if user["role"] == "Librarian":
        st.title("📖 Librarian Dashboard")
        st.write("Here you can manage books, view issued books, and more.")
    else:
        st.title("📗 User Dashboard")
        st.write("Browse, issue, and view your favorite books here.")

# ------------------ Main App ------------------
def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        authentication_ui()
    else:
        dashboard()

if __name__ == "__main__":
    main()

def load_books():
    """Load all books from JSON file."""
    if not os.path.exists(BOOK_FILE):
        return []
    try:
        with open(BOOK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_books(books):
    """Save books into JSON file."""
    with open(BOOK_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, indent=4, ensure_ascii=False)

def add_book(title, author, genre, description, cover_url, index):
    """Add a new book with full details."""
    books = load_books()
    new_book = {
        "id": len(books) + 1,
        "title": title,
        "author": author,
        "genre": genre,
        "description": description,
        "cover_url": cover_url,
        "index": index,
        "available": True
    }
    books.append(new_book)
    save_books(books)
    return new_book

def delete_book(book_id):
    """Delete book by ID."""
    books = load_books()
    updated_books = [b for b in books if b["id"] != book_id]
    save_books(updated_books)
    return len(books) != len(updated_books)

def update_book(book_id, updated_data):
    """Update book details by ID."""
    books = load_books()
    for book in books:
        if book["id"] == book_id:
            book.update(updated_data)
            save_books(books)
            return True
    return False

def find_book_by_title(title):
    """Search books by title keyword."""
    books = load_books()
    return [b for b in books if title.lower() in b["title"].lower()]

def find_book_by_genre(genre):
    """Search books by genre."""
    books = load_books()
    return [b for b in books if b["genre"].lower() == genre.lower()]

import streamlit as st
import json
import os
from datetime import datetime

# ================= File Paths =================
USERS_FILE = "users.json"
BOOKS_FILE = "books.json"
ISSUED_FILE = "issued.json"
FAVORITES_FILE = "favorites.json"

# ================= Helpers =================
def load_json(file, default):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        return default
    with open(file, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# Initialize files if not exists
for file, default in [
    (USERS_FILE, []),
    (BOOKS_FILE, []),
    (ISSUED_FILE, []),
    (FAVORITES_FILE, []),
]:
    if not os.path.exists(file):
        save_json(file, default)

# Load data
users = load_json(USERS_FILE, [])
books = load_json(BOOKS_FILE, [])
issued_books = load_json(ISSUED_FILE, [])
favorites = load_json(FAVORITES_FILE, [])

# ================= Authentication =================
def authenticate(username, password):
    for user in users:
        if user["username"] == username and user["password"] == password:
            return True, user["role"]
    return False, None

def register_user(username, password, role="student"):
    for user in users:
        if user["username"] == username:
            return False
    users.append({"username": username, "password": password, "role": role})
    save_json(USERS_FILE, users)
    return True

# ================= Features =================
def view_books():
    st.subheader("📚 All Books")
    for book in books:
        with st.expander(f"{book['title']} by {book['author']}"):
            st.image(book.get("cover", ""), width=120)
            st.write(book["description"])
            st.write(f"**Genre:** {book['genre']}")
            st.write(f"**Available:** {book['available']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"⭐ Favorite - {book['title']}", key=f"fav_{book['id']}"):
                    favorites.append({
                        "username": st.session_state.user,
                        "book_id": book["id"]
                    })
                    save_json(FAVORITES_FILE, favorites)
                    st.success(f"Added {book['title']} to Favorites ✅")
            with col2:
                if book["available"]:
                    if st.button(f"📖 Issue - {book['title']}", key=f"iss_{book['id']}"):
                        st.session_state["confirm_issue"] = book
                else:
                    st.warning("❌ Not Available")

# Confirm issue modal
def confirm_issue_modal():
    if "confirm_issue" in st.session_state and st.session_state["confirm_issue"]:
        book = st.session_state["confirm_issue"]
        st.warning(f"Do you want to issue **{book['title']}** ?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Issue"):
                book["available"] = False
                issued_books.append({
                    "username": st.session_state.user,
                    "book_id": book["id"],
                    "date": str(datetime.now().date())
                })
                save_json(BOOKS_FILE, books)
                save_json(ISSUED_FILE, issued_books)
                st.success(f"Issued {book['title']} successfully ✅")
                st.session_state["confirm_issue"] = None
        with col2:
            if st.button("❌ No"):
                st.session_state["confirm_issue"] = None

def view_issued_books():
    st.subheader("📖 Your Issued Books")
    user_issues = [i for i in issued_books if i["username"] == st.session_state.user]
    for issue in user_issues:
        book = next((b for b in books if b["id"] == issue["book_id"]), None)
        if book:
            st.write(f"- {book['title']} (Issued on {issue['date']})")

def view_favorites():
    st.subheader("⭐ Your Favorite Books")
    user_favs = [f for f in favorites if f["username"] == st.session_state.user]
    for fav in user_favs:
        book = next((b for b in books if b["id"] == fav["book_id"]), None)
        if book:
            st.write(f"- {book['title']} by {book['author']}")

# Chatbot
def chatbot():
    st.subheader("🤖 Chatbot")
    st.write("I can suggest books based on your interest or past favorites/issued books.")
    user_input = st.text_input("Tell me your interest (e.g., mystery, science, love):")
    if user_input:
        suggested = [b for b in books if user_input.lower() in b["genre"].lower()]
        if suggested:
            st.success("Here are some books you may like:")
            for book in suggested:
                st.write(f"- {book['title']} ({book['genre']})")
        else:
            st.warning("No books found for that genre.")
    # Recommend from favorites/issued
    favs = [f["book_id"] for f in favorites if f["username"] == st.session_state.user]
    iss = [i["book_id"] for i in issued_books if i["username"] == st.session_state.user]
    related = [b for b in books if b["id"] in favs + iss]
    if related:
        genres = set(b["genre"] for b in related)
        recs = [b for b in books if b["genre"] in genres and b["id"] not in favs + iss]
        if recs:
            st.info("📌 Recommended for you based on your past activity:")
            for book in recs[:5]:
                st.write(f"- {book['title']} ({book['genre']})")

# Admin add books
def add_book():
    st.subheader("➕ Add a New Book")
    with st.form("add_book_form"):
        title = st.text_input("Title")
        author = st.text_input("Author")
        description = st.text_area("Description")
        genre = st.text_input("Genre")
        cover = st.text_input("Cover Image URL")
        submitted = st.form_submit_button("Add Book")
        if submitted:
            new_id = len(books) + 1
            books.append({
                "id": new_id,
                "title": title,
                "author": author,
                "description": description,
                "genre": genre,
                "cover": cover,
                "available": True
            })
            save_json(BOOKS_FILE, books)
            st.success(f"Book '{title}' added successfully!")

# ================= Main App =================
def app():
    st.title("📚 Library Management System")

    if "user" not in st.session_state:
        menu = st.sidebar.radio("Menu", ["Login", "Register"])
        if menu == "Login":
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                success, role = authenticate(username, password)
                if success:
                    st.session_state.user = username
                    st.session_state.role = role
                    st.success("Logged in successfully!")
                else:
                    st.error("Invalid credentials")
        elif menu == "Register":
            st.subheader("Register")
            username = st.text_input("New Username")
            password = st.text_input("New Password", type="password")
            if st.button("Register"):
                if register_user(username, password):
                    st.success("User registered! Please log in.")
                else:
                    st.error("Username already exists")
    else:
        st.sidebar.write(f"👤 Logged in as: {st.session_state.user} ({st.session_state.role})")
        choice = st.sidebar.radio("Go to", ["All Books", "Issued Books", "Favorites", "Chatbot"])
        if st.session_state.role == "admin":
            if st.sidebar.button("➕ Add Book"):
                add_book()

        if choice == "All Books":
            view_books()
            confirm_issue_modal()
        elif choice == "Issued Books":
            view_issued_books()
        elif choice == "Favorites":
            view_favorites()
        elif choice == "Chatbot":
            chatbot()

        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.success("Logged out successfully!")

if __name__ == "__main__":
    app()

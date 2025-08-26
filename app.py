import streamlit as st
import json
import os
import datetime
import hashlib
import random

# ------------------ Helpers ------------------
USERS_FILE = "users.json"
BOOKS_FILE = "books.json"
ISSUES_FILE = "issues.json"

def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------ Authentication ------------------
def signup(name, mobile, email, password, role):
    users = load_json(USERS_FILE)
    if email in users:
        return False, "User already exists!"
    users[email] = {
        "name": name,
        "mobile": mobile,
        "password": hash_password(password),
        "role": role,
        "favorites": []
    }
    save_json(USERS_FILE, users)
    return True, "Account created successfully!"

def login(email, password):
    users = load_json(USERS_FILE)
    if email in users and users[email]["password"] == hash_password(password):
        return True, users[email]
    return False, None

# ------------------ Books ------------------
def load_books():
    return load_json(BOOKS_FILE)

def save_books(books):
    save_json(BOOKS_FILE, books)

def add_book(book_id, title, author, genre, cover, description, index, available=True):
    books = load_books()
    books[book_id] = {
        "title": title,
        "author": author,
        "genre": genre,
        "cover": cover,
        "description": description,
        "index": index,
        "available": available
    }
    save_books(books)

def delete_book(book_id):
    books = load_books()
    if book_id in books:
        del books[book_id]
        save_books(books)

# ------------------ Issue & Return ------------------
def issue_book(email, book_id):
    issues = load_json(ISSUES_FILE)
    books = load_books()
    if book_id in books and books[book_id]["available"]:
        deadline = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()
        issues.setdefault(email, {})
        issues[email][book_id] = {"issue_date": datetime.date.today().isoformat(), "deadline": deadline}
        books[book_id]["available"] = False
        save_json(ISSUES_FILE, issues)
        save_books(books)
        return True, f"Book issued! Return by {deadline}"
    return False, "Book not available"

def return_book(email, book_id):
    issues = load_json(ISSUES_FILE)
    books = load_books()
    if email in issues and book_id in issues[email]:
        del issues[email][book_id]
        books[book_id]["available"] = True
        save_json(ISSUES_FILE, issues)
        save_books(books)
        return True, "Book returned successfully!"
    return False, "No such issue record."

# ------------------ Recommendation ------------------
def recommend_books(email):
    issues = load_json(ISSUES_FILE)
    books = load_books()
    if email not in issues or not issues[email]:
        return random.sample(list(books.values()), min(5, len(books)))  # random suggestions
    last_book_id = list(issues[email].keys())[-1]
    last_genre = books[last_book_id]["genre"]
    recos = [b for b in books.values() if b["genre"] == last_genre and b["available"]]
    if not recos:
        recos = list(books.values())
    return random.sample(recos, min(5, len(recos)))

# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="Library Management System", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

def login_page():
    st.title("📚 Library Management System")
    menu = st.sidebar.selectbox("Menu", ["Login", "Sign Up"])
    
    if menu == "Login":
        st.subheader("🔑 Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            success, user = login(email, password)
            if success:
                st.session_state.user = {"email": email, **user}
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials.")
    
    elif menu == "Sign Up":
        st.subheader("📝 Create Account")
        name = st.text_input("Name")
        mobile = st.text_input("Mobile")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Student", "Librarian", "Other"])
        if st.button("Sign Up"):
            success, msg = signup(name, mobile, email, password, role)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

def home_page():
    user = st.session_state.user
    st.sidebar.title(f"Welcome, {user['name']} ({user['role']})")
    choice = st.sidebar.radio("Navigate", ["Home", "View All Books", "My Booklist", "Issued Books", "Recommendations"])
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"user": None}) or st.rerun())
    
    books = load_books()

    if choice == "Home":
        st.header("📖 Library Home")
        st.write("Browse and manage your books easily.")

    elif choice == "View All Books":
        st.header("📚 All Books")
        for book_id, book in books.items():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(book["cover"], width=120)
                with cols[1]:
                    st.subheader(book["title"])
                    st.caption(f"by {book['author']} | Genre: {book['genre']}")
                    st.write(book["description"])
                    if st.button("📖 View Index", key=f"idx_{book_id}"):
                        st.info("\n".join(book["index"]))
                    if user["role"] == "Librarian":
                        if st.button("🗑 Delete", key=f"del_{book_id}"):
                            delete_book(book_id)
                            st.rerun()
                    else:
                        if st.button("➕ Add to My Booklist", key=f"fav_{book_id}"):
                            users = load_json(USERS_FILE)
                            users[user["email"]]["favorites"].append(book_id)
                            save_json(USERS_FILE, users)
                            st.success("Book added to your list.")

    elif choice == "My Booklist":
        st.header("❤️ My Booklist")
        users = load_json(USERS_FILE)
        favs = users[user["email"]]["favorites"]
        for bid in favs:
            if bid in books:
                st.write(f"📖 {books[bid]['title']}")
                if st.button("📕 Issue", key=f"issue_{bid}"):
                    success, msg = issue_book(user["email"], bid)
                    st.success(msg) if success else st.error(msg)

    elif choice == "Issued Books":
        st.header("📕 My Issued Books")
        issues = load_json(ISSUES_FILE).get(user["email"], {})
        for bid, info in issues.items():
            if bid in books:
                deadline = datetime.date.fromisoformat(info["deadline"])
                days_left = (deadline - datetime.date.today()).days
                st.write(f"📖 {books[bid]['title']} | Return by: {info['deadline']} ({days_left} days left)")
                if st.button("✅ Return", key=f"ret_{bid}"):
                    success, msg = return_book(user["email"], bid)
                    st.success(msg) if success else st.error(msg)

    elif choice == "Recommendations":
        st.header("✨ Recommended for You")
        recos = recommend_books(user["email"])
        for book in recos:
            st.write(f"📖 {book['title']} ({book['genre']})")

# ------------------ Run App ------------------
if st.session_state.user is None:
    login_page()
else:
    home_page()

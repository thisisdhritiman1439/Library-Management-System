import streamlit as st
import json
import os
import datetime
from difflib import get_close_matches

# ----------------------------
# File paths
# ----------------------------
BOOKS_FILE = "books_data.json"
USERS_FILE = "users.json"
ISSUED_FILE = "issued_books.json"
FAV_FILE = "favorites.json"

# ----------------------------
# Helper functions
# ----------------------------
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# ----------------------------
# Load initial data
# ----------------------------
books = load_json(BOOKS_FILE, [])
users = load_json(USERS_FILE, [])
issued_books = load_json(ISSUED_FILE, {})
favorites = load_json(FAV_FILE, {})

# ----------------------------
# Authentication
# ----------------------------
def signup(name, mobile, email, password, role):
    for u in users:
        if u["email"] == email:
            return False, "Email already registered!"
    users.append({"name": name, "mobile": mobile, "email": email, "password": password, "role": role})
    save_json(USERS_FILE, users)
    return True, "Account created successfully!"

def login(email, password):
    for u in users:
        if u["email"] == email and u["password"] == password:
            return True, u
    return False, None

# ----------------------------
# Book Operations
# ----------------------------
def add_book(title, author, cover_url, description, index, genre):
    book_id = len(books) + 1
    books.append({
        "id": book_id,
        "title": title,
        "author": author,
        "cover_url": cover_url,
        "description": description,
        "index": index.split(","),
        "genre": genre,
        "available": True
    })
    save_json(BOOKS_FILE, books)

def delete_book(book_id):
    global books
    books = [b for b in books if b["id"] != book_id]
    save_json(BOOKS_FILE, books)

def issue_book(user_email, book_id):
    for b in books:
        if b["id"] == book_id and b["available"]:
            b["available"] = False
            due_date = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
            issued_books.setdefault(user_email, []).append({"book_id": book_id, "due_date": due_date})
            save_json(BOOKS_FILE, books)
            save_json(ISSUED_FILE, issued_books)
            return True, due_date
    return False, None

def return_book(user_email, book_id):
    if user_email in issued_books:
        issued_books[user_email] = [i for i in issued_books[user_email] if i["book_id"] != book_id]
        for b in books:
            if b["id"] == book_id:
                b["available"] = True
        save_json(BOOKS_FILE, books)
        save_json(ISSUED_FILE, issued_books)
        return True
    return False

# ----------------------------
# Chatbot & Recommendation
# ----------------------------
def recommend_books(user_email):
    if user_email not in issued_books or not issued_books[user_email]:
        return books[:3]  # return first 3 if no history
    last_book_id = issued_books[user_email][-1]["book_id"]
    last_book = next((b for b in books if b["id"] == last_book_id), None)
    if not last_book:
        return []
    genre = last_book["genre"]
    return [b for b in books if b["genre"] == genre and b["id"] != last_book_id]

def chatbot_response(query):
    query = query.lower()
    if "python" in query:
        return "Best Python books: 'Learning Python', 'Fluent Python', 'Automate the Boring Stuff'."
    elif "issue" in query:
        return "To issue a book, go to 'All Books' → click 'Issue Book'."
    elif "return" in query:
        return "To return a book, check 'Issued Books' section and click 'Return'."
    elif "category" in query:
        return "Categories include: Fiction, Non-Fiction, AI/ML, Data Science, Classics."
    else:
        matches = get_close_matches(query, [b["title"].lower() for b in books], n=1, cutoff=0.6)
        if matches:
            return f"Did you mean '{matches[0].title()}'? It's available in our library!"
        return "I'm not sure, please try asking differently!"

# ----------------------------
# Streamlit App
# ----------------------------
def app():
    st.set_page_config(page_title="📚 Smart Library System", layout="wide")
    st.title("📚 Smart Library Management System")

    if "user" not in st.session_state:
        st.session_state.user = None

    if not st.session_state.user:
        menu = st.sidebar.radio("Menu", ["Login", "Sign Up"])
        if menu == "Login":
            st.subheader("🔑 Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                success, user = login(email, password)
                if success:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        else:
            st.subheader("📝 Sign Up")
            name = st.text_input("Name")
            mobile = st.text_input("Mobile Number")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["User", "Librarian"])
            if st.button("Create Account"):
                success, msg = signup(name, mobile, email, password, role)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
    else:
        user = st.session_state.user
        st.sidebar.success(f"Welcome, {user['name']} ({user['role']})")
        menu = st.sidebar.radio("Navigation", ["All Books", "Issued Books", "Favorites", "Recommendations", "Chatbot", "Add Book (Librarian)", "Delete Book (Librarian)", "Logout"])

        # ---------------- All Books ----------------
        if menu == "All Books":
            st.subheader("📖 All Books")
            for b in books:
                with st.expander(f"{b['title']} by {b['author']}"):
                    st.image(b["cover_url"], width=150)
                    st.write(b["description"])
                    st.write("**Index:**", ", ".join(b["index"]))
                    st.write(f"Genre: {b['genre']}")
                    st.write("Status: ✅ Available" if b["available"] else "❌ Issued")
                    if user["role"] == "User":
                        if st.button(f"Add to Favorites - {b['id']}", key=f"fav{b['id']}"):
                            favorites.setdefault(user["email"], []).append(b["id"])
                            save_json(FAV_FILE, favorites)
                            st.success("Book added to favorites!")
                            st.rerun()
                        if b["available"] and st.button(f"Issue Book - {b['id']}", key=f"issue{b['id']}"):
                            success, due_date = issue_book(user["email"], b["id"])
                            if success:
                                st.success(f"Issued! Return by {due_date}")
                                st.rerun()

        # ---------------- Issued Books ----------------
        elif menu == "Issued Books":
            st.subheader("📦 Your Issued Books")
            if user["email"] in issued_books:
                for entry in issued_books[user["email"]]:
                    b = next((bk for bk in books if bk["id"] == entry["book_id"]), None)
                    if b:
                        due = datetime.date.fromisoformat(entry["due_date"])
                        days_left = (due - datetime.date.today()).days
                        st.write(f"📘 {b['title']} (Due: {due}, {days_left} days left)")
                        if st.button(f"Return {b['title']}", key=f"ret{b['id']}"):
                            return_book(user["email"], b["id"])
                            st.success("Book returned successfully!")
                            st.rerun()
            else:
                st.info("No issued books yet.")

        # ---------------- Favorites ----------------
        elif menu == "Favorites":
            st.subheader("⭐ Favorite Books")
            favs = favorites.get(user["email"], [])
            if favs:
                for fid in favs:
                    b = next((bk for bk in books if bk["id"] == fid), None)
                    if b:
                        st.write(f"📘 {b['title']} by {b['author']}")
            else:
                st.info("No favorites yet.")

        # ---------------- Recommendations ----------------
        elif menu == "Recommendations":
            st.subheader("🤖 Recommended for You")
            recs = recommend_books(user["email"])
            for r in recs:
                st.write(f"📘 {r['title']} ({r['genre']})")

        # ---------------- Chatbot ----------------
        elif menu == "Chatbot":
            st.subheader("💬 AI Librarian Chatbot")
            query = st.text_input("Ask me anything about books/library")
            if st.button("Ask"):
                st.write("🤖", chatbot_response(query))

        # ---------------- Add Book (Librarian) ----------------
        elif menu == "Add Book (Librarian)":
            if user["role"] == "Librarian":
                st.subheader("➕ Add New Book")
                title = st.text_input("Title")
                author = st.text_input("Author")
                cover_url = st.text_input("Cover Image URL")
                desc = st.text_area("Description")
                index = st.text_area("Index (comma separated)")
                genre = st.text_input("Genre")
                if st.button("Add Book"):
                    add_book(title, author, cover_url, desc, index, genre)
                    st.success("Book added successfully!")
                    st.rerun()
            else:
                st.error("Only librarians can add books.")

        # ---------------- Delete Book (Librarian) ----------------
        elif menu == "Delete Book (Librarian)":
            if user["role"] == "Librarian":
                st.subheader("🗑 Delete Book")
                book_id = st.number_input("Enter Book ID", min_value=1, step=1)
                if st.button("Delete"):
                    delete_book(book_id)
                    st.success("Book deleted successfully!")
                    st.rerun()
            else:
                st.error("Only librarians can delete books.")

        # ---------------- Logout ----------------
        elif menu == "Logout":
            st.session_state.user = None
            st.rerun()

if __name__ == "__main__":
    app()

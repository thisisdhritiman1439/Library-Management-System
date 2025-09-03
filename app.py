pip install gspread oauth2client
import streamlit as st
import json
import os
import shutil
import time
import hashlib
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

# -------------------------
# Config & filenames
# -------------------------
BOOKS_FILE = "books_data.json"
USERS_FILE = "users.json"
ISSUED_FILE = "issued_books.json"

FINE_PER_DAY = 10
DEFAULT_LOAN_DAYS = 14
APP_TITLE = "📚 Library Management System"

# -------------------------
# Safe JSON helpers
# -------------------------

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

# Load credentials JSON from the file you downloaded earlier.
# Ensure 'credentials.json' is in the same directory as your app.py,
# or provide the full path to the file.
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

# Authorize gspread with the loaded credentials.
# This creates a client object that can interact with Google Sheets.
client = gspread.authorize(creds)

# Open your Google Sheet.
# Replace "YOUR_SHEET_ID_HERE" with the actual ID of your Google Sheet.
# You can find the Sheet ID in the URL of your Google Sheet (e.g., in
# https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit).
SHEET_ID = "https://docs.google.com/spreadsheets/d/1HMTKp9UITW6-h2M5UCYn3xAGSCKCimhtBvGuXiUm_nU/edit?gid=0#gid=0"
sheet = client.open_by_key(SHEET_ID).sheet1 
def is_strong_password(password: str) -> (bool, str):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must include at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must include at least one special character."
    return True, ""
    
def backup_corrupt_file(path: str):
    try:
        ts = int(time.time())
        bak = f"{path}.corrupt.{ts}"
        shutil.copy(path, bak)
    except Exception:
        pass

def save_json(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(path: str, default):
    if not os.path.exists(path):
        save_json(path, default)
        return default
    try:
        if os.path.getsize(path) == 0:
            save_json(path, default)
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        backup_corrupt_file(path)
        save_json(path, default)
        return default
    except Exception:
        return default

# -------------------------
# Bootstrapping initial data
# -------------------------
def bootstrap_files():
    sample_books = [
        {
            "id": 1,
            "title": "To Kill a Mockingbird",
            "author": "Harper Lee",
            "cover_url": "https://m.media-amazon.com/images/I/81gepf1eMqL.jpg",
            "description": "A classic novel exploring racial injustice and moral growth in the Deep South.",
            "index": ["Chapter 1: Maycomb", "Chapter 2: The Radley Place", "Chapter 3: Atticus’ Advice"],
            "genre": ["Classic Fiction"],
            "keywords": ["justice", "racism", "law"],
            "available": True,
            "added_on": str(date.today() - timedelta(days=40))
        },
        {
            "id": 2,
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "cover_url": "https://images-na.ssl-images-amazon.com/images/I/41xShlnTZTL._SX374_BO1,204,203,200_.jpg",
            "description": "A handbook of agile software craftsmanship.",
            "index": ["Meaningful Names", "Functions", "Formatting", "Objects and Data Structures"],
            "genre": ["Software Engineering"],
            "keywords": ["programming", "best practices", "code"],
            "available": True,
            "added_on": str(date.today() - timedelta(days=30))
        },
        {
            "id": 3,
            "title": "Python Crash Course",
            "author": "Eric Matthes",
            "cover_url": "https://images-na.ssl-images-amazon.com/images/I/51BpsT0LfJL._SX376_BO1,204,203,200_.jpg",
            "description": "A hands-on introduction to programming with Python.",
            "index": ["Getting Started", "Variables", "Loops", "Functions", "Projects"],
            "genre": ["Programming"],
            "keywords": ["python", "beginner", "projects"],
            "available": True,
            "added_on": str(date.today() - timedelta(days=7))
        },
    ]
    sample_users = [
        {
            "name": "Head Librarian",
            "email": "librarian@example.com",
            "mobile": "9999999999",
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "librarian",
            "favorites": []
        },
        {
            "name": "Demo User",
            "email": "user@example.com",
            "mobile": "8888888888",
            "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
            "role": "user",
            "favorites": []
        }
    ]
    sample_issued = []
    load_json(BOOKS_FILE, sample_books)
    load_json(USERS_FILE, sample_users)
    load_json(ISSUED_FILE, sample_issued)

# -------------------------
# Data helpers
# -------------------------
def get_books() -> List[Dict[str,Any]]:
    return load_json(BOOKS_FILE, [])

def save_books(data: List[Dict[str,Any]]):
    save_json(BOOKS_FILE, data)

def get_users():
    records = sheet.get_all_records()
    return records

def save_users(data: List[Dict[str,Any]]):
    save_json(USERS_FILE, data)

def get_issued() -> List[Dict[str,Any]]:
    return load_json(ISSUED_FILE, [])

def save_issued(data: List[Dict[str,Any]]):
    save_json(ISSUED_FILE, data)

# -------------------------
# Auth
# -------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(email, name, password, role="student"):
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Insert into Google Sheet
    sheet.append_row([email, name, password, role, created_at])
    return True, "Account created."

def login_user(email, password):
    users = get_users()
    for user in users:
        if user['email'] == email and user['password'] == password:
            return user
    return None

# -------------------------
# Issue / Return
# -------------------------
def issue_book_to_user(user_email: str, book_id: int, loan_days: int = DEFAULT_LOAN_DAYS) -> (bool,str):
    books = get_books()
    issued = get_issued()
    book = next((b for b in books if b['id'] == book_id), None)
    if not book:
        return False, "Book not found."
    if not book.get('available', True):
        return False, "Book currently not available."

    # set availability + who holds it (optional)
    for b in books:
        if b['id'] == book_id:
            b['available'] = False
            b['issued_to'] = user_email.lower()
    save_books(books)

    today = date.today()
    due = today + timedelta(days=loan_days)
    issued.append({
        "user_email": user_email.lower(),
        "book_id": book_id,
        "issue_date": str(today),
        "due_date": str(due),
        "returned": False,
        "return_date": None
    })
    save_issued(issued)
    return True, f"Issued '{book['title']}'. Due on {due.isoformat()}."


def return_book_from_user(user_email: str, book_id: int) -> (bool,str,int):
    books = get_books()
    issued = get_issued()
    rec = next((r for r in issued if r['user_email'].lower() == user_email.lower() and r['book_id'] == book_id and not r['returned']), None)
    if not rec:
        return False, "No active issue found for this user & book.", 0
    today = date.today()
    due = datetime.fromisoformat(rec['due_date']).date()
    fine = (today - due).days * FINE_PER_DAY if today > due else 0
    rec['returned'] = True
    rec['return_date'] = str(today)
    save_issued(issued)
    for b in books:
        if b['id'] == book_id:
            b['available'] = True
            b.pop('issued_to', None)
    save_books(books)
    return True, "Book returned.", max(0, fine)

def user_active_issues(user_email: str) -> List[Dict[str,Any]]:
    return [r for r in get_issued() if r['user_email'].lower() == user_email.lower() and not r.get('returned', False)]

def calculate_fine_for_record(rec: Dict[str,Any]) -> int:
    due = datetime.fromisoformat(rec['due_date']).date()
    today = date.today()
    return max(0, (today - due).days * FINE_PER_DAY) if today > due else 0

# -------------------------
# Recommendations & Chatbot
# -------------------------
def recommend_for_user(user_email: str, top_k: int = 6) -> List[Dict[str,Any]]:
    books = get_books()
    users = get_users()
    user = next((u for u in users if u['email'].lower() == user_email.lower()), {})
    fav_ids = user.get('favorites', [])
    issued = user_active_issues(user_email)
    genres = set()
    for b in books:
        if b['id'] in fav_ids or any(r['book_id']==b['id'] for r in issued):
            genres.update(b.get('genre',[]))
    def score(b):
        s = 0
        if any(g in b.get('genre',[]) for g in genres):
            s += 2
        if b.get('available', False):
            s += 1
        return s
    ranked = sorted(books, key=score, reverse=True)
    return ranked[:top_k]
def chatbot_response_for_user(user_email: str, message: str) -> str:
    m = message.strip().lower()
    if not m:
        return "Ask me for book recommendations, or how to issue/return books."

    # Book recommendation by user interest keywords
    if "recommend" in m or "suggest" in m:
        keywords = m.replace("recommend","").replace("suggest","").strip().split()
        books = get_books()
        # filter books by keywords in title, genre, or description
        recs = []
        for b in books:
            text = (b.get('title','') + ' ' + ' '.join(b.get('genre',[])) + ' ' + b.get('description','')).lower()
            if any(k in text for k in keywords) and b.get('available', False):
                recs.append(b)
        # fallback to previous issued or favorites
        if not recs:
            recs = recommend_for_user(user_email, top_k=3)
        if not recs:
            return "No recommendations found right now. Try another keyword."
        return "I suggest:\n" + "\n".join([f"- {r['title']} by {r['author']}" for r in recs])

    if "how to issue" in m or "issue a book" in m:
        return "Go to 'All Books', then click the Issue button (only available for Users)."

    if "how to return" in m or "return a book" in m:
        return "Go to 'Issued Books' and click Return next to the book you want to return."

    if "genres" in m or "categories" in m:
        genres = sorted({g for b in get_books() for g in b.get('genre',[])} )
        return "Available genres: " + ", ".join(genres) if genres else "No genre data available."

    if any(x in m for x in ["hi","hello","hey"]):
        return "Hello! I'm the Chatbot. Try: 'Recommend Python books', 'How to issue a book', or 'What genres are available?'."

    return "Sorry — I didn't understand. Try: 'Recommend Python books', 'How to issue a book', or 'What genres are available?'."


# -------------------------
# UI helpers
# -------------------------
def book_card_ui(book: Dict[str, Any], current_user_email: str):
    cols = st.columns([1, 3])

    # LEFT: cover
    with cols[0]:
        if book.get('cover_url'):
            try:
                st.image(book['cover_url'], width=110)
            except Exception:
                st.write("[No Image]")

    # RIGHT: details + actions
    with cols[1]:
        st.markdown(f"### {book['title']}")
        genres = book.get('genre', [])
        if isinstance(genres, str):
            genres = [genres]
        st.markdown(f"*Genre:* {', '.join(genres)}")
        desc = book.get('description', '')
        st.write(desc[:400] + ("…" if len(desc) > 400 else ""))
        st.write(f"*Available:* {'✅ Yes' if book.get('available', True) else '❌ No'}")

        c1, c2, c3 = st.columns([1, 1, 1])

        # --- check if this user already issued this book ---
        issued_records = get_issued()
        active_for_user = any(
            r for r in issued_records
            if r['book_id'] == book['id']
            and r['user_email'].lower() == current_user_email.lower()
            and not r.get('returned', False)
        )

        # ---------- Issue flow ----------
        with c1:
            issue_key       = f"issue_{book['id']}_{current_user_email}"
            confirm_flag    = f"confirm_{book['id']}_{current_user_email}"
            radio_key       = f"radio_{book['id']}_{current_user_email}"
            confirm_btn_key = f"confirm_btn_{book['id']}_{current_user_email}"

            if active_for_user:
                st.success("✅ Already issued by you")

            elif book.get("available", True):
                # Step 1: show Issue button
                if st.button("📥 Issue", key=issue_key):
                    st.session_state[confirm_flag] = True

                # Step 2: show confirmation (Yes/No + Confirm)
                if st.session_state.get(confirm_flag, False):
                    st.write(f"Are you sure you want to issue '{book['title']}'?")
                    choice = st.radio("Choose an option:", ["No", "Yes"], key=radio_key)
                    if st.button("Confirm", key=confirm_btn_key):
                        if choice == "Yes":
                            ok, msg = issue_book_to_user(current_user_email, book['id'])
                            if ok:
                                st.success(msg)
                                st.session_state[confirm_flag] = False
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.info("❌ Issue cancelled.")
                            st.session_state[confirm_flag] = False

            else:
                st.info("❌ Already issued")

        # ---------- Favorites ----------
        with c2:
            if st.button("⭐ Add to Favorites", key=f"fav_{book['id']}_{current_user_email}"):
                users = get_users()
                for u in users:
                    if u['email'].lower() == current_user_email.lower():
                        u.setdefault('favorites', [])
                        if book['id'] not in u['favorites']:
                            u['favorites'].append(book['id'])
                            save_users(users)
                            st.session_state['user'] = {
                                k: v for k, v in u.items() if k != 'password_hash'
                            }
                            st.success("Added to favorites.")
                        else:
                            st.info("Already in favorites.")
                st.rerun()

        # ---------- Overview ----------
        with c3:
            with st.expander("🔎 Overview"):
                if book.get('cover_url'):
                    st.image(book['cover_url'], width=150)
                st.markdown(f"*Title:* {book.get('title','')}")
                st.markdown(f"*Author:* {book.get('author','')}")
                genres2 = book.get('genre', [])
                if isinstance(genres2, str):
                    genres2 = [genres2]
                st.markdown(f"*Genre:* {', '.join(genres2)}")
                st.markdown("*Description:*")
                st.write(book.get('description',''))
                if book.get('index'):
                    st.markdown("*Index:*")
                    for idx in book.get('index', []):
                        st.write(f"- {idx}")

# -------------------------
# Main app
# -------------------------
def app():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    bootstrap_files()
    if 'user' not in st.session_state:
        st.session_state['user'] = None
    if 'view_book' not in st.session_state:
        st.session_state['view_book'] = None

    # --------- Login/Signup ---------
    if st.session_state['user'] is None:
        left,right = st.columns([2,1])
        with left:
            st.markdown("Welcome — login or sign up. Demo: user@example.com / user123")
        with right:
            choice = st.selectbox("Action", ["Login","Sign Up"], key="auth_choice")
        if choice=="Sign Up":
            st.header("Create account")
            name = st.text_input("Full name", key="su_name")
            mobile = st.text_input("Mobile number", key="su_mobile")
            email = st.text_input("Email", key="su_email")
            password = st.text_input("Password", type="password", key="su_pass")
            role = st.selectbox("Role", ["user","librarian"], key="su_role")
            if st.button("Create Account"):
                ok,msg = signup_user(name,mobile,email,password,role)
                if ok: st.success(msg + " Please login.")
                else: st.error(msg)
        else:
            st.header("Login")
            email = st.text_input("Email", key="li_email")
            password = st.text_input("Password", type="password", key="li_pass")
            if st.button("Login"):
                user = login_user(email,password)
                if user:
                    st.session_state['user'] = user
                    st.success(f"Welcome {user['name']}")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        st.stop()

    current_user = st.session_state['user']

    st.sidebar.markdown(f"### 👤 {current_user['name']}")
    st.sidebar.markdown(f"*Role:* {current_user['role'].capitalize()}")
    st.sidebar.markdown("---")

    # Notifications
    notes = []
    user_issued = user_active_issues(current_user['email'])
    for rec in user_issued:
        due = datetime.fromisoformat(rec['due_date']).date()
        days_left = (due - date.today()).days
        book = next((b for b in get_books() if b['id']==rec['book_id']), None)
        title = book['title'] if book else f"Book #{rec['book_id']}"
        if days_left <= 3 and days_left > 0:
            notes.append(f"⏳ {days_left} days left: {title} (due {rec['due_date']})")
        if days_left < 0:
            fine_now = calculate_fine_for_record(rec)
            notes.append(f"⚠ Overdue: {title} — fine ₹{fine_now}")
    if notes:
        st.sidebar.markdown("#### 🔔 Notifications")
        for n in notes:
            st.sidebar.write(n)
        st.sidebar.markdown("---")


    # Chatbot
    st.sidebar.markdown("### 🤖 Chatbot")
    chat_q = st.sidebar.text_input("Ask (e.g. 'Recommend Python books')", key="chat_input")
    if st.sidebar.button("Ask", key="chat_btn"):
        if chat_q:
            response = chatbot_response_for_user(current_user['email'], chat_q)
            st.sidebar.info(response)

    # Navigation
    if current_user['role']=="user":
        page = st.sidebar.radio("Navigate", ["Dashboard","All Books","Favorites","Issued Books","Recommendations","Account","Logout"])
    else:
        page = st.sidebar.radio("Navigate", ["Dashboard","All Books","Add Book","Delete Book","Issued Overview","Account","Logout"])

    # ---------- Pages ----------
    if page=="Logout":
        st.session_state.clear()
        st.rerun()

    elif page=="Dashboard":
        st.header("📊 Dashboard")
        users = get_users()
        u = next((x for x in users if x['email'].lower()==current_user['email'].lower()), current_user)
        st.write(f"- ⭐ Favorites: *{len(u.get('favorites', []))}*")
        st.write(f"- 📥 Active borrowed books: *{len(user_active_issues(current_user['email']))}*")

    elif page=="All Books":
        st.header("📚 All Books")
        all_books = get_books()
        q = st.text_input("Search by title / author / genre (press Enter)", key="search_books")
        filtered = all_books
        if q:
            ql = q.lower()
            filtered = [b for b in all_books if ql in b.get('title','').lower() or ql in b.get('author','').lower() or any(ql in g.lower() for g in b.get('genre',[]))]
        for b in filtered:
            book_card_ui(b, current_user['email'])
            st.divider()

        if st.session_state.get('view_book'):
            bid = st.session_state['view_book']
            b = next((x for x in all_books if x['id']==bid), None)
            if b:
                st.subheader(f"📖 Detailed Overview: {b['title']}")
                st.image(b.get('cover_url',''), width=150)
                st.markdown(f"*Author:* {b.get('author','')}")
                st.markdown(f"*Genre:* {', '.join(b.get('genre',[]))}")
                st.markdown("*Description:*")
                st.write(b.get('description',''))
                st.markdown("*Index:*")
                for idx in b.get('index',[]): st.write(f"- {idx}")
            if st.button("Close Overview", key="close_overview"):
                st.session_state['view_book'] = None
                st.rerun()

    elif page=="Favorites":
        st.header("⭐ Favorites")
        fav_ids = current_user.get('favorites', [])
        fav_books = [b for b in get_books() if b['id'] in fav_ids]
        if not fav_books: st.info("No favorites yet.")
        for b in fav_books:
            book_card_ui(b, current_user['email'])
            st.divider()

    elif page=="Issued Books":
        st.header("📥 Issued Books")
        active = user_active_issues(current_user['email'])
        if not active:
            st.info("No active issues.")
        for rec in active:
            b = next((x for x in get_books() if x['id']==rec['book_id']), None)
            if not b:
                continue
            st.markdown(f"### {b['title']} by {b['author']}")
            st.write(f"*Issued on:* {rec['issue_date']}  |  *Due:* {rec['due_date']}")
            fine_now = calculate_fine_for_record(rec)
            if fine_now > 0:
                st.warning(f"⚠ Fine so far: ₹{fine_now}")

            # ✅ FIXED unique key for return button
            if st.button("Return", key=f"return_{rec['book_id']}{current_user['email']}{rec['issue_date']}"):
                ok, msg, fine = return_book_from_user(current_user['email'], rec['book_id'])
                if ok:
                    st.success(f"{msg}. Fine: ₹{fine}")
                    st.rerun()
                else:
                    st.error(msg)


    elif page=="Recommendations":
        st.header("💡 Recommendations for you")
        recs = recommend_for_user(current_user['email'], top_k=6)
        for b in recs:
            book_card_ui(b, current_user['email'])
            st.divider()

    # ---------- Librarian Pages ----------
    elif page=="Add Book" and current_user['role']=="librarian":
        st.header("➕ Add a New Book")
        title = st.text_input("Title")
        author = st.text_input("Author")
        cover_url = st.text_input("Cover Image URL (optional)")
        description = st.text_area("Description")
        genres = st.text_input("Genres (comma separated)")
        keywords = st.text_input("Keywords (comma separated)")

        if st.button("Add Book"):
            books = get_books()
            new_id = max([b['id'] for b in books], default=0) + 1
            new_book = {
                "id": new_id,
                "title": title.strip(),
                "author": author.strip(),
                "cover_url": cover_url.strip(),
                "description": description.strip(),
                "index": [],
                "genre": [g.strip() for g in genres.split(",") if g.strip()],
                "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
                "available": True,
                "added_on": str(date.today())
            }
            books.append(new_book)
            save_books(books)
            st.success(f"Book '{title}' added successfully ✅")

    elif page=="Delete Book" and current_user['role']=="librarian":
        st.header("🗑 Delete a Book")
        books = get_books()
        titles = {b['title']: b['id'] for b in books}
        choice = st.selectbox("Select book to delete", [""] + list(titles.keys()))
        if choice and st.button("Delete"):
            books = [b for b in books if b['id'] != titles[choice]]
            save_books(books)
            st.success(f"Book '{choice}' deleted successfully ✅")
            st.rerun()

    elif page=="Issued Overview" and current_user['role']=="librarian":
        st.header("📖 Issued Books Overview")
        issued = get_issued()
        if not issued:
            st.info("No issued books yet.")
        else:
            for rec in issued:
                b = next((x for x in get_books() if x['id']==rec['book_id']), None)
                if not b: continue
                st.markdown(f"### {b['title']} by {b['author']}")
                st.write(f"*Issued to:* {rec['user_email']}")
                st.write(f"*Issued on:* {rec['issue_date']}  |  *Due:* {rec['due_date']}")
                if rec['returned']:
                    st.success(f"✅ Returned on {rec['return_date']}")
                else:
                    fine_now = calculate_fine_for_record(rec)
                    if fine_now > 0:
                        st.warning(f"⚠ Overdue — Fine so far: ₹{fine_now}")

    elif page=="Account":
        st.header("👤 Account Details")
        st.write(f"*Name:* {current_user['name']}")
        st.write(f"*Email:* {current_user['email']}")
        st.write(f"*Mobile:* {current_user['mobile']}")
        st.write(f"*Role:* {current_user['role']}")
        if st.button("Change Password", key="chg_pass_btn"):
            old = st.text_input("Current password", type="password", key="old_pass")
            new = st.text_input("New password", type="password", key="new_pass")
            confirm = st.text_input("Confirm new password", type="password", key="confirm_pass")
            if st.button("Submit Password Change", key="submit_pass"):
                users = get_users()
                u = next((x for x in users if x['email'].lower()==current_user['email'].lower()), None)
                if not u or u['password_hash'] != hash_password(old):
                    st.error("Current password incorrect.")
                elif new != confirm:
                    st.error("New passwords do not match.")
                else:
                    u['password_hash'] = hash_password(new)
                    save_users(users)
                    st.success("Password changed successfully.")

# -------------------------
# Entry point
# -------------------------
if __name__ == "__main__":
    app()


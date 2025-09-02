import streamlit as st
import json
import os
import shutil
import time
import hashlib
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
APP_TITLE = "📚 Smart Library System"

# -------------------------
# Safe JSON helpers
# -------------------------
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
        {"id": 1, "title": "To Kill a Mockingbird", "author": "Harper Lee",
         "cover_url": "https://m.media-amazon.com/images/I/81gepf1eMqL.jpg",
         "description": "A classic novel exploring racial injustice and moral growth in the Deep South.",
         "index": ["Chapter 1: Maycomb", "Chapter 2: The Radley Place", "Chapter 3: Atticus’ Advice"],
         "genre": ["Classic Fiction"], "keywords": ["justice", "racism", "law"], "available": True,
         "added_on": str(date.today() - timedelta(days=40))},
        {"id": 2, "title": "Clean Code", "author": "Robert C. Martin",
         "cover_url": "https://images-na.ssl-images-amazon.com/images/I/41xShlnTZTL._SX374_BO1,204,203,200_.jpg",
         "description": "A handbook of agile software craftsmanship.",
         "index": ["Meaningful Names", "Functions", "Formatting", "Objects and Data Structures"],
         "genre": ["Software Engineering"], "keywords": ["programming", "best practices", "code"], "available": True,
         "added_on": str(date.today() - timedelta(days=30))},
        {"id": 3, "title": "Python Crash Course", "author": "Eric Matthes",
         "cover_url": "https://images-na.ssl-images-amazon.com/images/I/51BpsT0LfJL._SX376_BO1,204,203,200_.jpg",
         "description": "A hands-on introduction to programming with Python.",
         "index": ["Getting Started", "Variables", "Loops", "Functions", "Projects"],
         "genre": ["Programming"], "keywords": ["python", "beginner", "projects"], "available": True,
         "added_on": str(date.today() - timedelta(days=7))},
    ]
    sample_users = [
        {"name": "Head Librarian", "email": "librarian@example.com", "mobile": "9999999999",
         "password_hash": hashlib.sha256("admin123".encode()).hexdigest(), "role": "librarian", "favorites": []},
        {"name": "Demo User", "email": "user@example.com", "mobile": "8888888888",
         "password_hash": hashlib.sha256("user123".encode()).hexdigest(), "role": "user", "favorites": []}
    ]
    sample_issued = []

    load_json(BOOKS_FILE, sample_books)
    load_json(USERS_FILE, sample_users)
    load_json(ISSUED_FILE, sample_issued)

# -------------------------
# Data access helpers
# -------------------------
def get_books() -> List[Dict[str,Any]]:
    return load_json(BOOKS_FILE, [])

def save_books(data: List[Dict[str,Any]]):
    save_json(BOOKS_FILE, data)

def get_users() -> List[Dict[str,Any]]:
    return load_json(USERS_FILE, [])

def save_users(data: List[Dict[str,Any]]):
    save_json(USERS_FILE, data)

def get_issued() -> List[Dict[str,Any]]:
    return load_json(ISSUED_FILE, [])

def save_issued(data: List[Dict[str,Any]]):
    save_json(ISSUED_FILE, data)

# -------------------------
# Auth functions
# -------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(email: str, password: str):
    users = get_users()
    email_l = email.strip().lower()
    phash = hash_password(password)
    for u in users:
        if u['email'].lower() == email_l and u['password_hash'] == phash:
            return {k: v for k,v in u.items() if k != 'password_hash'}
    return None

# -------------------------
# Issue / Return / fines
# -------------------------
def issue_book_to_user(user_email: str, book_id: int, loan_days: int = DEFAULT_LOAN_DAYS) -> (bool,str):
    books = get_books()
    issued = get_issued()
    book = next((b for b in books if b['id'] == book_id), None)
    if not book:
        return False, "Book not found."
    if not book.get('available', True):
        return False, "Book currently not available."

    for b in books:
        if b['id'] == book_id:
            b['available'] = False
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
    save_books(books)

    return True, "Book returned.", max(0, fine)

def user_active_issues(user_email: str) -> List[Dict[str,Any]]:
    return [r for r in get_issued() if r['user_email'].lower() == user_email.lower() and not r.get('returned', False)]

# -------------------------
# Recommendations & Chatbot
# -------------------------
def recommend_for_user(user_email: str, top_k: int = 6) -> List[Dict[str,Any]]:
    books = get_books()
    issued = get_issued()
    users = get_users()
    u = next((x for x in users if x['email'].lower() == user_email.lower()), None)
    fav_ids = u.get('favorites', []) if u else []

    user_books_ids = [r['book_id'] for r in issued if r['user_email'].lower() == user_email.lower()] + fav_ids
    if not user_books_ids:
        available = [b for b in books if b.get('available', False)]
        return sorted(available, key=lambda x: x.get('added_on','0000-00-00'), reverse=True)[:top_k]

    scored = []
    for b in books:
        if b['id'] in user_books_ids:
            continue
        score = 0
        for bid in user_books_ids:
            ub = next((x for x in books if x['id'] == bid), None)
            if not ub: continue
            if b.get('author') == ub.get('author'): score += 3
            score += len(set(b.get('genre',[])) & set(ub.get('genre',[]))) * 1.5
            score += len(set(b.get('keywords',[])) & set(ub.get('keywords',[]))) * 0.7
        score += (1 if b.get('available', False) else 0) * 0.2
        scored.append((score,b))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [b for _,b in scored[:top_k]]

def chatbot_response_for_user(user_email: str, message: str) -> str:
    m = message.strip().lower()
    if not m:
        return "Ask me for recommendations or how to issue/return books."
    if "recommend" in m or "suggest" in m:
        recs = recommend_for_user(user_email, top_k=3)
        if not recs:
            return "No recommendations right now."
        return "I recommend:\n" + "\n".join([f"- {r['title']} by {r['author']}" for r in recs])
    if "how to issue" in m or "issue a book" in m:
        return "Go to 'All Books', then click the Issue button."
    if "how to return" in m or "return a book" in m:
        return "Go to 'Issued Books' and click Return."
    return "Sorry, I didn't understand. Try: 'Recommend books', 'How to issue a book'."

# -------------------------
# UI helpers
# -------------------------
def book_card_ui(book: Dict[str,Any], current_user_email: str):
    cols = st.columns([1, 3])
    with cols[0]:
        if book.get('cover_url'):
            try: st.image(book['cover_url'], width=110)
            except: st.write("[No Image]")
    with cols[1]:
        st.markdown(f"### {book['title']}")
        st.markdown(f"**Author:** {book['author']}  |  **Genre:** {', '.join(book.get('genre',[]))}")
        st.write(book.get('description','')[:400] + ("…" if len(book.get('description',''))>400 else ""))
        st.write(f"**Available:** {'✅ Yes' if book.get('available', False) else '❌ No'}")

        c1, c2 = st.columns([1,1])
        issue_key = f"issue_{book['id']}"
        if book.get('available', False):
            if issue_key not in st.session_state: st.session_state[issue_key] = False
            if not st.session_state[issue_key]:
                if c1.button("📥 Issue", key=f"btn_{issue_key}"):
                    st.session_state[issue_key] = True
            else:
                st.warning(f"Confirm issuing '{book['title']}'?")
                if c1.button("✅ Yes", key=f"confirm_yes_{issue_key}"):
                    ok,msg = issue_book_to_user(current_user_email, book['id'])
                    if ok: st.success(msg)
                    else: st.error(msg)
                    st.session_state[issue_key] = False
                    st.experimental_rerun()
                if c1.button("❌ Cancel", key=f"confirm_no_{issue_key}"):
                    st.session_state[issue_key] = False
        else: c1.button("📥 Issue (Unavailable)", disabled=True, key=f"btn_disabled_{book['id']}")

# -------------------------
# Main app
# -------------------------
def app():
    st.set_page_config(APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    bootstrap_files()

    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if not st.session_state['logged_in']:
        st.subheader("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(email, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user'] = user
                st.success(f"Welcome {user['name']}!")
                st.experimental_rerun()
            else: st.error("Invalid email/password")
        st.stop()

    current_user = st.session_state['user']
    all_books = get_books()
    st.header("📚 All Books")
    for b in all_books:
        book_card_ui(b, current_user['email'])
        st.divider()

if __name__ == "__main__":
    app()

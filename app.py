# app.py
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

def signup_user(name: str, mobile: str, email: str, password: str, role: str) -> (bool,str):
    users = get_users()
    email_l = email.strip().lower()
    if any(u['email'].lower() == email_l for u in users):
        return False, "Email already registered."
    users.append({
        "name": name.strip(),
        "mobile": mobile.strip(),
        "email": email_l,
        "password_hash": hash_password(password),
        "role": role,
        "favorites": []
    })
    save_users(users)
    return True, "Account created."

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

    # mark unavailable
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

def calculate_fine_for_record(rec: Dict[str,Any]) -> int:
    due = datetime.fromisoformat(rec['due_date']).date()
    today = date.today()
    return max(0, (today - due).days * FINE_PER_DAY) if today > due else 0

# -------------------------
# Recommendations & Chatbot
# -------------------------
def recommend_for_user(user_email: str, top_k: int = 6) -> List[Dict[str,Any]]:
    books = get_books()
    issued = get_issued()
    users = get_users()
    # collect genres from user's issued books
    issued_genres = set()
    for r in issued:
        if r['user_email'].lower() == user_email.lower():
            bk = next((b for b in books if b['id'] == r['book_id']), None)
            if bk:
                for g in bk.get('genre', []):
                    issued_genres.add(g)
    # collect genres from user's favorites
    user = next((u for u in users if u['email'].lower() == user_email.lower()), None)
    fav_genres = set()
    if user:
        for fid in user.get('favorites', []):
            bk = next((b for b in books if b['id'] == fid), None)
            if bk:
                for g in bk.get('genre', []):
                    fav_genres.add(g)
    combined_genres = issued_genres | fav_genres

    if combined_genres:
        # recommend books matching those genres, exclude already issued to user
        user_issued_ids = {r['book_id'] for r in issued if r['user_email'].lower() == user_email.lower()}
        user_fav_ids = set(user.get('favorites', [])) if user else set()
        candidates = [b for b in books if any(g in combined_genres for g in b.get('genre', [])) and b['id'] not in user_issued_ids and b['id'] not in user_fav_ids]
        return candidates[:top_k] if candidates else []
    # cold start
    available = [b for b in books if b.get('available', False)]
    return sorted(available, key=lambda x: x.get('added_on','0000-00-00'), reverse=True)[:top_k] if available else books[:top_k]

def chatbot_response_for_user(user_email: str, message: str) -> str:
    m = message.strip().lower()
    if not m:
        return "Ask me for recommendations or how to issue/return books."
    # if user gives an interest keyword, search by genre/keywords/title
    keywords = m.split()
    books = get_books()
    suggestions = []
    for b in books:
        text = " ".join((b.get('title',''), " ".join(b.get('genre',[])), " ".join(b.get('keywords',[])))).lower()
        if any(k in text for k in keywords):
            suggestions.append(b)
    if suggestions:
        top3 = suggestions[:6]
        return "Here are books matching your interest:\n" + "\n".join([f"- {r['title']} by {r['author']}" for r in top3])
    # fallback to recommend_for_user if user asked for recommend
    if "recommend" in m or "suggest" in m:
        recs = recommend_for_user(user_email, top_k=6)
        if recs:
            return "Based on your history/favorites, I suggest:\n" + "\n".join([f"- {r['title']} by {r['author']}" for r in recs])
        else:
            return "No personalized recommendations available yet. Try issuing/favoriting books first."
    if "how to issue" in m or "issue" in m:
        return "To issue a book: go to 'All Books', click Issue (you'll get a Yes/No confirmation)."
    if "how to return" in m or "return" in m:
        return "To return: go to 'Issued Books' and press Return. Fines are computed automatically for late returns."
    if any(x in m for x in ["hi","hello","hey"]):
        return "Hello! Tell me an interest (e.g. 'python', 'fiction', 'ai') and I'll suggest books."
    return "Sorry, I didn't understand. Try typing a genre or 'recommend'."

# -------------------------
# UI helpers
# -------------------------
def book_card_ui(book: Dict[str,Any], current_user_email: str):
    cols = st.columns([1, 3])
    with cols[0]:
        if book.get('cover_url'):
            try:
                st.image(book['cover_url'], width=110)
            except Exception:
                st.write("[No Image]")
    with cols[1]:
        st.markdown(f"### {book['title']}")
        st.markdown(f"**Author:** {book['author']}  |  **Genre:** {', '.join(book.get('genre',[]))}")
        st.write(book.get('description','')[:400] + ("…" if len(book.get('description',''))>400 else ""))
        st.write(f"**Available:** {'✅ Yes' if book.get('available', False) else '❌ No'}")
        c1, c2, c3 = st.columns([1,1,1])
        # Issue button (single) with confirmation
        with c1:
            if book.get('available', False):
                if st.button("Issue", key=f"issue_btn_{book['id']}"):
                    # set pending_issue in session for confirmation
                    st.session_state['pending_issue'] = {'book_id': book['id'], 'title': book['title']}
                    st.experimental_rerun()
            else:
                st.button("Not Available", key=f"issue_disabled_{book['id']}", disabled=True)
        # Favorite button (single)
        with c2:
            if st.button("Add to Favorites", key=f"fav_btn_{book['id']}"):
                users = get_users()
                for u in users:
                    if u['email'].lower() == current_user_email.lower():
                        if book['id'] not in u.get('favorites', []):
                            u.setdefault('favorites', []).append(book['id'])
                            save_users(users)
                            st.success("Added to favorites.")
                        else:
                            st.info("Already in favorites.")
                st.experimental_rerun()
        # Overview
        with c3:
            if st.button("Overview", key=f"ov_btn_{book['id']}"):
                st.session_state['view_book'] = book['id']

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
    if 'pending_issue' not in st.session_state:
        st.session_state['pending_issue'] = None

    # Not logged in
    if st.session_state['user'] is None:
        left, right = st.columns([2,1])
        with left:
            st.markdown("Welcome — please login or sign up. Demo accounts: `librarian@example.com / admin123`, `user@example.com / user123`.")
        with right:
            choice = st.selectbox("Action", ["Login","Sign Up"], key="auth_choice")
        if choice == "Sign Up":
            st.header("Create account")
            name = st.text_input("Full name", key="su_name")
            mobile = st.text_input("Mobile number", key="su_mobile")
            email = st.text_input("Email", key="su_email")
            password = st.text_input("Password", type="password", key="su_pass")
            role = st.selectbox("Role", ["user","librarian"], key="su_role")
            if st.button("Create Account"):
                ok,msg = signup_user(name,mobile,email,password,role)
                if ok:
                    st.success(msg + " Please login.")
                else:
                    st.error(msg)
        else:
            st.header("Login")
            email = st.text_input("Email", key="li_email")
            password = st.text_input("Password", type="password", key="li_pass")
            if st.button("Login"):
                user = login_user(email, password)
                if user:
                    st.session_state['user'] = user
                    st.success(f"Welcome {user['name']} — opening dashboard...")
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials.")
        st.stop()

    # Logged in pages
    current_user = st.session_state['user']
    st.sidebar.markdown(f"### 👤 {current_user['name']}")
    st.sidebar.markdown(f"**Role:** {current_user['role'].capitalize()}")
    st.sidebar.markdown("---")

    # Notifications (due soon / overdue)
    notes = []
    user_issued = user_active_issues(current_user['email'])
    for rec in user_issued:
        due = datetime.fromisoformat(rec['due_date']).date()
        days_left = (due - date.today()).days
        book = next((b for b in get_books() if b['id'] == rec['book_id']), None)
        title = book['title'] if book else f"Book #{rec['book_id']}"
        if 0 < days_left <= 3:
            notes.append(f"⏳ {days_left} days left to return: {title} (due {rec['due_date']})")
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
    chat_q = st.sidebar.text_input("Tell me your interest (e.g. 'python', 'fiction')", key="chat_q")
    if st.sidebar.button("Ask"):
        if chat_q:
            resp = chatbot_response_for_user(current_user['email'], chat_q)
            st.sidebar.info(resp)

    # navigation
    if current_user['role'] == 'user':
        page = st.sidebar.radio("Navigate", ["Dashboard","All Books","Favorites","Issued Books","Recommendations","Account","Logout"])
    else:
        page = st.sidebar.radio("Navigate", ["Dashboard","All Books","Add Book","Delete Book","Issued Overview","Account","Logout"])

    if page == "Logout":
        st.session_state.clear()
        st.experimental_rerun()

    # Dashboard
    if page == "Dashboard":
        st.header("📊 Dashboard")
        users = get_users()
        u = next((x for x in users if x['email'].lower() == current_user['email'].lower()), current_user)
        fav_count = len(u.get('favorites', []))
        active_issues = len(user_active_issues(current_user['email']))
        st.write(f"- ⭐ Favorites: **{fav_count}**")
        st.write(f"- 📥 Active borrowed books: **{active_issues}**")

    # All Books page - main listing + confirmation UI
    elif page == "All Books":
        st.header("📚 All Books")
        all_books = get_books()
        q = st.text_input("Search by title / author / genre (press Enter)", key="search_q")
        filtered = all_books
        if q:
            ql = q.lower()
            filtered = [b for b in all_books if ql in b.get('title','').lower() or ql in b.get('author','').lower() or any(ql in g.lower() for g in b.get('genre',[]))]
        for b in filtered:
            book_card_ui(b, current_user['email'])
            st.divider()

        # Confirmation popup for pending issue (single place)
        if st.session_state.get('pending_issue'):
            pending = st.session_state['pending_issue']
            # fetch book to ensure latest status
            book = next((x for x in get_books() if x['id'] == pending['book_id']), None)
            if book:
                st.markdown("---")
                st.warning(f"Do you want to issue '{book['title']}'? This will set due date to {DEFAULT_LOAN_DAYS} days from today.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Issue"):
                        ok,msg = issue_book_to_user(current_user['email'], book['id'])
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                        st.session_state['pending_issue'] = None
                        st.experimental_rerun()
                with col2:
                    if st.button("❌ No, Cancel"):
                        st.info("Issue cancelled.")
                        st.session_state['pending_issue'] = None
                        st.experimental_rerun()
            else:
                st.info("Selected book not found anymore.")
                st.session_state['pending_issue'] = None

        # book overview (if requested)
        if st.session_state.get('view_book'):
            bid = st.session_state.pop('view_book')
            book = next((x for x in get_books() if x['id'] == bid), None)
            if book:
                st.markdown("---")
                st.subheader(f"📖 {book['title']} — Overview")
                left, right = st.columns([1,2])
                with left:
                    if book.get('cover_url'):
                        try:
                            st.image(book['cover_url'], width=200)
                        except Exception:
                            st.write("[Image]")
                with right:
                    st.markdown(f"**Author:** {book['author']}")
                    st.markdown(f"**Genre:** {', '.join(book.get('genre',[]))}")
                    st.markdown("**Description**")
                    st.write(book.get('description',''))
                    st.markdown("**Index**")
                    for i, ch in enumerate(book.get('index', []), 1):
                        st.write(f"{i}. {ch}")

    # Favorites page (clean Issue & Remove actions)
    elif page == "Favorites":
        st.header("⭐ Your Favorites")
        users = get_users()
        u = next((x for x in users if x['email'].lower() == current_user['email'].lower()), {})
        fav_ids = u.get('favorites', [])
        if not fav_ids:
            st.info("No favorites yet.")
        else:
            for bid in fav_ids:
                b = next((x for x in get_books() if x['id'] == bid), None)
                if b:
                    st.markdown(f"**{b['title']}** — {b['author']}")
                    c1,c2 = st.columns([1,4])
                    with c1:
                        if b.get('cover_url'):
                            try:
                                st.image(b['cover_url'], width=80)
                            except Exception:
                                st.write("[Img]")
                    with c2:
                        if b.get('available', False):
                            if st.button("Issue", key=f"fav_issue_{b['id']}"):
                                # set pending and confirmation will appear in All Books page after rerun
                                st.session_state['pending_issue'] = {'book_id': b['id'], 'title': b['title']}
                                st.experimental_rerun()
                        else:
                            st.button("Not Available", key=f"fav_notavail_{b['id']}", disabled=True)
                        if st.button("Remove favorite", key=f"rmfav_{b['id']}"):
                            users = get_users()
                            for uu in users:
                                if uu['email'].lower() == current_user['email'].lower():
                                    uu['favorites'] = [x for x in uu.get('favorites', []) if x != b['id']]
                                    save_users(users)
                                    st.success("Removed from favorites.")
                                    st.experimental_rerun()

    # Issued Books page
    elif page == "Issued Books":
        st.header("📥 Your Issued Books")
        issued = user_active_issues(current_user['email'])
        if not issued:
            st.info("No active issued books.")
        else:
            for rec in issued:
                book = next((b for b in get_books() if b['id'] == rec['book_id']), None)
                if not book:
                    continue
                st.markdown(f"**{book['title']}** by {book['author']}")
                st.write(f"Issue Date: {rec['issue_date']}  |  Due: {rec['due_date']}")
                fine = calculate_fine_for_record(rec)
                if fine > 0:
                    st.error(f"Overdue — Current fine ₹{fine}")
                else:
                    due = datetime.fromisoformat(rec['due_date']).date()
                    st.info(f"Days left: {(due - date.today()).days} day(s)")
                if st.button(f"Return {book['title']}", key=f"return_{rec['book_id']}"):
                    ok,msg,fine_amt = return_book_from_user(current_user['email'], rec['book_id'])
                    if ok:
                        if fine_amt > 0:
                            st.warning(f"Returned. Please pay fine: ₹{fine_amt}")
                        else:
                            st.success("Returned successfully. No fine.")
                    else:
                        st.error(msg)
                    st.experimental_rerun()

    # Recommendations - based on issued + favorites (no random)
    elif page == "Recommendations":
        st.header("🎯 Recommended for you")
        recs = recommend_for_user(current_user['email'])
        if not recs:
            st.info("No personalized recommendations yet. Issue or favorite books to get tailored suggestions.")
        else:
            for r in recs:
                st.write(f"**{r['title']}** — {r['author']} (Available: {'Yes' if r.get('available') else 'No'})")
                if r.get('available', False):
                    if st.button("Issue", key=f"rec_issue_{r['id']}"):
                        st.session_state['pending_issue'] = {'book_id': r['id'], 'title': r['title']}
                        st.experimental_rerun()

    # Account
    elif page == "Account":
        st.header("⚙️ Account")
        st.write(f"**Name:** {current_user['name']}")
        st.write(f"**Email:** {current_user['email']}")
        st.write(f"**Mobile:** {current_user['mobile']}")
        st.write(f"**Role:** {current_user['role']}")
        if st.button("Delete my account"):
            users = get_users()
            users = [u for u in users if u['email'].lower() != current_user['email'].lower()]
            save_users(users)
            st.success("Account deleted.")
            st.session_state.clear()
            st.experimental_rerun()

    # Librarian pages
    elif page == "Add Book" and current_user['role'] == 'librarian':
        st.header("➕ Add New Book")
        with st.form("add_book_form"):
            title = st.text_input("Title")
            author = st.text_input("Author")
            cover_url = st.text_input("Cover URL")
            description = st.text_area("Description")
            genre_raw = st.text_input("Genres (comma separated)")
            keywords_raw = st.text_input("Keywords (comma separated)")
            index_raw = st.text_area("Index (one item per line)")
            submitted = st.form_submit_button("Add Book")
            if submitted:
                books = get_books()
                new_id = max([b['id'] for b in books], default=0) + 1
                books.append({
                    "id": new_id,
                    "title": title.strip(),
                    "author": author.strip(),
                    "cover_url": cover_url.strip(),
                    "description": description.strip(),
                    "index": [s.strip() for s in index_raw.splitlines() if s.strip()],
                    "genre": [g.strip() for g in genre_raw.split(",") if g.strip()],
                    "keywords": [k.strip() for k in keywords_raw.split(",") if k.strip()],
                    "available": True,
                    "added_on": str(date.today())
                })
                save_books(books)
                st.success("Book added.")
                st.experimental_rerun()

    elif page == "Delete Book" and current_user['role'] == 'librarian':
        st.header("🗑 Delete Book")
        books = get_books()
        if not books:
            st.info("No books.")
        else:
            choice = st.selectbox("Select book to delete", [f"{b['id']} — {b['title']}" for b in books])
            if st.button("Delete selected book"):
                bid = int(choice.split(" — ")[0])
                issued = get_issued()
                active = [r for r in issued if r['book_id'] == bid and not r.get('returned', False)]
                if active:
                    st.error("Cannot delete book: it is currently issued to user(s).")
                else:
                    books = [b for b in books if b['id'] != bid]
                    save_books(books)
                    st.success("Deleted.")
                    st.experimental_rerun()

    elif page == "Issued Overview" and current_user['role'] == 'librarian':
        st.header("📋 Issued Books Overview")
        issued = get_issued()
        if not issued:
            st.info("No issued records.")
        else:
            for rec in issued:
                book = next((b for b in get_books() if b['id'] == rec['book_id']), None)
                st.write(f"**{book['title'] if book else rec['book_id']}** — Borrower: {rec['user_email']}")
                st.write(f"Issue: {rec['issue_date']} | Due: {rec['due_date']} | Returned: {'Yes' if rec['returned'] else 'No'}")
                if not rec['returned']:
                    fine_now = calculate_fine_for_record(rec)
                    if fine_now > 0:
                        st.error(f"Fine: ₹{fine_now}")

if __name__ == "__main__":
    app()

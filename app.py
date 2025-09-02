# app.py
import streamlit as st
import json
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
import random

# ==========================
# Config
# ==========================
BOOKS_FILE = Path("books_data.json")
USERS_FILE = Path("users_data.json")
ISSUED_FILE = Path("issued_books.json")

FINE_PER_DAY = 10  # currency units per late day
DEFAULT_LOAN_DAYS = 14
APP_TITLE = "📚 Smart Library — Streamlit"

# ==========================
# Utilities: load / save / bootstrap
# ==========================
def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def bootstrap_files():
    # books
    if not BOOKS_FILE.exists():
        sample_books = [
            {
                "id": 1,
                "title": "To Kill a Mockingbird",
                "author": "Harper Lee",
                "cover_url": "https://m.media-amazon.com/images/I/81gepf1eMqL.jpg",
                "description": "A classic novel exploring racial injustice and moral growth in the Deep South.",
                "index": ["Chapter 1: Maycomb", "Chapter 2: The Radley Place", "Chapter 3: Atticus’ Advice"],
                "genre": ["Classic Fiction"],
                "keywords": ["justice","racism","law"],
                "available": True,
                "added_on": str(date.today())
            },
            {
                "id": 2,
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "cover_url": "https://images-na.ssl-images-amazon.com/images/I/41xShlnTZTL._SX374_BO1,204,203,200_.jpg",
                "description": "A handbook of agile software craftsmanship.",
                "index": ["Meaningful Names","Functions","Formatting","Objects and Data Structures"],
                "genre": ["Software Engineering"],
                "keywords": ["programming","best practices","code"],
                "available": True,
                "added_on": str(date.today() - timedelta(days=10))
            },
            {
                "id": 3,
                "title": "Introduction to Algorithms",
                "author": "Thomas H. Cormen",
                "cover_url": "https://images-na.ssl-images-amazon.com/images/I/41SN2C3dG+L._SX376_BO1,204,203,200_.jpg",
                "description": "The classic CLRS algorithms textbook.",
                "index": ["Sorting","Divide-and-Conquer","Dynamic Programming","Graph Algorithms"],
                "genre": ["Computer Science","Algorithms"],
                "keywords": ["algorithms","theory","ds"],
                "available": True,
                "added_on": str(date.today() - timedelta(days=30))
            },
            {
                "id": 4,
                "title": "Python Crash Course",
                "author": "Eric Matthes",
                "cover_url": "https://images-na.ssl-images-amazon.com/images/I/51BpsT0LfJL._SX376_BO1,204,203,200_.jpg",
                "description": "A hands-on introduction to programming with Python.",
                "index": ["Getting Started","Variables","Loops","Functions","Projects"],
                "genre": ["Programming"],
                "keywords": ["python","beginner","projects"],
                "available": True,
                "added_on": str(date.today() - timedelta(days=5))
            },
            {
                "id": 5,
                "title": "Deep Learning",
                "author": "Ian Goodfellow",
                "cover_url": "https://images-na.ssl-images-amazon.com/images/I/41M4vL0xh-L._SX379_BO1,204,203,200_.jpg",
                "description": "Foundations and techniques in deep learning.",
                "index": ["Linear Algebra","Optimization","Neural Networks","Convolutional Nets"],
                "genre": ["AI","Machine Learning"],
                "keywords": ["deep learning","neural networks","AI"],
                "available": True,
                "added_on": str(date.today() - timedelta(days=2))
            },
        ]
        save_json(BOOKS_FILE, sample_books)

    # users (simple: email as unique id; demo librarian)
    if not USERS_FILE.exists():
        sample_users = [
            {
                "name": "Head Librarian",
                "email": "librarian@example.com",
                "mobile": "9999999999",
                "password": "admin123",  # demo only; change before real use
                "role": "Librarian",
                "favorites": []
            },
            {
                "name": "Demo User",
                "email": "user@example.com",
                "mobile": "8888888888",
                "password": "user123",
                "role": "User",
                "favorites": []
            }
        ]
        save_json(USERS_FILE, sample_users)

    # issued
    if not ISSUED_FILE.exists():
        save_json(ISSUED_FILE, [])

# ==========================
# Data accessors
# ==========================
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

# ==========================
# Auth functions
# ==========================
def signup_user(name: str, mobile: str, email: str, password: str, role: str) -> (bool,str):
    users = get_users()
    if any(u['email'].lower() == email.lower() for u in users):
        return False, "Email already registered."
    users.append({
        "name": name.strip(),
        "mobile": mobile.strip(),
        "email": email.strip().lower(),
        "password": password,
        "role": role,
        "favorites": []
    })
    save_users(users)
    return True, "Account created."

def login_user(email: str, password: str):
    users = get_users()
    for u in users:
        if u['email'].lower() == email.lower() and u['password'] == password:
            return u
    return None

# ==========================
# Issue / return / fines
# ==========================
def issue_book_to_user(user_email: str, book_id: int, loan_days: int = DEFAULT_LOAN_DAYS) -> (bool,str):
    books = get_books()
    users = get_users()
    issued = get_issued()

    book = next((b for b in books if b['id'] == book_id), None)
    if not book:
        return False, "Book not found."
    if not book.get('available', True):
        return False, "Book not available."

    # mark book unavailable
    for b in books:
        if b['id'] == book_id:
            b['available'] = False
    save_books(books)

    # create issued record
    t0 = date.today()
    due = t0 + timedelta(days=loan_days)
    issued.append({
        "user_email": user_email.lower(),
        "book_id": book_id,
        "issue_date": str(t0),
        "due_date": str(due),
        "returned": False,
        "return_date": None
    })
    save_issued(issued)
    return True, f"Issued '{book['title']}' — due {due}"

def return_book_from_user(user_email: str, book_id: int) -> (bool,str,int):
    books = get_books()
    issued = get_issued()
    today = date.today()

    rec = next((r for r in issued if r['user_email'].lower() == user_email.lower() and r['book_id'] == book_id and not r['returned']), None)
    if not rec:
        return False, "No active issue found for this book & user.", 0

    # calculate fine
    due = datetime.fromisoformat(rec['due_date']).date()
    fine = max((today - due).days * FINE_PER_DAY, 0) if today > due else 0

    # mark returned
    rec['returned'] = True
    rec['return_date'] = str(today)
    save_issued(issued)

    # mark book available
    for b in books:
        if b['id'] == book_id:
            b['available'] = True
    save_books(books)

    return True, "Book returned.", fine

def user_active_issues(user_email: str) -> List[Dict[str,Any]]:
    issued = get_issued()
    return [r for r in issued if r['user_email'].lower() == user_email.lower() and not r['returned']]

def calculate_fine_for_record(rec: Dict[str,Any]) -> int:
    due = datetime.fromisoformat(rec['due_date']).date()
    today = date.today()
    if today > due:
        return (today - due).days * FINE_PER_DAY
    return 0

# ==========================
# Recommendations (simple content-based)
# ==========================
def recommend_for_user(user_email: str, top_k: int = 6) -> List[Dict[str,Any]]:
    books = get_books()
    issued = get_issued()
    user_issued = [r for r in issued if r['user_email'].lower() == user_email.lower()]
    if not user_issued:
        # cold start: return most available or random
        available = [b for b in books if b.get('available', False)]
        return (sorted(available, key=lambda x: x.get('added_on', "0000-00-00"), reverse=True)[:top_k]
                if available else books[:top_k])
    # use last borrowed book as seed
    last = sorted(user_issued, key=lambda r: r['issue_date'], reverse=True)[0]
    seed = next((b for b in books if b['id'] == last['book_id']), None)
    if not seed:
        return books[:top_k]
    def score(b):
        if b['id'] == seed['id']:
            return -999  # don't recommend the same book
        s = 0
        if b.get('author') == seed.get('author'):
            s += 3
        s += len(set(b.get('genre', [])) & set(seed.get('genre', []))) * 1.5
        s += len(set(b.get('keywords', [])) & set(seed.get('keywords', []))) * 0.7
        s += (1 if b.get('available', False) else 0) * 0.5
        return s
    ranked = sorted(books, key=score, reverse=True)
    return ranked[:top_k]

# ==========================
# Smart Notifications
# ==========================
def compute_notifications_for_user(user_email: str) -> List[str]:
    notes = []
    # due-date reminders
    for rec in user_active_issues(user_email):
        fine_days = calculate_fine_for_record(rec)
        due = datetime.fromisoformat(rec['due_date']).date()
        days_left = (due - date.today()).days
        book = next((b for b in get_books() if b['id'] == rec['book_id']), None)
        title = book['title'] if book else f"Book #{rec['book_id']}"
        if days_left > 0 and days_left <= 3:
            notes.append(f"📣 {days_left} day(s) left to return: {title} (Due {rec['due_date']})")
        elif days_left <= 0 and not rec['returned']:
            notes.append(f"⚠ Overdue: {title} (Due {rec['due_date']}) — current fine ₹{fine_days}")
    # new arrivals in user's favorite genres (if any)
    users = get_users()
    user = next((u for u in users if u['email'].lower() == user_email.lower()), None)
    if user and user.get('favorites'):
        fav_ids = user.get('favorites', [])
        # build favorite genres
        fav_genres = set()
        for f in get_books():
            if f['id'] in fav_ids:
                for g in f.get('genre', []):
                    fav_genres.add(g)
        # find books added in last 7 days matching those genres
        if fav_genres:
            recent = [b for b in get_books() if (date.fromisoformat(b.get('added_on','1900-01-01')) >= date.today() - timedelta(days=7))]
            for b in recent:
                if set(b.get('genre', [])) & fav_genres:
                    notes.append(f"✨ New in your favorite genre: {b['title']} ({', '.join(b.get('genre',[]))})")
    return notes

# ==========================
# Chatbot Librarian (very simple rule-based)
# ==========================
def chatbot_response(user_email: str, message: str) -> str:
    m = message.strip().lower()
    # quick commands
    if "recommend" in m or "suggest" in m:
        # find by keyword
        if "python" in m:
            recs = [b for b in get_books() if 'python' in ' '.join(b.get('keywords', [])).lower() or 'python' in b['title'].lower()]
        else:
            recs = recommend_for_user(user_email, top_k=3)
        if not recs:
            return "I couldn't find recommendations right now. Try another keyword."
        return "I recommend:\n" + "\n".join([f"- {r['title']} by {r['author']}" for r in recs])
    if "how to issue" in m or "issue a book" in m:
        return "To issue a book: go to 'All Books', find the book and click the Issue button. You can also add to Favorites and issue from there."
    if "return" in m or "how to return" in m:
        return "To return: go to 'Issued Books' in your dashboard and click Return for the book you want to return."
    if "genres" in m or "categories" in m:
        genres = set(g for b in get_books() for g in b.get('genre', []))
        return "Available genres: " + ", ".join(sorted(genres))
    # fallback small talk
    if any(w in m for w in ["hi","hello","hey"]):
        return "Hello! I'm the Chatbot Librarian — ask me for book suggestions, how to issue/return, or available genres."
    return "Sorry, I didn't understand. Try: 'Recommend Python books', 'How to issue a book', or 'What genres are available?'."

# ==========================
# UI helpers: cards / book row
# ==========================
def book_card(book: Dict[str,Any], user: Dict[str,Any]):
    cols = st.columns([1,3])
    with cols[0]:
        try:
            st.image(book.get('cover_url'), width=110)
        except Exception:
            st.write("[No Image]")
    with cols[1]:
        st.markdown(f"### {book['title']}")
        st.markdown(f"**Author:** {book['author']}  |  **Genre:** {', '.join(book.get('genre',[]))}")
        st.write(book.get('description','')[:350] + ("…" if len(book.get('description',''))>350 else ""))
        st.write(f"**Available:** {'✅ Yes' if book.get('available', False) else '❌ No'}")
        # Buttons row
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if book.get('available', False):
                if st.button(f"📥 Issue ({book['id']})", key=f"issue_{book['id']}"):
                    ok,msg = issue_book_to_user(user['email'], book['id'])
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.experimental_rerun()
        with c2:
            if st.button(f"⭐ Favorite ({book['id']})", key=f"fav_{book['id']}"):
                users = get_users()
                for u in users:
                    if u['email'].lower() == user['email'].lower():
                        if book['id'] not in u.get('favorites', []):
                            u.setdefault('favorites', []).append(book['id'])
                            save_users(users)
                            st.success("Added to favorites.")
                        else:
                            st.info("Already in favorites.")
                st.experimental_rerun()
        with c3:
            if st.button(f"🔎 Overview ({book['id']})", key=f"ov_{book['id']}"):
                st.session_state['view_book'] = book['id']

# ==========================
# Main app layout
# ==========================
def app():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    # bootstrap files if missing
    bootstrap_files()

    if 'user' not in st.session_state:
        st.session_state['user'] = None
    if 'view_book' not in st.session_state:
        st.session_state['view_book'] = None

    # Top navigation: login if not logged in
    if st.session_state['user'] is None:
        left, right = st.columns([2,1])
        with left:
            st.markdown("Welcome! Please **Login** or **Sign up** to continue. Demo accounts: `librarian@example.com` / `admin123` and `user@example.com` / `user123`.")
        with right:
            choice = st.selectbox("Action", ["Login","Sign Up"], key="auth_choice")
        if choice == "Sign Up":
            st.header("Create Account")
            name = st.text_input("Full name", key="su_name")
            mobile = st.text_input("Mobile number", key="su_mobile")
            email = st.text_input("Email", key="su_email")
            password = st.text_input("Password", type="password", key="su_pass")
            role = st.selectbox("Role", ["User","Librarian"], key="su_role")
            if st.button("Create Account"):
                ok,msg = signup_user(name,mobile,email,password,role)
                if ok:
                    st.success(msg + " You can now login.")
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
                    st.success(f"Welcome {user['name']} — redirecting to dashboard...")
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials. (Demo accounts: see note above.)")

        st.stop()  # stop further UI until logged in

    # At this point we have a logged-in user
    user = st.session_state['user']
    # Sidebar
    st.sidebar.markdown(f"### 👤 {user['name']}")
    st.sidebar.markdown(f"**Role:** {user['role']}")
    st.sidebar.markdown("---")

    # Notifications
    notes = compute_notifications_for_user(user['email'])
    if notes:
        st.sidebar.markdown("#### 🔔 Notifications")
        for n in notes:
            st.sidebar.write(n)
        st.sidebar.markdown("---")

    # Chatbot widget in sidebar
    st.sidebar.markdown("### 🤖 Chatbot Librarian")
    chat_query = st.sidebar.text_input("Ask me (e.g. 'Recommend Python books')", key="chat_query")
    if st.sidebar.button("Ask", key="ask_btn"):
        if chat_query.strip():
            resp = chatbot_response(user['email'], chat_query)
            st.sidebar.info(resp)

    # main navigation based on role
    if user['role'] == "User":
        page = st.sidebar.radio("Navigate", ["Dashboard","All Books","Favorites","Issued Books","Recommendations","Account","Logout"])
    else:
        page = st.sidebar.radio("Navigate", ["Dashboard","All Books","Add Book","Delete Book","Issued Overview","Account","Logout"])

    # ---- Pages ----
    if page == "Logout":
        st.session_state.clear()
        st.experimental_rerun()

    if page == "Dashboard":
        st.header("📊 Dashboard")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Your Summary")
            # favorites count
            users = get_users()
            u = next((x for x in users if x['email'].lower() == user['email'].lower()), None)
            fav_count = len(u.get('favorites', [])) if u else 0
            issued_count = len(user_active_issues(user['email']))
            st.write(f"- ⭐ Favorites: **{fav_count}**")
            st.write(f"- 📥 Active borrowed books: **{issued_count}**")
        with col2:
            st.subheader("Quick Actions")
            if st.button("Browse All Books"):
                page = "All Books"
                st.experimental_rerun()
            if st.button("View Recommendations"):
                page = "Recommendations"
                st.experimental_rerun()

    elif page == "All Books":
        st.header("📚 All Books")
        all_books = get_books()
        # simple search & filter
        q = st.text_input("Search by title / author / genre (press Enter)", key="search_q")
        filtered = all_books
        if q:
            ql = q.lower()
            filtered = [b for b in all_books if ql in b.get('title','').lower() or ql in b.get('author','').lower() or any(ql in g.lower() for g in b.get('genre',[]))]
        # grid display
        for b in filtered:
            book_card(b, user)
            st.divider()
        # handle book overview popup
        if st.session_state.get('view_book'):
            bid = st.session_state.pop('view_book')
            book = next((x for x in all_books if x['id'] == bid), None)
            if book:
                st.markdown("---")
                st.subheader(f"📖 {book['title']} — Overview")
                left, right = st.columns([1,2])
                with left:
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
                    for i, ch in enumerate(book.get('index',[]),1):
                        st.write(f"{i}. {ch}")

    elif page == "Favorites":
        st.header("⭐ Your Favorites")
        users = get_users()
        u = next((x for x in users if x['email'].lower() == user['email'].lower()), {})
        fav_ids = u.get('favorites', [])
        if not fav_ids:
            st.info("No favorites yet. Add from All Books.")
        else:
            for bid in fav_ids:
                b = next((x for x in get_books() if x['id'] == bid), None)
                if b:
                    st.write(f"**{b['title']}** — {b['author']}")
                    c1,c2 = st.columns([1,4])
                    with c1:
                        try:
                            st.image(b['cover_url'], width=80)
                        except Exception:
                            st.write("[Img]")
                    with c2:
                        if b.get('available', False) and st.button(f"Issue {b['id']}", key=f"favissue_{b['id']}"):
                            ok,msg = issue_book_to_user(user['email'], b['id'])
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
                            st.experimental_rerun()
                        if st.button(f"Remove favorite {b['id']}", key=f"rmfav_{b['id']}"):
                            users = get_users()
                            for uu in users:
                                if uu['email'].lower() == user['email'].lower():
                                    uu['favorites'] = [x for x in uu.get('favorites',[]) if x != b['id']]
                                    save_users(users)
                                    st.success("Removed from favorites.")
                                    st.experimental_rerun()

    elif page == "Issued Books":
        st.header("📥 Issued Books — Your Records")
        issued = user_active_issues(user['email'])
        if not issued:
            st.info("No active issued books.")
        else:
            for rec in issued:
                book = next((b for b in get_books() if b['id'] == rec['book_id']), None)
                if not book:
                    continue
                st.markdown(f"**{book['title']}** by {book['author']}")
                st.write(f"Issue Date: {rec['issue_date']}  |  Due Date: {rec['due_date']}")
                fine = calculate_fine_for_record(rec)
                if fine > 0:
                    st.error(f"Overdue — Current fine ₹{fine}")
                else:
                    due = datetime.fromisoformat(rec['due_date']).date()
                    st.info(f"Days left: {(due - date.today()).days} day(s)")
                if st.button(f"Return {book['title']}", key=f"return_{rec['book_id']}"):
                    ok,msg,fine_amt = return_book_from_user(user['email'], rec['book_id'])
                    if ok:
                        if fine_amt > 0:
                            st.warning(f"Returned. Please pay fine: ₹{fine_amt}")
                        else:
                            st.success("Returned successfully. No fine.")
                    else:
                        st.error(msg)
                    st.experimental_rerun()

    elif page == "Recommendations":
        st.header("🎯 Recommended for you")
        recs = recommend_for_user(user['email'])
        if not recs:
            st.info("No recommendations yet. Borrow a book to get personalized suggestions.")
        else:
            for r in recs:
                st.write(f"**{r['title']}** — {r['author']} (Available: {'Yes' if r.get('available') else 'No'})")
                if st.button(f"Issue {r['id']}", key=f"rec_issue_{r['id']}"):
                    ok,msg = issue_book_to_user(user['email'], r['id'])
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.experimental_rerun()

    elif page == "Account":
        st.header("⚙️ Account")
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Mobile:** {user['mobile']}")
        st.write(f"**Role:** {user['role']}")
        st.write("**Password:** (hidden for security)")
        if st.button("Delete my account"):
            # Simple deletion (demo); remove user (and do not cascade)
            users = get_users()
            users = [u for u in users if u['email'].lower() != user['email'].lower()]
            save_users(users)
            st.success("Account deleted. Refreshing...")
            st.session_state.clear()
            st.experimental_rerun()

    # ----- Librarian pages -----
    elif page == "Add Book" and user['role'] == "Librarian":
        st.header("➕ Add New Book (Librarian)")
        with st.form("add_book_form"):
            title = st.text_input("Title")
            author = st.text_input("Author")
            cover_url = st.text_input("Cover URL")
            description = st.text_area("Description")
            genre = st.text_input("Genres (comma separated)")
            keywords = st.text_input("Keywords (comma separated)")
            added_index = st.text_area("Index / Table of contents (one per line)")
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
                    "index": [x.strip() for x in added_index.splitlines() if x.strip()],
                    "genre": [g.strip() for g in genre.split(",") if g.strip()],
                    "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
                    "available": True,
                    "added_on": str(date.today())
                })
                save_books(books)
                st.success("Book added successfully.")
                st.experimental_rerun()

    elif page == "Delete Book" and user['role'] == "Librarian":
        st.header("🗑 Delete Book (Librarian)")
        books = get_books()
        if not books:
            st.info("No books to delete.")
        else:
            to_delete = st.selectbox("Select book to delete", [f"{b['id']} - {b['title']}" for b in books])
            if st.button("Delete selected book"):
                bid = int(to_delete.split(" - ")[0])
                books = [b for b in books if b['id'] != bid]
                save_books(books)
                st.success("Book deleted.")
                st.experimental_rerun()

    elif page == "Issued Overview" and user['role'] == "Librarian":
        st.header("📋 Issued Books Overview (All Users)")
        issued = get_issued()
        if not issued:
            st.info("No issued books recorded.")
        else:
            for rec in issued:
                book = next((b for b in get_books() if b['id'] == rec['book_id']), None)
                st.write(f"**{book['title'] if book else 'Unknown'}** — Borrower: {rec['user_email']}")
                st.write(f"Issue: {rec['issue_date']}  |  Due: {rec['due_date']}  |  Returned: {'Yes' if rec['returned'] else 'No'}")
                if not rec['returned']:
                    fine_now = calculate_fine_for_record(rec)
                    if fine_now > 0:
                        st.error(f"Fine: ₹{fine_now}")

if __name__ == "__main__":
    app()

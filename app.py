# app.py
import streamlit as st
from pathlib import Path
import json, hashlib, datetime, uuid, os, shutil, time
from typing import List, Dict

st.set_page_config(page_title="Smart Library", page_icon="📚", layout="wide")

# -------------------- File paths --------------------
USER_FILE = "users.json"
BOOK_FILE = "books.json"
ISSUED_FILE = "issued_books.json"

# -------------------- Safe JSON helpers --------------------
def safe_save_json(path: str, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def safe_load_json(path: str, default):
    """
    Load JSON from path. If file missing or empty or corrupt, create file with default and return default.
    If corrupt, back up the original file to path + .backup.TIMESTAMP
    """
    p = Path(path)
    if not p.exists():
        safe_save_json(path, default)
        return default
    try:
        text = p.read_text(encoding="utf-8").strip()
        if text == "":
            # empty file -> write default
            safe_save_json(path, default)
            return default
        return json.loads(text)
    except (json.JSONDecodeError, ValueError) as e:
        # backup corrupt file
        try:
            bak = f"{path}.backup.{int(time.time())}"
            shutil.move(path, bak)
            # write clean file
            safe_save_json(path, default)
            st.warning(f"Found corrupt JSON at `{path}`. Backed up to `{bak}` and recreated default file.")
        except Exception:
            # if backup fails, still try to recreate file
            safe_save_json(path, default)
            st.warning(f"Found corrupt JSON at `{path}`. Recreated default file (backup failed).")
        return default

# -------------------- Init files & sample data --------------------
def create_sample_data_if_missing():
    users = safe_load_json(USER_FILE, [])
    books = safe_load_json(BOOK_FILE, [])
    issued = safe_load_json(ISSUED_FILE, [])

    created = False
    if not users:
        # create a sample librarian (email: librarian@example.com, password: admin123)
        sample_admin = {
            "name": "Admin Librarian",
            "mobile": "9999999999",
            "email": "librarian@example.com",
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "Librarian",
            "favorites": [],
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        users = [sample_admin]
        safe_save_json(USER_FILE, users)
        st.info("Sample librarian created: email `librarian@example.com`, password `admin123` (change after login).")
        created = True

    if not books:
        sample_books = [
            {
                "id": "B001",
                "title": "Python for Data Analysis",
                "author": "Wes McKinney",
                "cover": "https://m.media-amazon.com/images/I/51K8ouYrHeL._SX379_BO1,204,203,200_.jpg",
                "description": "Hands-on guide to data analysis in Python using pandas and NumPy.",
                "index": "Ch1: Python basics\nCh2: Data structures\nCh3: pandas essentials\nCh4: Time series",
                "tags": ["python", "data", "pandas"],
                "price": 599.0,
                "publisher": "O'Reilly",
                "isbn": "9781491957660",
                "pages": "550",
                "edition": "2nd",
                "language": "English",
                "rating": 4.4,
                "reviews": [],
                "available": True,
                "times_issued": 0,
                "created_at": datetime.datetime.utcnow().isoformat()
            },
            {
                "id": "B002",
                "title": "Introduction to Algorithms",
                "author": "Cormen, Leiserson, Rivest, Stein",
                "cover": "https://images-na.ssl-images-amazon.com/images/I/41as+WafrFL._SX258_BO1,204,203,200_.jpg",
                "description": "Comprehensive textbook on algorithms.",
                "index": "Ch1: Foundations\nCh2: Sorting\nCh3: Graph algorithms\nCh4: Dynamic Programming",
                "tags": ["algorithms", "cs"],
                "price": 899.0,
                "publisher": "MIT Press",
                "isbn": "9780262033848",
                "pages": "1312",
                "edition": "3rd",
                "language": "English",
                "rating": 4.6,
                "reviews": [],
                "available": True,
                "times_issued": 0,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
        ]
        safe_save_json(BOOK_FILE, sample_books)
        st.info("Sample books added to books.json.")
        created = True

    if not issued:
        safe_save_json(ISSUED_FILE, [])
        created = True

    return created

# Ensure files exist and create sample data if empty
safe_load_json(USER_FILE, [])
safe_load_json(BOOK_FILE, [])
safe_load_json(ISSUED_FILE, [])
create_sample_data_if_missing()

# -------------------- Utility functions --------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def find_user_by_email(email: str):
    users = safe_load_json(USER_FILE, [])
    for u in users:
        if u.get("email","").lower() == email.lower():
            return u
    return None

def update_user_in_file(user_obj: dict):
    users = safe_load_json(USER_FILE, [])
    for i,u in enumerate(users):
        if u.get("email","").lower() == user_obj.get("email","").lower():
            users[i] = user_obj
            safe_save_json(USER_FILE, users)
            return True
    # not found -> append
    users.append(user_obj)
    safe_save_json(USER_FILE, users)
    return True

# -------------------- Business logic --------------------
def signup(name, mobile, email, password, role):
    if not (name and email and password):
        return False, "Name, email and password are required."
    if find_user_by_email(email):
        return False, "Email already registered."
    user = {
        "name": name.strip(),
        "mobile": mobile.strip(),
        "email": email.strip().lower(),
        "password_hash": hash_password(password.strip()),
        "role": role,
        "favorites": [],
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    users = safe_load_json(USER_FILE, [])
    users.append(user)
    safe_save_json(USER_FILE, users)
    return True, user

def login(email, password):
    if not (email and password):
        return False, "Email and password required."
    u = find_user_by_email(email)
    if not u:
        return False, "No account with that email."
    if u.get("password_hash") != hash_password(password):
        return False, "Incorrect password."
    return True, u

# Book CRUD
def load_books() -> List[Dict]:
    return safe_load_json(BOOK_FILE, [])

def save_books(books: List[Dict]):
    safe_save_json(BOOK_FILE, books)

def add_book(book_id, title, author, cover, description, index_text, tags: List[str],
             price=None, publisher=None, isbn=None, pages=None, edition=None, language=None, rating=None):
    books = load_books()
    if any(b.get("id") == book_id for b in books):
        return False, "Book ID already exists."
    b = {
        "id": book_id,
        "title": title,
        "author": author,
        "cover": cover,
        "description": description,
        "index": index_text,
        "tags": tags,
        "price": price,
        "publisher": publisher,
        "isbn": isbn,
        "pages": pages,
        "edition": edition,
        "language": language,
        "rating": rating or 0.0,
        "reviews": [],
        "available": True,
        "times_issued": 0,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    books.append(b)
    save_books(books)
    return True, "Book added."

def edit_book(book_id, **fields):
    books = load_books()
    for i,b in enumerate(books):
        if b.get("id") == book_id:
            b.update(fields)
            books[i] = b
            save_books(books)
            return True, "Book updated."
    return False, "Book not found."

def delete_book(book_id):
    books = load_books()
    new_books = [b for b in books if b.get("id") != book_id]
    if len(new_books) == len(books):
        return False, "Book not found."
    save_books(new_books)
    # remove issued records for this book and remove from users' favorites
    issued = safe_load_json(ISSUED_FILE, [])
    issued = [r for r in issued if r.get("book_id") != book_id]
    safe_save_json(ISSUED_FILE, issued)
    users = safe_load_json(USER_FILE, [])
    changed = False
    for u in users:
        if book_id in u.get("favorites", []):
            u["favorites"].remove(book_id)
            changed = True
    if changed:
        safe_save_json(USER_FILE, users)
    return True, "Book deleted and references cleaned."

# Issue / Return
DEFAULT_LOAN_DAYS = 14

def issue_book(book_id, user_email, days=DEFAULT_LOAN_DAYS):
    books = load_books()
    book = next((b for b in books if b.get("id") == book_id), None)
    if not book:
        return False, "Book not found."
    if not book.get("available", True):
        return False, "Book currently checked out."
    rec = {
        "record_id": str(uuid.uuid4()),
        "book_id": book_id,
        "user_email": user_email.lower(),
        "issue_date": datetime.date.today().isoformat(),
        "deadline": (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
    }
    issued = safe_load_json(ISSUED_FILE, [])
    issued.append(rec)
    safe_save_json(ISSUED_FILE, issued)
    # mark book unavailable + increment
    book["available"] = False
    book["times_issued"] = book.get("times_issued", 0) + 1
    save_books(books)
    return True, rec

def return_book(record_id, user_email=None):
    issued = safe_load_json(ISSUED_FILE, [])
    rec = next((r for r in issued if r.get("record_id") == record_id), None)
    if not rec:
        return False, "Issue record not found."
    if user_email and rec.get("user_email","").lower() != user_email.lower():
        return False, "You are not the borrower for this record."
    # mark book available
    books = load_books()
    for b in books:
        if b.get("id") == rec.get("book_id"):
            b["available"] = True
    save_books(books)
    issued = [r for r in issued if r.get("record_id") != record_id]
    safe_save_json(ISSUED_FILE, issued)
    return True, "Returned successfully."

def get_user_issued(user_email=None):
    issued = safe_load_json(ISSUED_FILE, [])
    if user_email:
        return [r for r in issued if r.get("user_email","").lower() == user_email.lower()]
    return issued

# Favorites
def add_favorite(user_email, book_id):
    u = find_user_by_email(user_email)
    if not u:
        return False, "User not found."
    u.setdefault("favorites", [])
    if book_id in u["favorites"]:
        return False, "Already in your list."
    u["favorites"].append(book_id)
    update_user_in_file(u)
    return True, "Added to your book list."

def remove_favorite(user_email, book_id):
    u = find_user_by_email(user_email)
    if not u:
        return False, "User not found."
    if book_id in u.get("favorites", []):
        u["favorites"].remove(book_id)
        update_user_in_file(u)
        return True, "Removed from your list."
    return False, "Book not in your list."

# Recommendation (hybrid)
def recommend_for_user(user_email: str, top_n=6):
    books = load_books()
    issued = safe_load_json(ISSUED_FILE, [])
    pop = {b.get("id"): b.get("times_issued", 0) for b in books}
    if not user_email or not any(r.get("user_email","").lower() == user_email.lower() for r in issued):
        # return top popular available books
        candidates = [b for b in books if b.get("available", True)]
        candidates = sorted(candidates, key=lambda x: pop.get(x.get("id"),0), reverse=True)
        return candidates[:top_n]
    # user's last borrowed books
    user_recs = sorted([r for r in issued if r.get("user_email","").lower()==user_email.lower()],
                       key=lambda x: x.get("issue_date",""))
    last_ids = [r.get("book_id") for r in user_recs[-3:]]
    last_books = [b for b in books if b.get("id") in last_ids]
    last_authors = set([b.get("author","").lower() for b in last_books if b.get("author")])
    last_tags = set()
    for b in last_books:
        for t in b.get("tags", []):
            last_tags.add(t.lower())
    scores = []
    for b in books:
        if b.get("id") in last_ids:
            continue
        score = 0.0
        if b.get("author") and b.get("author","").lower() in last_authors:
            score += 6.0
        tag_overlap = len(set([t.lower() for t in b.get("tags", [])]) & last_tags)
        score += 2.0 * tag_overlap
        score += pop.get(b.get("id"),0) / 5.0
        if b.get("available", True):
            score += 1.0
        scores.append((score, b))
    scores.sort(key=lambda x: x[0], reverse=True)
    recs = [b for s,b in scores][:top_n]
    if len(recs) < top_n:
        extra = [b for b in sorted(books, key=lambda x: pop.get(x.get("id"),0), reverse=True) if b not in recs and b.get("id") not in last_ids]
        recs += extra[:(top_n-len(recs))]
    return recs[:top_n]

# -------------------- UI Helpers --------------------
def days_left(deadline_iso: str) -> int:
    try:
        d = datetime.date.fromisoformat(deadline_iso)
        return (d - datetime.date.today()).days
    except Exception:
        return 0

def safe_image(url, width=150):
    try:
        st.image(url, width=width)
    except Exception:
        st.image("https://via.placeholder.com/150x220.png?text=No+Cover", width=width)

def show_rating_stars(rating: float, max_stars=5):
    try:
        r = float(rating)
    except:
        r = 0.0
    full = int(round(r))
    full = min(max(full,0), max_stars)
    stars = "★" * full + "☆" * (max_stars - full)
    return f"{stars} ({r:.1f})"

def book_card(book: dict, user=None):
    left, right = st.columns([1,3])
    with left:
        safe_image(book.get("cover"), width=150)
    with right:
        st.markdown(f"### {book.get('title')}")
        st.markdown(f"**Author:** {book.get('author','-')}  \n**Book ID:** `{book.get('id')}`")
        if book.get("price") is not None:
            st.markdown(f"**Price:** ₹{book.get('price')}")
        if book.get("rating"):
            st.markdown(f"**Rating:** {show_rating_stars(book.get('rating'))} • {len(book.get('reviews',[]))} reviews")
        st.markdown(f"**Availability:** {'Available' if book.get('available', True) else 'Checked out'}")
        st.write(book.get("description","_No description available._")[:240] + ("..." if len(book.get("description",""))>240 else ""))
        c1,c2,c3,c4 = st.columns([1,1,1,1])
        if c1.button("View Details", key=f"detail_{book['id']}"):
            st.session_state.page = "book_detail"
            st.session_state.book_id = book["id"]
            st.experimental_rerun()
        if user:
            if book.get("id") in user.get("favorites",[]):
                if c2.button("★ Favorited", key=f"favrem_{book['id']}"):
                    remove_favorite(user["email"], book["id"])
                    st.session_state.user = find_user_by_email(user["email"])
                    st.experimental_rerun()
            else:
                if c2.button("☆ Add to List", key=f"favadd_{book['id']}"):
                    add_favorite(user["email"], book["id"])
                    st.session_state.user = find_user_by_email(user["email"])
                    st.experimental_rerun()
            if user.get("role") != "Librarian":
                if book.get("available", True):
                    if c3.button("📚 Issue Book", key=f"issue_{book['id']}"):
                        ok, resp = issue_book(book["id"], user["email"])
                        if ok:
                            st.success(f"Issued — due {resp.get('deadline')}")
                        else:
                            st.error(resp)
                        st.experimental_rerun()
            else:
                # Librarian action placeholders
                if c3.button("✏ Edit", key=f"edit_{book['id']}"):
                    st.session_state.edit_book_id = book["id"]
                    st.session_state.page = "librarian_edit"
                    st.experimental_rerun()
                if c4.button("🗑 Delete", key=f"del_{book['id']}"):
                    ok,msg = delete_book(book["id"])
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.experimental_rerun()
        else:
            c2.info("Login to issue / save")
    st.write("---")

# -------------------- App state init --------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "book_id" not in st.session_state:
    st.session_state.book_id = None
if "edit_book_id" not in st.session_state:
    st.session_state.edit_book_id = None

# -------------------- Header --------------------
st.markdown("<h1 style='margin-bottom:0.1rem'>📚 Smart Library</h1>", unsafe_allow_html=True)
st.markdown("<div style='color:#6c757d;margin-top:0;'>A role-based Streamlit library with book detail pages & hybrid recommendations</div>", unsafe_allow_html=True)
st.write("---")

# -------------------- Sidebar Nav (dynamic) --------------------
def get_nav_options():
    if st.session_state.user:
        options = ["Home", "My Favorites", "My Issued Books", "Recommendations", "About"]
        if st.session_state.user.get("role") == "Librarian":
            options.insert(1, "Librarian Console")
        return options
    else:
        return ["Home", "Login", "Sign Up", "About"]

nav_options = get_nav_options()
# keep previous page selection if valid
if st.session_state.page not in nav_options:
    st.session_state.page = nav_options[0]
choice = st.sidebar.selectbox("Navigation", nav_options, index=nav_options.index(st.session_state.page))
st.session_state.page = choice

# profile / logout
if st.session_state.user:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Signed in as**  \n{st.session_state.user['name']}  \n{st.session_state.user['email']}  \n**Role:** {st.session_state.user['role']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "Home"
        st.experimental_rerun()

# -------------------- Pages --------------------
def page_home():
    st.subheader("Library Home")
    books = load_books()
    q_col, s_col = st.columns([3,1])
    with q_col:
        q = st.text_input("Search by title, author, tag or id")
    with s_col:
        avail_filter = st.selectbox("Availability", ["All","Available only","Checked out only"])
    filtered = []
    for b in books:
        text = " ".join([str(b.get(k,"")).lower() for k in ("title","author","id")]) + " " + " ".join([t.lower() for t in b.get("tags",[])])
        if q and q.strip().lower() not in text:
            continue
        if avail_filter == "Available only" and not b.get("available",True):
            continue
        if avail_filter == "Checked out only" and b.get("available",True):
            continue
        filtered.append(b)
    st.write(f"Found **{len(filtered)}** books")
    for b in filtered:
        book_card(b, st.session_state.user)

def page_login():
    st.subheader("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            ok, resp = login(email, password)
            if ok:
                st.session_state.user = resp
                st.session_state.page = "Home"   # redirect to home
                st.success(f"Welcome back, {resp.get('name')} — redirected to Home.")
                st.experimental_rerun()
            else:
                st.error(resp)

def page_signup():
    st.subheader("Create account")
    with st.form("signup_form"):
        name = st.text_input("Full name")
        mobile = st.text_input("Mobile number")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["User", "Librarian"])
        submitted = st.form_submit_button("Create account")
        if submitted:
            ok, resp = signup(name, mobile, email, password, role)
            if ok:
                # auto-login and redirect
                st.session_state.user = resp
                st.session_state.page = "Home"
                st.success("Account created and logged in — redirected to Home.")
                st.experimental_rerun()
            else:
                st.error(resp)

def page_about():
    st.subheader("About")
    st.write("""
    Smart Library — Features:
    - Role-based authentication (User / Librarian)
    - View all books with cover, details, and index
    - Librarian: Add, Edit, Delete books
    - Users: Add to book list (favorites), Issue & Return books
    - Issued book tracking with deadline & days-left
    - Book detail page (Flipkart-like): cover, price, rating, publisher, ISBN, pages, edition, language, description, index, reviews
    - Hybrid recommender: author + tags + popularity + availability
    - Safe JSON handling: no crash if files are empty or corrupted.
    """)

def page_my_favorites():
    if not st.session_state.user:
        st.warning("Please login to view your book list.")
        return
    st.subheader("My Book List (Favorites)")
    favs = st.session_state.user.get("favorites", [])
    books_dict = {b.get("id"):b for b in load_books()}
    if not favs:
        st.info("No books saved. Browse Home and add books to your list.")
        return
    for fid in favs:
        b = books_dict.get(fid)
        if b:
            book_card(b, st.session_state.user)

def page_my_issued():
    if not st.session_state.user:
        st.warning("Please login to view your issued books.")
        return
    st.subheader("My Issued Books")
    issued = get_user_issued(st.session_state.user["email"])
    if not issued:
        st.info("You have no issued books.")
        return
    books = {b.get("id"):b for b in load_books()}
    for rec in issued:
        b = books.get(rec.get("book_id"), {})
        left = days_left(rec.get("deadline",""))
        col1,col2 = st.columns([3,1])
        with col1:
            st.markdown(f"**{b.get('title','-')}** by {b.get('author','-')}")
            st.write(f"Issued: {rec.get('issue_date')} • Due: {rec.get('deadline')} • Days left: {left}")
        with col2:
            if st.button("Return Book", key=f"return_{rec.get('record_id')}"):
                ok,msg = return_book(rec.get('record_id'), st.session_state.user["email"])
                if ok:
                    st.success(msg)
                    # refresh user issued listing
                    st.experimental_rerun()
                else:
                    st.error(msg)

def page_recommendations():
    if not st.session_state.user:
        st.warning("Please login to view personalized recommendations.")
        return
    st.subheader("Recommended for you")
    recs = recommend_for_user(st.session_state.user["email"], top_n=8)
    if not recs:
        st.info("No recommendations available yet.")
        return
    for b in recs:
        book_card(b, st.session_state.user)

def page_book_detail():
    bid = st.session_state.book_id
    if not bid:
        st.info("No book selected.")
        return
    book = next((b for b in load_books() if b.get("id")==bid), None)
    if not book:
        st.error("Book not found.")
        return
    left,right = st.columns([1,2])
    with left:
        safe_image(book.get("cover"), width=300)
        if book.get("price") is not None:
            st.markdown(f"### ₹{book.get('price')}")
        st.markdown(f"**Availability:** {'Available' if book.get('available',True) else 'Checked out'}")
        if st.session_state.user:
            if book.get("id") in st.session_state.user.get("favorites",[]):
                if st.button("★ Favorited (Remove)"):
                    remove_favorite(st.session_state.user["email"], book["id"])
                    st.session_state.user = find_user_by_email(st.session_state.user["email"])
                    st.experimental_rerun()
            else:
                if st.button("☆ Add to Book List"):
                    add_favorite(st.session_state.user["email"], book["id"])
                    st.session_state.user = find_user_by_email(st.session_state.user["email"])
                    st.experimental_rerun()
            if st.session_state.user.get("role") != "Librarian":
                if book.get("available", True):
                    if st.button("📚 Issue This Book"):
                        ok, resp = issue_book(book["id"], st.session_state.user["email"])
                        if ok:
                            st.success(f"Issued — due {resp.get('deadline')}")
                        else:
                            st.error(resp)
                        st.experimental_rerun()
            else:
                if st.button("✏ Edit Book (Console)"):
                    st.session_state.edit_book_id = book["id"]
                    st.session_state.page = "Librarian Console"
                    st.experimental_rerun()
    with right:
        st.markdown(f"## {book.get('title')}")
        st.markdown(f"**Author:** {book.get('author','-')}")
        meta = []
        if book.get("publisher"): meta.append(f"Publisher: {book.get('publisher')}")
        if book.get("isbn"): meta.append(f"ISBN: {book.get('isbn')}")
        if book.get("pages"): meta.append(f"{book.get('pages')} pages")
        if book.get("edition"): meta.append(f"Edition: {book.get('edition')}")
        if book.get("language"): meta.append(f"Language: {book.get('language')}")
        if meta:
            st.markdown(" • ".join(meta))
        st.write("---")
        st.subheader("Description")
        st.write(book.get("description","_No description provided._"))
        st.subheader("Index / Overview")
        st.write(book.get("index","_No index provided._"))
        st.write("---")
        st.subheader("Reviews")
        if book.get("reviews"):
            for r in book.get("reviews"):
                st.markdown(f"**{r.get('user','Anon')}** — {show_rating_stars(r.get('rating',0))} • {r.get('date')}")
                st.write(r.get("comment",""))
                st.write("---")
        else:
            st.info("No reviews yet for this book.")
    st.subheader("Related / Recommended")
    # show same-author first
    same_author = [b for b in load_books() if b.get("author","").lower()==book.get("author","").lower() and b.get("id")!=book.get("id")]
    shown = 0
    if same_author:
        for sb in same_author[:3]:
            book_card(sb, st.session_state.user)
            shown += 1
    if shown < 6:
        recs = recommend_for_user(st.session_state.user["email"] if st.session_state.user else "", top_n=6)
        for rb in recs:
            if rb.get("id") != book.get("id") and shown < 6:
                book_card(rb, st.session_state.user)
                shown += 1

def page_librarian_console():
    if not st.session_state.user or st.session_state.user.get("role") != "Librarian":
        st.warning("Librarian access only.")
        return
    st.subheader("Librarian Console")
    mode = st.selectbox("Console Mode", ["Add Book","Edit Book","All Issued"])
    if mode == "Add Book":
        st.markdown("### Add a new book")
        with st.form("add_book_form"):
            book_id = st.text_input("Book ID", value=str(uuid.uuid4())[:8])
            title = st.text_input("Title")
            author = st.text_input("Author")
            cover = st.text_input("Cover Image URL")
            price = st.text_input("Price (₹)")
            publisher = st.text_input("Publisher")
            isbn = st.text_input("ISBN")
            pages = st.text_input("Pages")
            edition = st.text_input("Edition")
            language = st.text_input("Language")
            tags = st.text_input("Tags (comma separated)")
            rating = st.number_input("Rating (0-5)", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
            description = st.text_area("Short Description")
            index_text = st.text_area("Index / Overview")
            submitted = st.form_submit_button("Add Book")
            if submitted:
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                price_val = float(price) if price.strip() else None
                ok,msg = add_book(book_id.strip(), title.strip(), author.strip(), cover.strip(), description.strip(), index_text.strip(), tag_list,
                                 price=price_val, publisher=publisher.strip() or None, isbn=isbn.strip() or None, pages=pages.strip() or None,
                                 edition=edition.strip() or None, language=language.strip() or None, rating=rating)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
    elif mode == "Edit Book":
        st.markdown("### Edit book")
        books = load_books()
        if not books:
            st.info("No books to edit.")
            return
        key_map = {b.get("id"): f"{b.get('title')} — {b.get('author')}" for b in books}
        sel = st.selectbox("Select book", list(key_map.keys()), format_func=lambda x: key_map[x])
        book = next((b for b in books if b.get("id")==sel), None)
        if book:
            with st.form("edit_book_form"):
                title = st.text_input("Title", value=book.get("title",""))
                author = st.text_input("Author", value=book.get("author",""))
                cover = st.text_input("Cover URL", value=book.get("cover",""))
                price = st.text_input("Price", value=str(book.get("price") or ""))
                publisher = st.text_input("Publisher", value=book.get("publisher","") or "")
                isbn = st.text_input("ISBN", value=book.get("isbn","") or "")
                pages = st.text_input("Pages", value=book.get("pages","") or "")
                edition = st.text_input("Edition", value=book.get("edition","") or "")
                language = st.text_input("Language", value=book.get("language","") or "")
                tags = st.text_input("Tags (comma separated)", value=",".join(book.get("tags",[])))
                rating = st.number_input("Rating (0-5)", min_value=0.0, max_value=5.0, value=float(book.get("rating",0.0)), step=0.1)
                description = st.text_area("Description", value=book.get("description",""))
                index_text = st.text_area("Index / Overview", value=book.get("index",""))
                submitted = st.form_submit_button("Save Changes")
                if submitted:
                    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                    price_val = float(price) if price.strip() else None
                    ok,msg = edit_book(book.get("id"), title=title.strip(), author=author.strip(), cover=cover.strip(),
                                       price=price_val, publisher=publisher.strip() or None, isbn=isbn.strip() or None,
                                       pages=pages.strip() or None, edition=edition.strip() or None,
                                       language=language.strip() or None, tags=tag_list,
                                       rating=rating, description=description.strip(), index=index_text.strip())
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
    else:
        st.markdown("### All Issued Records")
        issued = get_user_issued()
        books = {b.get("id"):b for b in load_books()}
        if not issued:
            st.info("No issued records.")
            return
        for rec in issued:
            b = books.get(rec.get("book_id"), {})
            st.write(f"- **{b.get('title','-')}** | Borrower: {rec.get('user_email')} | Due: {rec.get('deadline')}")
            if st.button(f"Return {rec.get('record_id')}", key=f"libret_{rec.get('record_id')}"):
                ok,msg = return_book(rec.get('record_id'))
                if ok:
                    st.success("Returned")
                    st.experimental_rerun()
                else:
                    st.error(msg)

# Dispatch
page = st.session_state.page
if page == "Home":
    page_home()
elif page == "Login":
    page_login()
elif page == "Sign Up":
    page_signup()
elif page == "About":
    page_about()
elif page == "My Favorites":
    page_my_favorites()
elif page == "My Issued Books":
    page_my_issued()
elif page == "Recommendations":
    page_recommendations()
elif page == "book_detail":
    page_book_detail()
elif page == "Librarian Console":
    page_librarian_console()
elif page == "librarian_edit":
    page_librarian_console()
else:
    st.info("Page not implemented.")

# keep session user fresh
if st.session_state.user:
    st.session_state.user = find_user_by_email(st.session_state.user.get("email"))

# app.py
import streamlit as st
from pathlib import Path
import json, hashlib, datetime, uuid
from typing import List, Dict

st.set_page_config(page_title="Smart Library", page_icon="📚", layout="wide")

# -------------------- Files --------------------
USER_FILE = "users.json"
BOOK_FILE = "books.json"
ISSUED_FILE = "issued_books.json"

def ensure_file(path: str, default):
    p = Path(path)
    if not p.exists():
        p.write_text(json.dumps(default, indent=4, ensure_ascii=False))
    return path

ensure_file(USER_FILE, [])
ensure_file(BOOK_FILE, [])
ensure_file(ISSUED_FILE, [])

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# -------------------- Security & helpers --------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def find_user_by_email(email: str):
    users = load_json(USER_FILE)
    for u in users:
        if u["email"].lower() == email.lower():
            return u
    return None

def update_user(user_obj: dict):
    users = load_json(USER_FILE)
    for i,u in enumerate(users):
        if u["email"].lower() == user_obj["email"].lower():
            users[i] = user_obj
            save_json(USER_FILE, users)
            return True
    return False

# -------------------- User auth --------------------
def signup(name, mobile, email, password, role):
    if find_user_by_email(email):
        return False, "Email already registered."
    user = {
        "name": name,
        "mobile": mobile,
        "email": email.lower(),
        "password_hash": hash_password(password),
        "role": role,
        "favorites": [],
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    users = load_json(USER_FILE)
    users.append(user)
    save_json(USER_FILE, users)
    return True, user

def login(email, password):
    u = find_user_by_email(email)
    if not u:
        return False, "No account with that email."
    if u["password_hash"] != hash_password(password):
        return False, "Incorrect password."
    return True, u

# -------------------- Book CRUD & metadata --------------------
def load_books() -> List[Dict]:
    return load_json(BOOK_FILE)

def save_books(books: List[Dict]):
    save_json(BOOK_FILE, books)

def add_book(book_id, title, author, cover, description, index_text,
             tags: List[str], price=None, publisher=None, isbn=None,
             pages=None, edition=None, language=None, rating=None):
    books = load_books()
    if any(b["id"] == book_id for b in books):
        return False, "Book ID already exists."
    book = {
        "id": book_id,
        "title": title,
        "author": author,
        "cover": cover,
        "description": description,
        "index": index_text,
        "tags": tags,
        "available": True,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "times_issued": 0,
        # optional e-commerce-style fields:
        "price": price,
        "publisher": publisher,
        "isbn": isbn,
        "pages": pages,
        "edition": edition,
        "language": language,
        "rating": rating or 0.0,
        "reviews": []  # list of {"user","rating","comment","date"}
    }
    books.append(book)
    save_books(books)
    return True, "Book added."

def edit_book(book_id, **fields):
    books = load_books()
    for b in books:
        if b["id"] == book_id:
            b.update(fields)
            save_books(books)
            return True, "Book updated."
    return False, "Book not found."

def delete_book(book_id):
    books = load_books()
    new_books = [b for b in books if b["id"] != book_id]
    if len(new_books) == len(books):
        return False, "Book not found."
    save_books(new_books)
    # remove issued records and favorites referencing this book
    issued = load_json(ISSUED_FILE)
    issued = [i for i in issued if i["book_id"] != book_id]
    save_json(ISSUED_FILE, issued)
    users = load_json(USER_FILE)
    for u in users:
        if "favorites" in u and book_id in u["favorites"]:
            u["favorites"].remove(book_id)
    save_json(USER_FILE, users)
    return True, "Book deleted and references cleaned."

# -------------------- Issue / Return --------------------
DEFAULT_LOAN_DAYS = 14

def issue_book(book_id, user_email, days=DEFAULT_LOAN_DAYS):
    books = load_books()
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        return False, "Book not found."
    if not book.get("available", True):
        return False, "Book currently checked out."
    # create issue record
    issued = load_json(ISSUED_FILE)
    rec = {
        "record_id": str(uuid.uuid4()),
        "book_id": book_id,
        "user_email": user_email.lower(),
        "issue_date": datetime.date.today().isoformat(),
        "deadline": (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
    }
    issued.append(rec)
    save_json(ISSUED_FILE, issued)
    # update book
    book["available"] = False
    book["times_issued"] = book.get("times_issued", 0) + 1
    save_books(books)
    return True, rec

def return_book(record_id, user_email=None):
    issued = load_json(ISSUED_FILE)
    rec = next((r for r in issued if r["record_id"] == record_id), None)
    if not rec:
        return False, "Issue record not found."
    if user_email and rec["user_email"].lower() != user_email.lower():
        return False, "You are not the borrower for this record."
    # mark book available
    books = load_books()
    for b in books:
        if b["id"] == rec["book_id"]:
            b["available"] = True
    save_books(books)
    issued = [r for r in issued if r["record_id"] != record_id]
    save_json(ISSUED_FILE, issued)
    return True, "Returned successfully."

def get_user_issued(user_email=None):
    issued = load_json(ISSUED_FILE)
    if user_email:
        return [r for r in issued if r["user_email"].lower() == user_email.lower()]
    return issued

# -------------------- Favorites --------------------
def add_favorite(user_email, book_id):
    u = find_user_by_email(user_email)
    if not u:
        return False, "User not found."
    u.setdefault("favorites", [])
    if book_id in u["favorites"]:
        return False, "Already in your list."
    u["favorites"].append(book_id)
    update_user(u)
    return True, "Added to your book list."

def remove_favorite(user_email, book_id):
    u = find_user_by_email(user_email)
    if not u:
        return False, "User not found."
    if book_id in u.get("favorites", []):
        u["favorites"].remove(book_id)
        update_user(u)
        return True, "Removed from your list."
    return False, "Book not in your list."

# -------------------- Recommendation (hybrid) --------------------
def recommend_for_user(user_email: str, top_n=6):
    """
    Hybrid recommender:
    - if user has history: score by author match (+5), tag overlap (+2 per tag), popularity (times_issued/5),
      availability (+1)
    - else: return most popular available books
    """
    books = load_books()
    issued = load_json(ISSUED_FILE)
    user_history = [r["book_id"] for r in issued if r["user_email"].lower() == user_email.lower()]
    # popularity map
    pop = {b["id"]: b.get("times_issued", 0) for b in books}
    if not user_history:
        # recommend popular available books
        candidates = [b for b in books if b.get("available", True)]
        candidates = sorted(candidates, key=lambda x: pop.get(x["id"],0), reverse=True)
        return candidates[:top_n]
    # gather last borrowed (most recent)
    # sort user's issued records by issue_date
    user_recs = sorted([r for r in issued if r["user_email"].lower()==user_email.lower()],
                       key=lambda x: x["issue_date"])
    last_ids = [r["book_id"] for r in user_recs[-3:]]  # last 3
    last_books = [b for b in books if b["id"] in last_ids]
    last_authors = set([b["author"].lower() for b in last_books if b.get("author")])
    last_tags = set()
    for b in last_books:
        for t in b.get("tags", []):
            last_tags.add(t.lower())
    scores = []
    for b in books:
        if b["id"] in last_ids:
            continue  # deprioritize already-read items
        score = 0.0
        if b.get("author") and b["author"].lower() in last_authors:
            score += 6.0
        # tag overlap
        tag_overlap = len(set([t.lower() for t in b.get("tags", [])]) & last_tags)
        score += 2.0 * tag_overlap
        # popularity
        score += pop.get(b["id"], 0) / 5.0
        # availability
        if b.get("available", True):
            score += 1.0
        # small boost if created recently
        score += 0.01 * (1 if b.get("created_at") else 0)
        scores.append((score, b))
    scores.sort(key=lambda x: x[0], reverse=True)
    recommended = [b for s,b in scores][:top_n]
    # if not enough, fill with popular available
    if len(recommended) < top_n:
        extra = [b for b in sorted(books, key=lambda x: pop.get(x["id"],0), reverse=True) if b not in recommended and b["id"] not in last_ids]
        recommended += extra[:(top_n-len(recommended))]
    return recommended[:top_n]

# -------------------- UI Helpers --------------------
def days_left(deadline_iso: str) -> int:
    try:
        d = datetime.date.fromisoformat(deadline_iso)
        return (d - datetime.date.today()).days
    except:
        return 0

def show_rating_stars(rating: float, max_stars=5):
    """Return star string for display (rounded to 1 decimal)"""
    full = int(round(rating))
    stars = "★" * full + "☆" * (max_stars - full)
    return f"{stars} ({rating:.1f})"

def safe_image(url, width=150):
    try:
        st.image(url, width=width)
    except:
        st.image("https://via.placeholder.com/150x220.png?text=No+Cover", width=width)

def book_card(book: dict, user=None):
    # E-commerce-like compact card
    left, right = st.columns([1,3])
    with left:
        safe_image(book.get("cover"), width=150)
    with right:
        st.markdown(f"### {book.get('title')}")
        st.markdown(f"**Author:** {book.get('author','-')}  \n**Book ID:** `{book.get('id')}`")
        # show price if exists
        if book.get("price") is not None:
            st.markdown(f"**Price:** ₹{book.get('price')}")
        if book.get("rating"):
            st.markdown(f"**Rating:** {show_rating_stars(float(book.get('rating',0)))}  • {len(book.get('reviews',[]))} reviews")
        st.markdown(f"**Availability:** {'Available' if book.get('available', True) else 'Checked out'}")
        st.write(book.get("description","_No description available._")[:240] + ("..." if len(book.get("description",""))>240 else ""))
        # buttons
        c1,c2,c3,c4 = st.columns([1,1,1,1])
        if c1.button("View Details", key=f"detail_{book['id']}"):
            st.session_state.page = "book_detail"
            st.session_state.book_id = book["id"]
            st.experimental_rerun()
        if user:
            if book.get("id") in user.get("favorites",[]):
                if c2.button("★ Favorited", key=f"favrem_{book['id']}"):
                    remove_favorite(user["email"], book["id"])
                    st.experimental_rerun()
            else:
                if c2.button("☆ Add to List", key=f"favadd_{book['id']}"):
                    add_favorite(user["email"], book["id"])
                    st.experimental_rerun()
            if user.get("role") != "Librarian":
                if book.get("available", True):
                    if c3.button("📚 Issue Book", key=f"issue_{book['id']}"):
                        ok, resp = issue_book(book["id"], user["email"])
                        if ok:
                            st.success(f"Issued — due {resp['deadline']}")
                        else:
                            st.error(resp)
                        st.experimental_rerun()
                else:
                    c3.write("")
            # Librarian edit/delete
            if user.get("role") == "Librarian":
                if c4.button("✏ Edit", key=f"edit_{book['id']}"):
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

# -------------------- App State --------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "book_id" not in st.session_state:
    st.session_state.book_id = None
if "edit_book_id" not in st.session_state:
    st.session_state.edit_book_id = None

# -------------------- Top Header --------------------
st.markdown("<h1 style='margin-bottom:0.1rem'>📚 Smart Library</h1>", unsafe_allow_html=True)
st.markdown("<div style='color:#6c757d;margin-top:0;'>A role-based Streamlit library with rich book pages & hybrid recommendations</div>", unsafe_allow_html=True)
st.write("----")

# -------------------- Sidebar Nav (dynamic) --------------------
if st.session_state.user:
    # logged in nav (hide login/sign-up)
    nav_options = ["Home", "My Favorites", "My Issued Books", "Recommendations", "About"]
    if st.session_state.user.get("role") == "Librarian":
        nav_options.insert(1, "Librarian Console")
else:
    nav_options = ["Home", "Login", "Sign Up", "About"]

choice = st.sidebar.selectbox("Navigation", nav_options, index=nav_options.index(st.session_state.page) if st.session_state.page in nav_options else 0)
st.session_state.page = choice

# quick profile / logout panel
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
    # simple search/filter bar
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
        submit = st.form_submit_button("Login")
        if submit:
            ok, resp = login(email, password)
            if ok:
                st.session_state.user = resp
                st.session_state.page = "Home"   # redirect to home immediately
                st.success(f"Welcome back, {resp['name']} — redirecting to Home")
                st.experimental_rerun()
            else:
                st.error(resp)

def page_signup():
    st.subheader("Create Account")
    with st.form("signup_form"):
        name = st.text_input("Full name")
        mobile = st.text_input("Mobile number")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Student", "Librarian", "Other"])
        submit = st.form_submit_button("Sign Up")
        if submit:
            ok, resp = signup(name, mobile, email, password, role)
            if ok:
                # auto-login after sign up and redirect to Home
                st.session_state.user = resp
                st.session_state.page = "Home"
                st.success("Account created and logged in — redirecting to Home")
                st.experimental_rerun()
            else:
                st.error(resp)

def page_about():
    st.subheader("About")
    st.write("""
    Smart Library — features:
    - Role-based login (Student / Librarian / Other)
    - Rich book page (like e-commerce) with cover, price, rating, publisher, ISBN, pages, edition, language, description, index, reviews
    - Add/delete books (Librarian only)
    - Add to book list (favorites), Issue & Return books with deadlines
    - Issued book tracking, days-left calculation
    - Hybrid recommendation engine (author + tags + popularity + availability)
    - Persisted JSON backend for small deployments (replace with SQLite for production)
    """)

def page_my_favorites():
    if not st.session_state.user:
        st.warning("Please login to view your favorites.")
        return
    st.subheader("My Book List (Favorites)")
    favs = st.session_state.user.get("favorites", [])
    books = {b["id"]: b for b in load_books()}
    if not favs:
        st.info("No books saved. Browse Home and add books to your list.")
        return
    for fid in favs:
        b = books.get(fid)
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
    books = {b["id"]: b for b in load_books()}
    for rec in issued:
        b = books.get(rec["book_id"], {})
        left = days_left(rec["deadline"])
        col1,col2 = st.columns([3,1])
        with col1:
            st.markdown(f"**{b.get('title','-')}** by {b.get('author','-')}")
            st.write(f"Issued: {rec['issue_date']} • Due: {rec['deadline']} • Days left: {left}")
        with col2:
            if st.button("Return Book", key=f"return_{rec['record_id']}"):
                ok,msg = return_book(rec['record_id'], st.session_state.user["email"])
                if ok:
                    st.success(msg)
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
    book_id = st.session_state.book_id
    if not book_id:
        st.info("No book selected.")
        return
    books = load_books()
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        st.error("Book not found.")
        return
    # layout like product page
    left, right = st.columns([1,2])
    with left:
        safe_image(book.get("cover"), width=300)
        if book.get("price") is not None:
            st.markdown(f"### ₹{book.get('price')}")
        st.markdown(f"**Availability:** {'Available' if book.get('available',True) else 'Checked out'}")
        if book.get("rating"):
            st.markdown(f"**Rating:** {show_rating_stars(float(book.get('rating',0)))} • {len(book.get('reviews',[]))} reviews")
        st.write("---")
        if st.session_state.user:
            if book.get("id") in st.session_state.user.get("favorites",[]):
                if st.button("★ Favorited (Remove)", key="detail_fav_remove"):
                    remove_favorite(st.session_state.user["email"], book["id"])
                    st.session_state.user = find_user_by_email(st.session_state.user["email"])
                    st.experimental_rerun()
            else:
                if st.button("☆ Add to Book List", key="detail_fav_add"):
                    add_favorite(st.session_state.user["email"], book["id"])
                    st.session_state.user = find_user_by_email(st.session_state.user["email"])
                    st.success("Added to your book list.")
                    st.experimental_rerun()
            if st.session_state.user.get("role") != "Librarian":
                if book.get("available",True):
                    if st.button("📚 Issue This Book", key="detail_issue"):
                        ok, resp = issue_book(book["id"], st.session_state.user["email"])
                        if ok:
                            st.success(f"Issued — due {resp['deadline']}")
                        else:
                            st.error(resp)
                        st.experimental_rerun()
            if st.session_state.user.get("role") == "Librarian":
                if st.button("✏ Edit Book (sidebar)", key="detail_edit"):
                    st.session_state.edit_book_id = book["id"]
                    st.session_state.page = "librarian_edit"
                    st.experimental_rerun()
    with right:
        st.markdown(f"## {book.get('title')}")
        st.markdown(f"**Author:** {book.get('author','-')}")
        # e-commerce metadata
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
        st.subheader("Customer-style Reviews")
        if book.get("reviews"):
            for r in book.get("reviews"):
                st.markdown(f"**{r.get('user','Anon')}** — {show_rating_stars(float(r.get('rating',0)))} • {r.get('date')}")
                st.write(r.get("comment",""))
                st.write("---")
        else:
            st.info("No reviews yet for this book.")
    # Related books by recommender
    st.subheader("Related / Recommended")
    rels = recommend_for_user(st.session_state.user["email"], top_n=6) if st.session_state.user else recommend_for_user("", top_n=6)
    # try to show books with same author first
    same_author = [b for b in load_books() if b.get("author","").lower() == book.get("author","").lower() and b["id"] != book["id"]]
    shown = 0
    if same_author:
        for sb in same_author[:4]:
            book_card(sb, st.session_state.user)
            shown += 1
    if shown < 4:
        for rb in rels:
            if rb["id"] != book["id"] and shown < 6:
                book_card(rb, st.session_state.user)
                shown += 1

def page_librarian_console():
    if not st.session_state.user or st.session_state.user.get("role") != "Librarian":
        st.warning("Librarian access only.")
        return
    st.subheader("Librarian Console")
    mode = st.sidebar.selectbox("Console Mode", ["Add Book", "All Issued", "Edit Book"])
    if mode == "Add Book":
        st.markdown("## Add a new book")
        with st.form("add_book_form"):
            book_id = st.text_input("Book ID", value=str(uuid.uuid4())[:8])
            title = st.text_input("Title")
            author = st.text_input("Author")
            cover = st.text_input("Cover Image URL")
            price = st.text_input("Price (numeric)", value="")
            publisher = st.text_input("Publisher")
            isbn = st.text_input("ISBN")
            pages = st.text_input("Pages")
            edition = st.text_input("Edition")
            language = st.text_input("Language")
            tags = st.text_input("Tags (comma separated)")
            rating = st.number_input("Initial Rating (0-5)", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
            description = st.text_area("Short Description")
            index_text = st.text_area("Index / Overview")
            submit = st.form_submit_button("Add Book")
            if submit:
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                price_val = float(price) if price.strip() else None
                ok,msg = add_book(book_id.strip(), title.strip(), author.strip(),
                                 cover.strip(), description.strip(), index_text.strip(), tag_list,
                                 price=price_val, publisher=publisher.strip() or None,
                                 isbn=isbn.strip() or None, pages=pages.strip() or None,
                                 edition=edition.strip() or None, language=language.strip() or None,
                                 rating=rating)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
    elif mode == "All Issued":
        st.markdown("## All Issued Records")
        issued = get_user_issued()
        books = {b["id"]:b for b in load_books()}
        for rec in issued:
            b = books.get(rec["book_id"], {})
            st.write(f"- **{b.get('title','-')}** | Borrower: {rec['user_email']} | Due: {rec['deadline']}")
            if st.button(f"Return {rec['record_id']}", key=f"libret_{rec['record_id']}"):
                ok,msg = return_book(rec['record_id'])
                if ok:
                    st.success("Returned")
                else:
                    st.error(msg)
                st.experimental_rerun()
    elif mode == "Edit Book":
        st.markdown("## Edit an existing book")
        books = load_books()
        key_map = {b["id"]: f"{b['title']} — {b['author']}" for b in books}
        if not key_map:
            st.info("No books to edit.")
            return
        sel = st.selectbox("Select book to edit", list(key_map.keys()), format_func=lambda x: key_map[x])
        book = next((b for b in books if b["id"]==sel), None)
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
                submit = st.form_submit_button("Save Changes")
                if submit:
                    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                    price_val = float(price) if price.strip() else None
                    ok,msg = edit_book(book["id"], title=title.strip(), author=author.strip(), cover=cover.strip(),
                                       price=price_val, publisher=publisher.strip() or None, isbn=isbn.strip() or None,
                                       pages=pages.strip() or None, edition=edition.strip() or None,
                                       language=language.strip() or None, tags=tag_list,
                                       rating=rating, description=description.strip(), index=index_text.strip())
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

# dispatch
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
    # if edit_book_id is set, show edit in sidebar; fallback to console
    page_librarian_console()
else:
    st.info("Page not implemented.")

# keep session user object fresh after modifications
if st.session_state.user:
    st.session_state.user = find_user_by_email(st.session_state.user["email"])

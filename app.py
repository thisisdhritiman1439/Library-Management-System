# app.py
import streamlit as st
import json
from pathlib import Path
import hashlib
import datetime
import uuid

st.set_page_config(page_title="Smart Library", page_icon="📚", layout="wide")

# -------------------- File paths --------------------
USER_FILE = "users.json"
BOOK_FILE = "books.json"
ISSUED_FILE = "issued_books.json"

# -------------------- Helpers --------------------
def ensure_file(path, default):
    p = Path(path)
    if not p.exists():
        p.write_text(json.dumps(default, indent=4))
    return path

ensure_file(USER_FILE, [])
ensure_file(BOOK_FILE, [])
ensure_file(ISSUED_FILE, [])

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def find_user_by_email(email):
    users = load_json(USER_FILE)
    for u in users:
        if u["email"].lower() == email.lower():
            return u
    return None

def update_user(user_obj):
    users = load_json(USER_FILE)
    for i, u in enumerate(users):
        if u["email"].lower() == user_obj["email"].lower():
            users[i] = user_obj
            save_json(USER_FILE, users)
            return True
    return False

# -------------------- Business logic --------------------
def signup(name, mobile, email, password, role):
    if find_user_by_email(email):
        return False, "Email already registered."
    user = {
        "name": name,
        "mobile": mobile,
        "email": email.lower(),
        "password_hash": hash_password(password),
        "role": role,
        "favorites": []    # list of book_ids user saved for later
    }
    users = load_json(USER_FILE)
    users.append(user)
    save_json(USER_FILE, users)
    return True, "Account created successfully."

def login(email, password):
    u = find_user_by_email(email)
    if not u:
        return False, "No account with that email."
    if u["password_hash"] != hash_password(password):
        return False, "Incorrect password."
    return True, u

# Book CRUD
def load_books():
    return load_json(BOOK_FILE)

def save_books(books):
    save_json(BOOK_FILE, books)

def add_book(book_id, title, author, cover, description, index_text, tags):
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
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    books.append(book)
    save_books(books)
    return True, "Book added."

def delete_book(book_id):
    books = load_books()
    new = [b for b in books if b["id"] != book_id]
    if len(new) == len(books):
        return False, "Book not found."
    save_books(new)
    # Also remove any issued records for this book and remove from users' favorites
    issued = load_json(ISSUED_FILE)
    issued = [i for i in issued if i["book_id"] != book_id]
    save_json(ISSUED_FILE, issued)
    users = load_json(USER_FILE)
    for u in users:
        if book_id in u.get("favorites", []):
            u["favorites"].remove(book_id)
    save_json(USER_FILE, users)
    return True, "Book deleted."

# Issue / Return
DEFAULT_LOAN_DAYS = 14

def issue_book(book_id, user_email, days=DEFAULT_LOAN_DAYS):
    books = load_books()
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        return False, "Book not found."
    if not book["available"]:
        return False, "Book is currently not available."

    issued = load_json(ISSUED_FILE)
    issue_rec = {
        "record_id": str(uuid.uuid4()),
        "book_id": book_id,
        "user_email": user_email.lower(),
        "issue_date": datetime.date.today().isoformat(),
        "deadline": (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
    }
    issued.append(issue_rec)
    save_json(ISSUED_FILE, issued)

    # mark book unavailable
    book["available"] = False
    save_books(books)
    return True, issue_rec

def return_book(record_id, user_email=None):
    issued = load_json(ISSUED_FILE)
    rec = next((r for r in issued if r["record_id"] == record_id), None)
    if not rec:
        return False, "Issue record not found."
    if user_email and rec["user_email"].lower() != user_email.lower():
        return False, "You are not the borrower of this record."
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

# Favorites
def add_favorite(user_email, book_id):
    u = find_user_by_email(user_email)
    if not u: return False, "User not found."
    if book_id in u.get("favorites", []):
        return False, "Already in favorites."
    u.setdefault("favorites", []).append(book_id)
    update_user(u)
    return True, "Added to favorites."

def remove_favorite(user_email, book_id):
    u = find_user_by_email(user_email)
    if not u: return False, "User not found."
    if book_id in u.get("favorites", []):
        u["favorites"].remove(book_id)
        update_user(u)
        return True, "Removed from favorites."
    return False, "Book not in favorites."

# Simple recommendation engine
def recommend_for_user(user_email, top_n=5):
    issued = load_json(ISSUED_FILE)
    books = load_books()
    user_history = [r["book_id"] for r in issued if r["user_email"].lower() == user_email.lower()]
    if not user_history:
        # recommend popular available books (simple heuristic: newest available)
        candidates = [b for b in books if b["available"]]
        candidates = sorted(candidates, key=lambda x: x.get("created_at",""), reverse=True)
        return candidates[:top_n]
    last = user_history[-1]
    last_book = next((b for b in books if b["id"] == last), None)
    if not last_book:
        return books[:top_n]
    # Prefer same author
    same_author = [b for b in books if b["author"].lower()==last_book["author"].lower() and b["id"]!=last]
    if same_author:
        return same_author[:top_n]
    # fallback: match tags
    tags = set(last_book.get("tags", []))
    if tags:
        scored = []
        for b in books:
            if b["id"] == last: continue
            score = len(tags.intersection(set(b.get("tags", []))))
            if score>0:
                scored.append((score,b))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [b for s,b in scored][:top_n]
    # last fallback: other available books
    return [b for b in books if b["id"]!=last][:top_n]

# -------------------- UI helpers --------------------
def days_left(deadline_iso):
    d = datetime.date.fromisoformat(deadline_iso)
    delta = (d - datetime.date.today()).days
    return delta

def book_card(book, user=None):
    col1, col2 = st.columns([1,4])
    with col1:
        if book.get("cover"):
            try:
                st.image(book["cover"], use_column_width=True)
            except:
                st.image("https://via.placeholder.com/150x220.png?text=No+Cover", use_column_width=True)
        else:
            st.image("https://via.placeholder.com/150x220.png?text=No+Cover", use_column_width=True)
    with col2:
        st.markdown(f"### {book['title']}")
        st.markdown(f"**Author:** {book['author']}")
        st.markdown(f"**Book ID:** `{book['id']}` — {'Available' if book.get('available',True) else 'Checked out'}")
        st.write(book.get("description","_No description provided._"))
        with st.expander("Index / Overview"):
            st.write(book.get("index","_No index provided._"))

# -------------------- Main app --------------------
def main():
    st.sidebar.title("Navigation")
    menu = st.sidebar.radio("", ["Home","Login","Sign Up","About"])

    # global session user
    if "user" not in st.session_state:
        st.session_state.user = None

    # top header
    st.markdown("""
    <style>
    .title {font-size:28px; font-weight:600;}
    .muted {color:#6c757d;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="title">📚 Smart Library System</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Role-based, deploy-ready Streamlit library management</div>', unsafe_allow_html=True)
    st.write("---")

    if menu == "Home":
        books = load_books()
        r1, r2 = st.columns([3,1])
        with r1:
            st.subheader("All Books")
            for b in books:
                st.container()
                book_card(b, st.session_state.user)
                # buttons row
                cols = st.columns([1,1,1,1,1])
                if st.session_state.user:
                    user_role = st.session_state.user["role"]
                    # Favorite button for non-librarian & others
                    if b["id"] in st.session_state.user.get("favorites",[]):
                        if cols[0].button("★ Favorited", key=f"fav_remove_{b['id']}"):
                            remove_favorite(st.session_state.user["email"], b["id"])
                            st.experimental_rerun()
                    else:
                        if cols[0].button("☆ Add to List", key=f"fav_add_{b['id']}"):
                            add_favorite(st.session_state.user["email"], b["id"])
                            st.success("Added to your list.")
                            st.experimental_rerun()

                    # Issue button (only if available)
                    if b.get("available", True) and user_role != "Librarian":
                        if cols[1].button("📚 Issue Book", key=f"issue_{b['id']}"):
                            ok, resp = issue_book(b["id"], st.session_state.user["email"])
                            if ok:
                                st.success(f"Issued successfully — deadline {resp['deadline']}")
                            else:
                                st.error(resp)
                            st.experimental_rerun()
                    else:
                        cols[1].write("")  # spacing

                    # Overview/Index
                    if cols[2].button("🔎 View Index", key=f"index_{b['id']}"):
                        st.info(b.get("index","No index available"))
                    # Librarian actions
                    if user_role == "Librarian":
                        if cols[3].button("✏️ Edit", key=f"edit_{b['id']}"):
                            st.session_state.edit_book_id = b['id']
                            st.experimental_rerun()
                        if cols[4].button("🗑 Delete", key=f"del_{b['id']}"):
                            ok,msg = delete_book(b['id'])
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
                            st.experimental_rerun()
                else:
                    # not logged in - show login prompt for issue/favorites
                    cols[0].info("Login to issue / save")
                st.write("---")

        with r2:
            st.subheader("Quick Panel")
            if st.session_state.user:
                st.markdown(f"**Signed in as:** {st.session_state.user['name']}  \n**Role:** {st.session_state.user['role']}")
                if st.button("Logout"):
                    st.session_state.user = None
                    st.success("Logged out.")
                    st.experimental_rerun()

                st.write("### My Favorites")
                favs = st.session_state.user.get("favorites", [])
                books_dict = {b["id"]:b for b in load_books()}
                if favs:
                    for fid in favs:
                        b = books_dict.get(fid)
                        if b:
                            st.write(f"- {b['title']} by {b['author']} ({'Available' if b['available'] else 'Checked out'})")
                else:
                    st.write("_No favorites yet._")

                st.write("### My Issued Books")
                my_issued = get_user_issued(st.session_state.user["email"])
                if my_issued:
                    for rec in my_issued:
                        b = next((bb for bb in load_books() if bb["id"]==rec["book_id"]), {})
                        left = days_left(rec["deadline"])
                        st.write(f"- **{b.get('title','-')}** | Due: {rec['deadline']} | Days left: {left}")
                        if st.button(f"Return: {b.get('title','')}", key=f"return_{rec['record_id']}"):
                            ok,msg = return_book(rec["record_id"], st.session_state.user["email"])
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
                            st.experimental_rerun()
                else:
                    st.write("_No issued books._")

                st.write("### Recommendations")
                recs = recommend_for_user(st.session_state.user["email"], top_n=5)
                for rb in recs:
                    st.write(f"- {rb['title']} by {rb['author']}")
            else:
                st.info("Login or Sign Up to access favorites, issue books and recommendations.")
                st.markdown("[Login →](#login)")

    elif menu == "Sign Up":
        st.subheader("Create a new account")
        with st.form("signup_form"):
            name = st.text_input("Full name")
            mobile = st.text_input("Mobile number")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Student", "Librarian", "Other"])
            submitted = st.form_submit_button("Sign Up")
            if submitted:
                ok,msg = signup(name, mobile, email, password, role)
                if ok:
                    st.success(msg + " Please login.")
                else:
                    st.error(msg)

    elif menu == "Login":
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                ok, resp = login(email, password)
                if ok:
                    st.session_state.user = resp
                    st.success(f"Welcome {resp['name']} ({resp['role']})")
                    st.experimental_rerun()
                else:
                    st.error(resp)

    elif menu == "About":
        st.subheader("About this system")
        st.write("""
        **Smart Library System** — Features:
        - Role-based authentication (Student / Librarian / Other)
        - View all books with cover, description and index
        - Librarian-only: Add, Edit (planned), Delete books
        - Users: Add to favorites (book list), Issue & Return books
        - Issued book tracking with deadline & days-left calculation
        - Recommendations based on user's borrowing history (author/tags)
        """)
        st.markdown("## Deployment\nFollow standard Streamlit Cloud / GitHub deployment steps. Add `app.py`, JSON files and `requirements.txt` to repo.")

    # Librarian add / edit panel (floating)
    if st.session_state.user and st.session_state.user["role"] == "Librarian":
        st.sidebar.write("### Librarian Console")
        lib_action = st.sidebar.selectbox("Librarian Action", ["Add Book","View All Issued"])
        if lib_action == "Add Book":
            st.sidebar.write("Add a new book")
            with st.sidebar.form("add_book_form"):
                book_id = st.text_input("Book ID", value=str(uuid.uuid4())[:8])
                title = st.text_input("Title")
                author = st.text_input("Author")
                cover = st.text_input("Cover Image URL")
                tags = st.text_input("Tags (comma separated)")
                description = st.text_area("Short Description")
                index_text = st.text_area("Index / Overview")
                submit = st.form_submit_button("Add Book")
                if submit:
                    ok,msg = add_book(book_id.strip(), title.strip(), author.strip(), cover.strip(), description.strip(), index_text.strip(), [t.strip() for t in tags.split(",") if t.strip()])
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
        else:
            st.sidebar.write("All issued records")
            issued = get_user_issued()
            for rec in issued:
                b = next((bb for bb in load_books() if bb["id"]==rec["book_id"]), {})
                st.sidebar.write(f"- {b.get('title','-')} | {rec['user_email']} | Due {rec['deadline']}")
                if st.sidebar.button(f"Return {rec['record_id']}", key=f"libret_{rec['record_id']}"):
                    ok,msg = return_book(rec['record_id'])
                    if ok:
                        st.sidebar.success("Returned")
                    else:
                        st.sidebar.error(msg)
                    st.experimental_rerun()

if __name__ == "__main__":
    main()

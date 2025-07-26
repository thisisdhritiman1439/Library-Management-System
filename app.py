import streamlit as st
import pandas as pd
import os
import json
import hashlib
import random
import datetime
import requests
from collections import Counter

# ------------------ File paths ------------------
BOOKS_FILE = "books_data.json"
USERS_FILE = "users.json"
RESERVATIONS_FILE = "reservations.json"

# ------------------ Helper functions ------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_simulated(contact, otp):
    st.info(f"(Simulation) OTP sent to {contact}: **{otp}**")

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ------------------ Users ------------------
def load_users():
    return load_json(USERS_FILE)

def save_users(users):
    save_json(USERS_FILE, users)

def signup(username, password, role, email, phone):
    users = load_users()
    if any(u["username"] == username for u in users):
        return False
    users.append({"username": username, "password": hash_password(password), "role": role, "email": email, "phone": phone})
    save_users(users)
    return True

def check_credentials(username, password):
    for u in load_users():
        if u["username"] == username and u["password"] == hash_password(password):
            return u
    return None

def update_password(username, new_password):
    users = load_users()
    for u in users:
        if u["username"] == username:
            u["password"] = hash_password(new_password)
            save_users(users)
            return True
    return False

# ------------------ Books ------------------
def load_books():
    data = load_json(BOOKS_FILE)
    df = pd.DataFrame(data)
    for col in ["issued_to", "issue_date", "due_date", "description", "cover_url"]:
        if col not in df.columns:
            df[col] = ""
    return df

def save_books(df):
    save_json(BOOKS_FILE, df.to_dict(orient="records"))

def fetch_book_info_by_isbn(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        response = requests.get(url)
        data = response.json()
        if "items" in data:
            volume_info = data["items"][0]["volumeInfo"]
            description = volume_info.get("description", "No description available.")
            cover_url = volume_info.get("imageLinks", {}).get("thumbnail", "")
            return description, cover_url
    except:
        pass
    return "No description available.", ""

# ------------------ Reservation ------------------
def load_reservations():
    return load_json(RESERVATIONS_FILE)

def save_reservations(reservations):
    save_json(RESERVATIONS_FILE, reservations)

def notify_due_books(books_df):
    today = datetime.date.today()
    warning = False
    for _, row in books_df.iterrows():
        if row["status"] == "issued" and row["due_date"]:
            due = datetime.date.fromisoformat(row["due_date"])
            if 0 <= (due - today).days <= 3:
                st.warning(f"📢 Reminder: '{row['title']}' is due on {row['due_date']} for {row['issued_to']}")
                warning = True
    return warning

def recommend_books(df, user):
    past = df[df["issued_to"] == user]
    if past.empty:
        return df.sample(3)
    categories = past["category"].value_counts().index.tolist()
    return df[df["category"].isin(categories) & (df["status"] == "available")].sample(min(3, len(df)))

def analytics_dashboard(df):
    st.header("📊 Analytics Dashboard")
    most_borrowed = df[df["status"] == "issued"]["title"].value_counts().head(5)
    st.subheader("Most Borrowed Books")
    st.bar_chart(most_borrowed)

    users = df[df["status"] == "issued"]["issued_to"].value_counts().head(5)
    st.subheader("Active Users")
    st.bar_chart(users)

    late = 0
    today = datetime.date.today()
    for _, row in df.iterrows():
        if row["status"] == "issued" and row["due_date"]:
            due = datetime.date.fromisoformat(row["due_date"])
            if today > due:
                late += 1
    st.subheader("Late Returns")
    st.metric("Late Returned Books", late)

# ------------------ Chatbot Assistant ------------------
def librarian_bot():
    st.subheader("💬 Ask the Librarian")
    user_q = st.text_input("Ask your question")
    if user_q:
        if "issue" in user_q.lower():
            st.info("Go to 'Issue Book' to borrow a book.")
        elif "return" in user_q.lower():
            st.info("Visit 'Return Book' to give back your book.")
        elif "recommend" in user_q.lower():
            st.info("Go to 'View Books' for AI-based recommendations.")
        else:
            st.info("Sorry, I didn't understand that. Try asking about issuing, returning, or recommendations.")

# ------------------ Streamlit App ------------------
st.set_page_config("Library Management", "📚", layout="wide")

if "auth_stage" not in st.session_state:
    st.session_state.auth_stage = "login"
if "pending_user" not in st.session_state:
    st.session_state.pending_user = None
if "otp" not in st.session_state:
    st.session_state.otp = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

st.title("📚 Library Management System")

# ------------------ Signup ------------------
with st.expander("📝 Sign Up"):
    su_user = st.text_input("Username")
    su_pass = st.text_input("Password", type="password")
    su_email = st.text_input("Email")
    su_phone = st.text_input("Phone Number")
    su_role = st.selectbox("Role", ["student", "admin"])
    if st.button("Register"):
        if signup(su_user, su_pass, su_role, su_email, su_phone):
            st.success("✅ Account created.")
        else:
            st.error("⚠️ Username exists.")

# ------------------ Login ------------------
if st.session_state.auth_stage == "login":
    login_user = st.text_input("Username")
    login_pass = st.text_input("Password", type="password")
    if st.button("Login"):
        user = check_credentials(login_user, login_pass)
        if user:
            otp = generate_otp()
            st.session_state.otp = otp
            st.session_state.pending_user = login_user
            send_otp_simulated(user["email"] or user["phone"], otp)
            st.session_state.auth_stage = "otp"
        else:
            st.error("Invalid credentials.")

elif st.session_state.auth_stage == "otp":
    otp_input = st.text_input("Enter OTP")
    if st.button("Verify"):
        if otp_input == st.session_state.otp:
            st.session_state.logged_in = True
            st.session_state.username = st.session_state.pending_user
            u = next((x for x in load_users() if x["username"] == st.session_state.username), None)
            st.session_state.role = u["role"]
            st.session_state.auth_stage = "loggedin"
        else:
            st.error("Incorrect OTP")

# ------------------ Dashboard ------------------
if st.session_state.logged_in:
    user = st.session_state.username
    role = st.session_state.role
    books_df = load_books()
    reservations = load_reservations()

    notify_due_books(books_df)

    menu = ["View Books", "Issue Book", "Return Book", "Recommendations", "Ask Librarian", "Logout"]
    if role == "admin":
        menu = ["Analytics", "Add Book", "Delete Book"] + menu
    choice = st.sidebar.radio("Menu", menu)

    if choice == "View Books":
        for _, row in books_df.iterrows():
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    if row["cover_url"]:
                        st.image(row["cover_url"], width=120)
                with cols[1]:
                    st.subheader(f"{row['title']} by {row['author']}")
                    st.markdown(f"**Category:** {row['category']}\n**Status:** {row['status']}")
                    st.markdown(f"**Description:** {row['description']}")
                    if row["status"] == "issued":
                        if st.button(f"Reserve {row['title']}"):
                            reservations.append({"user": user, "bid": row["bid"]})
                            save_reservations(reservations)
                            st.success("Book reserved. You'll be notified when it's returned.")

    elif choice == "Add Book" and role == "admin":
        bid = st.number_input("Book ID", min_value=1)
        title = st.text_input("Title")
        author = st.text_input("Author")
        category = st.text_input("Category")
        isbn = st.text_input("ISBN (optional)")
        description, cover_url = "", ""
        if isbn and st.button("Fetch via ISBN"):
            description, cover_url = fetch_book_info_by_isbn(isbn)
        description = st.text_area("Description", value=description)
        cover_url = st.text_input("Cover URL", value=cover_url)
        if st.button("Add"):
            books_df = books_df.append({"bid": bid, "title": title, "author": author, "category": category,
                                        "status": "available", "issued_to": "", "issue_date": "", "due_date": "",
                                        "description": description, "cover_url": cover_url}, ignore_index=True)
            save_books(books_df)
            st.success("Book added")

    elif choice == "Delete Book" and role == "admin":
        bid = st.selectbox("Book ID", books_df["bid"])
        if st.button("Delete"):
            books_df = books_df[books_df["bid"] != bid]
            save_books(books_df)
            st.success("Deleted")

    elif choice == "Issue Book":
        avail = books_df[books_df["status"] == "available"]
        if not avail.empty:
            bid = st.selectbox("Book", avail["bid"].astype(str) + " - " + avail["title"])
            actual_bid = int(bid.split(" - ")[0])
            if st.button("Issue"):
                idx = books_df[books_df["bid"] == actual_bid].index[0]
                books_df.at[idx, "status"] = "issued"
                books_df.at[idx, "issued_to"] = user
                today = datetime.date.today()
                due = today + datetime.timedelta(days=30)
                books_df.at[idx, "issue_date"] = str(today)
                books_df.at[idx, "due_date"] = str(due)
                save_books(books_df)
                st.success("Book issued")
        else:
            st.info("No available books")

    elif choice == "Return Book":
        my_books = books_df[(books_df["issued_to"] == user)]
        if not my_books.empty:
            bid = st.selectbox("Return", my_books["bid"].astype(str) + " - " + my_books["title"])
            actual_bid = int(bid.split(" - ")[0])
            if st.button("Return"):
                idx = books_df[books_df["bid"] == actual_bid].index[0]
                today = datetime.date.today()
                due = datetime.date.fromisoformat(books_df.at[idx, "due_date"])
                fine = max(0, (today - due).days * 5)
                books_df.at[idx, "status"] = "available"
                books_df.at[idx, "issued_to"] = ""
                books_df.at[idx, "issue_date"] = ""
                books_df.at[idx, "due_date"] = ""
                save_books(books_df)

                # Check reservations
                to_notify = [r for r in reservations if r["bid"] == actual_bid]
                if to_notify:
                    st.success(f"Book returned. Reserved user {to_notify[0]['user']} should be notified.")
                    reservations.remove(to_notify[0])
                    save_reservations(reservations)
                if fine > 0:
                    st.warning(f"Late return. Fine: ₹{fine}")
                else:
                    st.success("Returned successfully")
        else:
            st.info("No books to return")

    elif choice == "Recommendations":
        st.subheader("📌 Recommended Books for You")
        rec = recommend_books(books_df, user)
        for _, row in rec.iterrows():
            st.markdown(f"- **{row['title']}** by *{row['author']}* ({row['category']})")

    elif choice == "Analytics":
        analytics_dashboard(books_df)

    elif choice == "Ask Librarian":
        librarian_bot()

    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.auth_stage = "login"
        st.rerun()

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
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
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
    for _, row in books_df.iterrows():
        if row["status"] == "issued" and row["due_date"]:
            due = datetime.date.fromisoformat(row["due_date"])
            if 0 <= (due - today).days <= 3:
                st.warning(f"📢 Reminder: '{row['title']}' is due on {row['due_date']} for {row['issued_to']}")

def recommend_books(df, user):
    past = df[df["issued_to"] == user]
    if past.empty:
        return df[df["status"] == "available"].sample(min(3, len(df)))
    categories = past["category"].value_counts().index.tolist()
    return df[(df["category"].isin(categories)) & (df["status"] == "available")].sample(min(3, len(df)))

def analytics_dashboard(df):
    st.header("📊 Analytics Dashboard")
    most_borrowed = df["title"].value_counts().head(5)
    st.subheader("Most Borrowed Books")
    st.bar_chart(most_borrowed)

    users = df["issued_to"].value_counts().head(5)
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
    user_q = st.text_input("Ask your question", key="chatbot_input")
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

if not st.session_state.logged_in:
    with st.expander("📝 Sign Up (Only if you want to create a new account)"):
        su_user = st.text_input("New Username", key="signup_user")
        su_pass = st.text_input("New Password", type="password", key="signup_pass")
        su_email = st.text_input("Email", key="signup_email")
        su_phone = st.text_input("Phone", key="signup_phone")
        su_role = st.selectbox("Role", ["student", "admin"], key="signup_role")
        if st.button("Register", key="signup_btn"):
            if signup(su_user, su_pass, su_role, su_email, su_phone):
                st.success("✅ Account created.")
            else:
                st.error("⚠️ Username exists.")

if not st.session_state.logged_in and st.session_state.auth_stage == "login":
    login_user = st.text_input("Username", key="login_user")
    login_pass = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login", key="login_btn"):
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
    otp_input = st.text_input("Enter OTP", key="otp_input")
    if st.button("Verify", key="otp_btn"):
        if otp_input == st.session_state.otp:
            st.session_state.logged_in = True
            st.session_state.username = st.session_state.pending_user
            u = next((x for x in load_users() if x["username"] == st.session_state.username), None)
            st.session_state.role = u["role"]
            st.session_state.auth_stage = "loggedin"
        else:
            st.error("Incorrect OTP")

if st.session_state.logged_in:
    st.success(f"Welcome, {st.session_state.username}! 🎉")
    books_df = load_books()
    notify_due_books(books_df)
    librarian_bot()

    st.subheader("📚 Recommended Books for You")
    recs = recommend_books(books_df, st.session_state.username)
    for _, row in recs.iterrows():
        st.markdown(f"### {row['title']} by {row['author']}")
        st.image(row['cover_url'] or "https://via.placeholder.com/120x180", width=120)
        st.write(row['description'] or "No description available.")
        st.markdown("---")

    if st.session_state.role == "admin":
        analytics_dashboard(books_df)

    st.header("📘 All Books")
    for _, row in books_df.iterrows():
        with st.container():
            cols = st.columns([1, 4])
            with cols[0]:
                st.image(row['cover_url'] or "https://via.placeholder.com/120x180", width=120)
            with cols[1]:
                st.subheader(f"{row['title']} by {row['author']}")
                st.markdown(f"**Category:** {row['category']} | **Status:** {row['status']}")
                st.write(row['description'] or "No description available.")
                st.markdown("---")

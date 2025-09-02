# app.py
import streamlit as st
from pathlib import Path
import json, hashlib, datetime, uuid, shutil, time
from typing import List, Dict

st.set_page_config(page_title="Smart Library", page_icon="📚", layout="wide")

# ---------------------- File paths ----------------------
USER_FILE = "users.json"
BOOK_FILE = "books_data.json"
ISSUED_FILE = "issued_books.json"

# ---------------------- Safe JSON helpers ----------------------
def safe_save_json(path: str, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def safe_load_json(path: str, default):
    p = Path(path)
    if not p.exists():
        safe_save_json(path, default)
        return default
    try:
        text = p.read_text(encoding="utf-8").strip()
        if text == "":
            safe_save_json(path, default)
            return default
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        # backup corrupted file
        try:
            bak = f"{path}.backup.{int(time.time())}"
            shutil.move(path, bak)
            safe_save_json(path, default)
            st.warning(f"Corrupt JSON `{path}` found — backed up to `{bak}` and recreated default.")
        except Exception:
            safe_save_json(path, default)
            st.warning(f"Corrupt JSON `{path}` detected — recreated default (backup may have failed).")
        return default

# ---------------------- Default 61 books dataset ----------------------
def get_default_books() -> List[Dict]:
    # 61 books converted to new format. Covers are mostly public Amazon links (may change over time).
    # Each book has: id (B001..B061), title, author, cover, description, index (list), available (bool), genre, tags, price optional
    now = datetime.datetime.utcnow().isoformat()
    B = []
    def add(i, title, author, cover, desc, idx_list, genre, available=True, tags=None, price=None):
        bid = f"B{int(i):03d}"
        B.append({
            "id": bid,
            "title": title,
            "author": author,
            "cover": cover or "",
            "description": desc,
            "index": idx_list,
            "available": bool(available),
            "genre": genre,
            "tags": tags or [],
            "price": price,
            "publisher": None,
            "isbn": None,
            "pages": None,
            "edition": None,
            "language": None,
            "rating": 0.0,
            "reviews": [],
            "times_issued": 0,
            "created_at": now
        })
    # We'll add the 61 books (some cover links used previously in the conversation; fallbacks may be empty)
    add(1,  "Steve Jobs", "Walter Isaacson", "https://images-na.ssl-images-amazon.com/images/I/71zF6lUgWwL.jpg",
        "Biography of Steve Jobs, detailing his life and the founding of Apple.", ["Introduction","Timeline","Chapters"], "Biography", available=False, tags=["biography","technology"])
    add(2,  "Discovery of India", "Jawaharlal Nehru", "https://images-na.ssl-images-amazon.com/images/I/81j5jbe0CZL.jpg",
        "Jawaharlal Nehru's reflections on Indian history, culture and identity.", ["Part I","Part II","Part III"], "History", available=False, tags=["history","india"])
    add(3,  "My Experiments with Truth", "Mahatma Gandhi", "https://images-na.ssl-images-amazon.com/images/I/91uCG96XJYL.jpg",
        "Autobiography of Mahatma Gandhi covering his personal experiments and philosophy.", ["Early Life","South Africa","Return to India"], "Autobiography", available=False, tags=["autobiography","india"])
    add(4,  "Object Oriented Programming with C++", "E Balagurusamy", "https://m.media-amazon.com/images/I/51BIl9DYsUL.jpg",
        "Introductory textbook on C++ and object oriented concepts.", ["Basics","Classes & Objects","Advanced Topics"], "Education", available=False, tags=["programming","c++"])
    add(5,  "Thinking with Type", "Ellen Lupton", "https://images-na.ssl-images-amazon.com/images/I/81chrfcZz7L.jpg",
        "A guide to typography and visual communication.", ["Principles","Type Anatomy","Applications"], "Arts", available=False, tags=["design","typography"])
    add(6,  "The Photographer's", "Lindsay Adler", "https://images-na.ssl-images-amazon.com/images/I/51MYoPQidUL.jpg",
        "Techniques and guidance for portrait and fashion photography.", ["Lighting","Posing","Editing"], "Photography", available=False, tags=["photography"])
    add(7,  "Think and Grow", "Napoleon Hill", "https://images-na.ssl-images-amazon.com/images/I/81s6DUyQCZL.jpg",
        "Personal development and success principles.", ["Mindset","Habits","Wealth"], "Economics", available=False, tags=["self-help","success"])
    add(8,  "The Fifth Discipline : The Art", "Peter M.Senge", "https://m.media-amazon.com/images/I/81b0C2YNSrL.jpg",
        "Systems thinking and learning organizations.", ["Systems","Leadership","Practice"], "Management", available=False, tags=["management"])
    add(9,  "A Theory of Justice", "John Rawls", "https://images-na.ssl-images-amazon.com/images/I/81OthjkJBuL.jpg",
        "Philosophical exposition of justice as fairness.", ["Foundations","Principles","Applications"], "Law", available=False, tags=["philosophy","political"])
    add(10, "Eat to Live", "Joel Fuhrman", "https://m.media-amazon.com/images/I/81gepf1eMqL.jpg",
        "Nutrition guide promoting nutrient rich eating for health and weight loss.", ["Nutrition","Recipes","Plans"], "Health", available=False, tags=["health","nutrition"])
    add(11, "City of Heavenly Fire", "Cassandra Clare", "https://m.media-amazon.com/images/I/91b0C2YNSrL.jpg",
        "Fiction — young adult fantasy with Shadowhunters.", ["Prologue","Battles","Aftermath"], "Fiction", available=True, tags=["fantasy"])
    add(12, "Da Vinci Code", "Dan Brown", "https://m.media-amazon.com/images/I/71K6XJrGZOL.jpg",
        "A fast-paced thriller mixing art, history and conspiracy.", ["Prologue","The Puzzle","The Chase"], "Fiction", available=True, tags=["thriller"])
    add(13, "War and Peace", "Leo Tolstoy", "https://m.media-amazon.com/images/I/81s6DUyQCZL.jpg",
        "Epic novel of Russia during the Napoleonic era.", ["Book I","Book II","Book III"], "Philosophical fiction", available=False, tags=["classic","historical"])
    add(14, "Python For All", "John Shovic", "https://m.media-amazon.com/images/I/51K8ouYrHeL._SX379_BO1,204,203,200_.jpg",
        "Introductory Python text with hands-on examples.", ["Basics","Data Structures","Projects"], "Education", available=True, tags=["python"])
    add(15, "Automate The Boring Stuff With Python", "Al Sweigart", "https://m.media-amazon.com/images/I/81t2CVWEsUL.jpg",
        "Practical automation tasks using Python.", ["Automating Tasks","Web Scraping","Excel"], "Education", available=True, tags=["python","automation"])
    add(16, "Wings Of Fire", "APJ Abdul Kalam", "https://m.media-amazon.com/images/I/81xXAy8pM1L.jpg",
        "Autobiography of A.P.J. Abdul Kalam describing his journey.", ["Early Life","Career","Vision"], "Autobiography", available=True, tags=["india","autobiography"])
    add(17, "Ikigai", "Hector Garcia", "https://m.media-amazon.com/images/I/81kR0V4Es6L.jpg",
        "Japanese concept about finding purpose and longevity.", ["Principles","Practices","Stories"], "Personal Development", available=True, tags=["self-help"])
    add(18, "Who Will Cry When You Will Die", "Robin Sharma", "https://m.media-amazon.com/images/I/81KXf2r4qOL.jpg",
        "Short life lessons and personal growth ideas.", ["Lessons","Practices"], "Personal Development", available=True, tags=["self-help"])
    add(19, "Rich Dad Poor Dad", "Robert T. Kiyosaki", "https://m.media-amazon.com/images/I/81bsw6fnUiL.jpg",
        "Personal finance and investing fundamentals.", ["Foundations","Assets","Mindset"], "Business", available=True, tags=["finance"])
    add(20, "Immortals of Meluha", "Amish Tripathi", "https://m.media-amazon.com/images/I/81cLw4kPOeL.jpg",
        "A mythological fantasy set in ancient India.", ["Origins","Conflict","Resolution"], "High Fantasy", available=True, tags=["fantasy","myth"])
    add(21, "A Brief History Of Time", "Stephen Hawking", "https://m.media-amazon.com/images/I/71yX3Z8wJEL.jpg",
        "Accessible cosmology and the physics of the universe.", ["Big Bang","Black Holes","Time"], "Science", available=False, tags=["science","physics"])
    add(22, "I Know Why The Caged Bird Sings", "Maya Angelou", "https://m.media-amazon.com/images/I/81uG1JZJ8xL.jpg",
        "Autobiographical work exploring identity and resilience.", ["Childhood","Voice","Triumph"], "Story", available=True, tags=["autobiography"])
    add(23, "Lord Of Flies", "William Golding", "https://m.media-amazon.com/images/I/71g2ednj0JL.jpg",
        "Novel about boys stranded on an island and the collapse of order.", ["Arrival","Conflict","Aftermath"], "Fiction", available=False, tags=["classic"])
    add(24, "Lorna Doone", "R. D. Blackmore", "https://m.media-amazon.com/images/I/71bG3r8qvPL.jpg",
        "Romantic historical novel set in Exmoor.", ["Love","Strife","Resolution"], "Fiction", available=False, tags=["classic"])
    add(25, "Jamaica Inn", "Daphne du Maurier", "https://m.media-amazon.com/images/I/81m6aQwUVAL.jpg",
        "A Gothic novel of smuggling and suspense.", ["Arrival","Mysteries","Confrontation"], "Fiction", available=False, tags=["gothic"])
    add(26, "Kidnapped", "Robert Louis Stevenson", "https://m.media-amazon.com/images/I/81gUQ5xnCkL.jpg",
        "Adventure novel of young David Balfour in Scotland.", ["Kidnapping","Journey","Home"], "Fiction", available=True, tags=["adventure"])
    add(27, "Treasure Island", "Robert Louis Stevenson", "https://m.media-amazon.com/images/I/81gUQ5xnCkL.jpg",
        "Classic pirate adventure with Long John Silver.", ["Map","Voyage","Treasure"], "Fiction", available=True, tags=["adventure"])
    add(28, "The Call Of The Wild", "Jack London", "https://m.media-amazon.com/images/I/81zj3j2IgaL.jpg",
        "The tale of Buck, a dog who returns to his wild instincts.", ["Kidnapped","Trail","Freedom"], "Fiction", available=True, tags=["adventure"])
    add(29, "Charlotte's Web", "E. B. White", "https://m.media-amazon.com/images/I/81OthjkJBuL.jpg",
        "Children's story of friendship between Wilbur and Charlotte.", ["Friendship","Courage","Legacy"], "Fiction", available=True, tags=["children"])
    add(30, "The Wind In The Willows", "Kenneth Grahame", "https://m.media-amazon.com/images/I/81t2CVWEsUL.jpg",
        "Whimsical tales of Mole, Rat, Toad and Badger.", ["River","Adventure","Home"], "Fiction", available=True, tags=["children"])
    add(31, "Being and Time", "Martin Heidegger", "https://m.media-amazon.com/images/I/81cLw4kPOeL.jpg",
        "Philosophical work exploring being and existence.", ["Existence","Time","Care"], "Philosophy", available=True, tags=["philosophy"])
    add(32, "The Republic", "Plato", "https://m.media-amazon.com/images/I/81dE3XoqoFL.jpg",
        "Dialogues on justice, politics and the ideal state.", ["Justice","Education","State"], "Philosophy", available=False, tags=["philosophy"])
    add(33, "Critique of Pure Reason", "Immanuel Kant", "https://m.media-amazon.com/images/I/81trR8LrYjL.jpg",
        "Foundational work of modern philosophy on cognition and reason.", ["Aesthetic","Understanding","Reason"], "Philosophy", available=True, tags=["philosophy"])
    add(34, "The Prince", "Niccolò Machiavelli", "https://m.media-amazon.com/images/I/81hLzKg4ZDL.jpg",
        "Treatise on political power and rule.", ["Power","Strategy","Ruler"], "Philosophy", available=True, tags=["political"])
    add(35, "Ethics", "Stuart Hampshire", "https://m.media-amazon.com/images/I/81U0a5yR0nL.jpg",
        "A collection exploring moral philosophy.", ["Moral Questions","Action","Responsibility"], "Philosophy", available=True, tags=["ethics"])
    add(36, "Long Walk To Freedom", "Nelson Mandela", "https://m.media-amazon.com/images/I/91uCG96XJYL.jpg",
        "Autobiography of Nelson Mandela and the struggle against apartheid.", ["Early Life","Activism","Presidency"], "Autobiography", available=True, tags=["history","autobiography"])
    add(37, "The Diary of a Young Girl", "Anne Frank", "https://m.media-amazon.com/images/I/81ySO5Z0j2L.jpg",
        "Anne Frank's wartime diary recording daily life in hiding.", ["Diary","Hope","Legacy"], "Autobiography", available=True, tags=["history"])
    add(38, "Mark Twain (selected)", "Mark Twain", "https://m.media-amazon.com/images/I/81x9V4Xj5mL.jpg",
        "Selections from Mark Twain's works.", ["Sketches","Stories"], "Autobiography", available=True, tags=["classic"])
    add(39, "Mein Kampf (historical)", "Adolf Hitler", "", 
        "Historical text (sensitive) — included for completeness; handle with care. Consider removing for public deployments.", ["Part 1","Part 2"], "Historical", available=True, tags=["history"])
    add(40, "Freakonomics", "Steven D. Levitt & Stephen J. Dubner", "https://m.media-amazon.com/images/I/81bsw6fnUiL.jpg",
        "Popular economics looking at incentives and unexpected correlations.", ["Incentives","Case Studies"], "Economics", available=False, tags=["economics"])
    add(41, "Thinking, Fast and Slow", "Daniel Kahneman", "https://m.media-amazon.com/images/I/81a4kCNuH+L.jpg",
        "Cognitive biases, heuristics and two systems of thought.", ["System 1","System 2"], "Economics", available=True, tags=["psychology"])
    add(42, "How Nations Fail (excerpt)", "Daron Acemoglu & James A. Robinson", "https://m.media-amazon.com/images/I/81r5z4NOpzL.jpg",
        "Why nations succeed or fail — institutions and politics.", ["Institutions","Case Studies"], "Economics", available=True, tags=["political"])
    add(43, "Animal Spirits", "George A. Akerlof & Robert J. Shiller", "https://m.media-amazon.com/images/I/81m6aQwUVAL.jpg",
        "Behavioral economics and the role of psychology in markets.", ["Confidence","Narrative"], "Economics", available=True, tags=["economics"])
    add(44, "The Black Swan", "Nassim Nicholas Taleb", "https://m.media-amazon.com/images/I/81p2bYd0KDL.jpg",
        "On rare events, unpredictability, and robustness.", ["Rare Events","Risk"], "Economics", available=False, tags=["economics"])
    add(45, "1984", "George Orwell", "https://m.media-amazon.com/images/I/71kxa1-0mfL.jpg",
        "Dystopian novel about surveillance and totalitarianism.", ["Big Brother","Resistance","Aftermath"], "Story", available=True, tags=["dystopia"])
    add(46, "The Lord of the Rings", "J.R.R. Tolkien", "https://m.media-amazon.com/images/I/91zbi9M+mKL.jpg",
        "Epic fantasy trilogy about the One Ring and the fight against Sauron.", ["Fellowship","Two Towers","Return of the King"], "Story", available=False, tags=["fantasy"])
    add(47, "Kite Runner", "Khaled Hosseini", "https://m.media-amazon.com/images/I/81OthjkJBuL.jpg",
        "A story of friendship, betrayal and redemption set against Afghanistan's turbulent history.", ["Childhood","Betrayal","Return"], "Story", available=True, tags=["fiction"])
    add(48, "Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "https://m.media-amazon.com/images/I/81iqZ2HHD-L.jpg",
        "The first Harry Potter book introducing Hogwarts and magic.", ["The Boy Who Lived","Hogwarts","The Mirror"], "Story", available=True, tags=["fantasy","young-adult"])
    add(49, "The Book Thief", "Markus Zusak", "https://m.media-amazon.com/images/I/81OthjkJBuL.jpg",
        "A story about a girl in Nazi Germany who steals books and shares them.", ["Books","War","Loss"], "Story", available=True, tags=["historical"])
    add(50, "A History of the 20th Century", "Martin Gilbert", "https://m.media-amazon.com/images/I/81nR8hLgAqL.jpg",
        "A survey of major events shaping the 20th century.", ["Wars","Politics","Society"], "History", available=True, tags=["history"])
    add(51, "Guns, Germs, and Steel", "Jared Diamond", "https://m.media-amazon.com/images/I/81v3w7h2ckL.jpg",
        "An analysis of societal development shaped by environment and resources.", ["Geography","Agriculture","Technology"], "History", available=False, tags=["history"])
    add(52, "A World Lit Only by Fire", "William Manchester", "https://m.media-amazon.com/images/I/81U0a5yR0nL.jpg",
        "A popular history of the Middle Ages and early modern Europe.", ["Dark Ages","Expansion"], "History", available=False, tags=["history"])
    add(53, "The Crusades", "Thomas Asbridge", "https://m.media-amazon.com/images/I/81xK4nwl8zL.jpg",
        "History of the medieval Crusades.", ["Origins","Campaigns","Impact"], "History", available=True, tags=["history"])
    add(54, "Over the Edge of the World", "Laurence Bergreen", "https://m.media-amazon.com/images/I/81STa7K8UvL.jpg",
        "Voyage of Magellan and the first circumnavigation.", ["Voyage","Challenges","Legacy"], "History", available=True, tags=["history","exploration"])
    add(55, "A Beautiful Mind", "Sylvia Nasar", "https://m.media-amazon.com/images/I/91ySO5Z0j2L.jpg",
        "Biography of John Nash and his work in game theory.", ["Early Life","Math","Struggles"], "Biography", available=True, tags=["biography"])
    add(56, "The Enigma", "Andrew Hodges", "https://m.media-amazon.com/images/I/91tL-4Qh5qL.jpg",
        "Biography of Alan Turing and the birth of computer science.", ["Turing","War","Legacy"], "Biography", available=True, tags=["biography","computing"])
    add(57, "Alexander Hamilton", "Ron Chernow", "https://m.media-amazon.com/images/I/91b0C2YNSrL.jpg",
        "Biography of American Founding Father Alexander Hamilton.", ["Early Life","Politics","Legacy"], "Biography", available=True, tags=["biography","history"])
    add(58, "Barracoon", "Zora Neale Hurston", "https://m.media-amazon.com/images/I/81kR0V4Es6L.jpg",
        "First-hand account of formerly enslaved people in America.", ["Interviews","Stories"], "Biography", available=True, tags=["history"])
    add(59, "Churchill: A Life", "Martin Gilbert", "https://m.media-amazon.com/images/I/81Q1Z9sKcRL.jpg",
        "Biography of Winston Churchill and his role in the 20th century.", ["Early Life","WWII","Politics"], "Biography", available=True, tags=["biography","history"])
    add(60, "A Tale of Two Cities", "Charles Dickens", "https://m.media-amazon.com/images/I/81nR8hLgAqL.jpg",
        "Classic novel set during the French Revolution.", ["Recalled to Life","The Golden Thread","The Storm"], "Historical novel", available=False, tags=["classic"])
    add(61, "Les Misérables", "Victor Hugo", "https://m.media-amazon.com/images/I/91RYWwPjYyL.jpg",
        "Epic novel of justice, love and revolution in 19th-century France.", ["Jean Valjean","Cosette","Barricades"], "Historical fiction", available=True, tags=["classic"])
    return B

# ---------------------- Initialize sample data ----------------------
def create_sample_data_if_missing():
    users = safe_load_json(USER_FILE, [])
    books = safe_load_json(BOOK_FILE, [])
    issued = safe_load_json(ISSUED_FILE, [])

    changed = False
    if not users:
        admin = {
            "name": "Admin Librarian",
            "mobile": "9999999999",
            "email": "librarian@example.com",
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "Librarian",
            "favorites": [],
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        safe_save_json(USER_FILE, [admin])
        st.info("Sample librarian created: email `librarian@example.com`, password `admin123`. Change it after login.")
        changed = True

    if not books:
        default_books = get_default_books()
        safe_save_json(BOOK_FILE, default_books)
        st.info("Default books added to books_data.json.")
        changed = True

    if not issued:
        safe_save_json(ISSUED_FILE, [])
        changed = True

    return changed

# Ensure default files exist and sample data is present
safe_load_json(USER_FILE, [])
safe_load_json(BOOK_FILE, [])
safe_load_json(ISSUED_FILE, [])
create_sample_data_if_missing()

# ---------------------- Utility functions ----------------------
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def find_user_by_email(email: str):
    users = safe_load_json(USER_FILE, [])
    for u in users:
        if u.get("email","").lower() == (email or "").lower():
            return u
    return None

def update_user_in_file(user_obj: dict):
    users = safe_load_json(USER_FILE, [])
    for i,u in enumerate(users):
        if u.get("email","").lower() == user_obj.get("email","").lower():
            users[i] = user_obj
            safe_save_json(USER_FILE, users)
            return True
    users.append(user_obj)
    safe_save_json(USER_FILE, users)
    return True

# ---------------------- Business logic ----------------------
def signup(name, mobile, email, password, role):
    if not (name and email and password):
        return False, "Name, email and password are required."
    if find_user_by_email(email):
        return False, "Email already registered."
    u = {
        "name": name.strip(),
        "mobile": mobile.strip(),
        "email": email.strip().lower(),
        "password_hash": hash_password(password.strip()),
        "role": role,
        "favorites": [],
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    users = safe_load_json(USER_FILE, [])
    users.append(u)
    safe_save_json(USER_FILE, users)
    return True, u

def login(email, password):
    if not (email and password):
        return False, "Email and password required."
    u = find_user_by_email(email)
    if not u:
        return False, "No account with that email."
    if u.get("password_hash") != hash_password(password):
        return False, "Incorrect password."
    return True, u

# Books
def load_books() -> List[Dict]:
    return safe_load_json(BOOK_FILE, [])

def save_books(books: List[Dict]):
    safe_save_json(BOOK_FILE, books)

def add_book(book_id, title, author, cover, description, index_text, tags: List[str], price=None,
             publisher=None, isbn=None, pages=None, edition=None, language=None, rating=None):
    books = load_books()
    if any(b.get("id")==book_id for b in books):
        return False, "Book ID already exists."
    book = {
        "id": book_id,
        "title": title,
        "author": author,
        "cover": cover,
        "description": description,
        "index": index_text if isinstance(index_text, list) else (index_text.split("\n") if index_text else []),
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
    books.append(book)
    save_books(books)
    return True, "Book added."

def edit_book(book_id, **fields):
    books = load_books()
    for i,b in enumerate(books):
        if b.get("id") == book_id:
            # if index provided, ensure it's a list
            if "index" in fields and not isinstance(fields["index"], list):
                fields["index"] = fields["index"].split("\n")
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

# Issue/Return
DEFAULT_LOAN_DAYS = 14

def issue_book(book_id, user_email, days=DEFAULT_LOAN_DAYS):
    books = load_books()
    book = next((b for b in books if b.get("id")==book_id), None)
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
    # mark not available and increment
    book["available"] = False
    book["times_issued"] = book.get("times_issued", 0) + 1
    save_books(books)
    return True, rec

def return_book(record_id, user_email=None):
    issued = safe_load_json(ISSUED_FILE, [])
    rec = next((r for r in issued if r.get("record_id")==record_id), None)
    if not rec:
        return False, "Issue record not found."
    if user_email and rec.get("user_email","").lower() != user_email.lower():
        return False, "You are not the borrower for this record."
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

# Recommendation - hybrid
def recommend_for_user(user_email: str, top_n=6):
    books = load_books()
    issued = safe_load_json(ISSUED_FILE, [])
    pop = {b.get("id"): b.get("times_issued", 0) for b in books}
    if not user_email or not any(r.get("user_email","").lower() == user_email.lower() for r in issued):
        candidates = [b for b in books if b.get("available", True)]
        candidates = sorted(candidates, key=lambda x: pop.get(x.get("id"),0), reverse=True)
        return candidates[:top_n]
    user_recs = sorted([r for r in issued if r.get("user_email","").lower() == user_email.lower()], key=lambda x: x.get("issue_date",""))
    last_ids = [r.get("book_id") for r in user_recs[-3:]]
    last_books = [b for b in books if b.get("id") in last_ids]
    last_authors = set(b.get("author","").lower() for b in last_books if b.get("author"))
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
        tag_overlap = len(set(t.lower() for t in b.get("tags", [])) & last_tags)
        score += 2.0 * tag_overlap
        score += pop.get(b.get("id"), 0) / 5.0
        if b.get("available", True):
            score += 1.0
        scores.append((score, b))
    scores.sort(key=lambda x: x[0], reverse=True)
    recs = [b for s,b in scores][:top_n]
    if len(recs) < top_n:
        extra = [b for b in sorted(books, key=lambda x: pop.get(x.get("id"),0), reverse=True) if b not in recs and b.get("id") not in last_ids]
        recs += extra[:(top_n-len(recs))]
    return recs[:top_n]

# ---------------------- Presentation helpers ----------------------
def safe_image(url, width=150):
    try:
        if url:
            st.image(url, width=width)
        else:
            st.image("https://via.placeholder.com/150x220.png?text=No+Cover", width=width)
    except Exception:
        st.image("https://via.placeholder.com/150x220.png?text=No+Cover", width=width)

def show_rating_stars(rating: float, max_stars=5):
    try:
        r = float(rating)
    except:
        r = 0.0
    full = int(round(r))
    full = min(max(full, 0), max_stars)
    stars = "★" * full + "☆" * (max_stars - full)
    return f"{stars} ({r:.1f})"

def days_left(deadline_iso: str) -> int:
    try:
        d = datetime.date.fromisoformat(deadline_iso)
        return (d - datetime.date.today()).days
    except Exception:
        return 0

def book_card(book: dict, user=None):
    left, right = st.columns([1,3])
    with left:
        safe_image(book.get("cover"), width=150)
    with right:
        st.markdown(f"### {book.get('title')}")
        st.markdown(f"**Author:** {book.get('author','-')}  \n**ID:** `{book.get('id')}`")
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
            if book.get("id") in user.get("favorites", []):
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
                if c3.button("✏ Edit", key=f"edit_{book['id']}"):
                    st.session_state.edit_book_id = book["id"]
                    st.session_state.page = "Librarian Console"
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

# ---------------------- Session state init ----------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "book_id" not in st.session_state:
    st.session_state.book_id = None
if "edit_book_id" not in st.session_state:
    st.session_state.edit_book_id = None

# ---------------------- Header ----------------------
st.markdown("<h1 style='margin-bottom:0.1rem'>📚 Smart Library</h1>", unsafe_allow_html=True)
st.markdown("<div style='color:#6c757d;margin-top:0;'>Role-based Streamlit Library with detailed book pages & hybrid recommendations</div>", unsafe_allow_html=True)
st.write("---")

# ---------------------- Sidebar Nav ----------------------
def nav_options():
    if st.session_state.user:
        opts = ["Home", "My Favorites", "My Issued Books", "Recommendations", "About"]
        if st.session_state.user.get("role") == "Librarian":
            opts.insert(1, "Librarian Console")
        return opts
    else:
        return ["Home", "Login", "Sign Up", "About"]

options = nav_options()
if st.session_state.page not in options:
    st.session_state.page = options[0]
choice = st.sidebar.selectbox("Navigation", options, index=options.index(st.session_state.page))
st.session_state.page = choice

if st.session_state.user:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Signed in as**  \n{st.session_state.user.get('name')}  \n{st.session_state.user.get('email')}  \n**Role:** {st.session_state.user.get('role')}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "Home"
        st.experimental_rerun()

# ---------------------- Pages ----------------------
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
        text = " ".join([str(b.get(k,"")).lower() for k in ("title","author","id")]) + " " + " ".join([t.lower() for t in b.get("tags",[])] + [b.get("genre","").lower()])
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
    # If already logged in, redirect to Home
    if st.session_state.user:
        st.info("Already logged in — redirected to Home.")
        st.session_state.page = "Home"
        st.experimental_rerun()
        return

    st.subheader("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            ok, resp = login(email, password)
            if ok:
                st.session_state.user = resp
                st.session_state.page = "Home"
                st.success(f"Welcome back, {resp.get('name')} — redirected to Home.")
                st.experimental_rerun()
            else:
                st.error(resp)

def page_signup():
    # If already logged in, redirect to Home
    if st.session_state.user:
        st.info("Already logged in — redirected to Home.")
        st.session_state.page = "Home"
        st.experimental_rerun()
        return

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
                st.session_state.user = resp
                st.session_state.page = "Home"
                st.success("Account created and logged in — redirected to Home.")
                st.experimental_rerun()
            else:
                st.error(resp)

def page_about():
    st.subheader("About")
    st.write("""
    Smart Library — features:
    - Role-based authentication (User / Librarian)
    - View all books with cover, details, and index
    - Librarian-only: add / edit / delete books
    - Users: add to favorites, issue & return books
    - Issued book tracking + deadline & days-left
    - Book detail page with metadata similar to shopping sites
    - Hybrid recommender (author + tags + popularity + availability)
    - Robust JSON handling to avoid crashes on empty/corrupt files
    """)

def page_my_favorites():
    if not st.session_state.user:
        st.warning("Please login to view your book list.")
        return
    st.subheader("My Book List (Favorites)")
    favs = st.session_state.user.get("favorites", [])
    books_dict = {b.get("id"): b for b in load_books()}
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
    issued = get_user_issued(st.session_state.user.get("email"))
    if not issued:
        st.info("You have no issued books.")
        return
    books = {b.get("id"): b for b in load_books()}
    for rec in issued:
        b = books.get(rec.get("book_id"), {})
        left = days_left(rec.get("deadline",""))
        col1,col2 = st.columns([3,1])
        with col1:
            st.markdown(f"**{b.get('title','-')}** by {b.get('author','-')}")
            st.write(f"Issued: {rec.get('issue_date')} • Due: {rec.get('deadline')} • Days left: {left}")
        with col2:
            if st.button("Return Book", key=f"return_{rec.get('record_id')}"):
                ok,msg = return_book(rec.get('record_id'), st.session_state.user.get("email"))
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
    recs = recommend_for_user(st.session_state.user.get("email"), top_n=8)
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
        st.markdown(f"**Availability:** {'Available' if book.get('available', True) else 'Checked out'}")
        if st.session_state.user:
            if book.get("id") in st.session_state.user.get("favorites", []):
                if st.button("★ Favorited (Remove)"):
                    remove_favorite(st.session_state.user.get("email"), book.get("id"))
                    st.session_state.user = find_user_by_email(st.session_state.user.get("email"))
                    st.experimental_rerun()
            else:
                if st.button("☆ Add to Book List"):
                    add_favorite(st.session_state.user.get("email"), book.get("id"))
                    st.session_state.user = find_user_by_email(st.session_state.user.get("email"))
                    st.experimental_rerun()
            if st.session_state.user.get("role") != "Librarian":
                if book.get("available", True):
                    if st.button("📚 Issue This Book"):
                        ok, resp = issue_book(book.get("id"), st.session_state.user.get("email"))
                        if ok:
                            st.success(f"Issued — due {resp.get('deadline')}")
                        else:
                            st.error(resp)
                        st.experimental_rerun()
            else:
                if st.button("✏ Edit Book (Console)"):
                    st.session_state.edit_book_id = book.get("id")
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
        idx = book.get("index", [])
        if isinstance(idx, list):
            for it in idx:
                st.write(f"- {it}")
        else:
            st.write(idx)
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
    same_author = [b for b in load_books() if b.get("author","").lower() == book.get("author","").lower() and b.get("id") != book.get("id")]
    shown = 0
    if same_author:
        for sb in same_author[:3]:
            book_card(sb, st.session_state.user)
            shown += 1
    if shown < 6:
        recs = recommend_for_user(st.session_state.user.get("email") if st.session_state.user else "", top_n=6)
        for rb in recs:
            if rb.get("id") != book.get("id") and shown < 6:
                book_card(rb, st.session_state.user)
                shown += 1

def page_librarian_console():
    if not st.session_state.user or st.session_state.user.get("role") != "Librarian":
        st.warning("Librarian access only.")
        return
    st.subheader("Librarian Console")
    mode = st.selectbox("Mode", ["Add Book","Edit Book","All Issued"])
    if mode == "Add Book":
        st.markdown("### Add a book")
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
            index_text = st.text_area("Index / Overview (one per line)")
            submitted = st.form_submit_button("Add Book")
            if submitted:
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                price_val = float(price) if price.strip() else None
                ok,msg = add_book(book_id.strip(), title.strip(), author.strip(), cover.strip(), description.strip(), index_text.strip().splitlines(), tag_list,
                                 price=price_val, publisher=publisher.strip() or None, isbn=isbn.strip() or None, pages=pages.strip() or None,
                                 edition=edition.strip() or None, language=language.strip() or None, rating=rating)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
    elif mode == "Edit Book":
        st.markdown("### Edit a book")
        books = load_books()
        if not books:
            st.info("No books.")
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
                index_text = st.text_area("Index / Overview (one per line)", value="\n".join(book.get("index",[])))
                submitted = st.form_submit_button("Save Changes")
                if submitted:
                    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                    price_val = float(price) if price.strip() else None
                    ok,msg = edit_book(book.get("id"), title=title.strip(), author=author.strip(), cover=cover.strip(),
                                       price=price_val, publisher=publisher.strip() or None, isbn=isbn.strip() or None,
                                       pages=pages.strip() or None, edition=edition.strip() or None,
                                       language=language.strip() or None, tags=tag_list,
                                       rating=rating, description=description.strip(), index=index_text.strip().splitlines())
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
    else:
        st.markdown("### All Issued Records")
        issued = get_user_issued()
        books_map = {b.get("id"):b for b in load_books()}
        if not issued:
            st.info("No issued records.")
            return
        for rec in issued:
            b = books_map.get(rec.get("book_id"), {})
            st.write(f"- **{b.get('title','-')}** | Borrower: {rec.get('user_email')} | Due: {rec.get('deadline')}")
            if st.button(f"Return {rec.get('record_id')}", key=f"libret_{rec.get('record_id')}"):
                ok,msg = return_book(rec.get('record_id'))
                if ok:
                    st.success("Returned")
                    st.experimental_rerun()
                else:
                    st.error(msg)

# Dispatcher
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

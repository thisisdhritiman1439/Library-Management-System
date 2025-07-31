# 📚 Library Management System using Python and Streamlit

A full-featured, role-based **Library Management System** built using **Python** and **Streamlit**, designed to digitize and automate library operations such as book issuing, returns, viewing, recommendations, and more. The system supports both **Students** and **Librarians**, offering secure login, detailed book previews, personalized recommendations, and data stored in **JSON** format.

---

## 🚀 Features

### 🔐 User Authentication
- Signup/Login with **Name**, **Mobile Number**, **Email**, **Password**, and **Role** (Student/Librarian/Others).
- Role-based access (Librarian-exclusive features).

### 📖 Book Management
- **View All Books** with:
  - Book ID, Title, Author
  - Cover image, Description
  - Availability Status

- **Add New Book** *(Librarian only)*  
- **Delete Book** *(Librarian only)*  
- **Book Overview with Index Page**  
- JSON-based book storage for portability and flexibility.

### 📋 Student Utilities
- **Add to Book List** (Wishlist/Favorites before issuing)
- **Issue Book** with:
  - Due date tracking
  - Countdown on days remaining
- **Return Book** to mark availability
- **View Issued Books**

### 🤖 Book Recommendation System
- Suggests books based on past borrowing history and category.
- Enhances discovery of related books.

---

## 🛠️ Tech Stack

| Technology | Usage |
|------------|-------|
| `Python`   | Backend & Logic |
| `Streamlit` | Frontend UI |
| `JSON` | Data storage for books and users |
| `Pandas` | Data processing and management |
| `Streamlit Cloud` | Deployment platform |
| `GitHub` | Version Control & Hosting |

---

## 📂 Folder Structure

```

📁 library-management-system/
│
├── 📄 app.py                  # Main Streamlit application
├── 📁 assets/                 # Book cover images
├── 📄 books.json              # Book data with descriptions & availability
├── 📄 users.json              # User data (students/librarians)
├── 📄 issued\_books.json       # Issued book records
├── 📄 requirements.txt        # Python dependencies
└── 📄 README.md               # This file

````

---

## 🖥️ Live Demo

🌐 **Try the app now**:  
[🔗 Live Streamlit App](https://library-management-system-ef4yqfughzl8otmr6uwkzy.streamlit.app/)

---

## 📌 How to Run Locally

1. Clone this repo:
```bash
git clone https://github.com/thisisdhritiman1439/Library-Management-System.git
cd Library-Management-System
````

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
streamlit run app.py
```

---

## 📷 Screenshots

> Add screenshots in the `assets/` folder and embed them here:

* ✅ Login & Sign Up
* 📚 View All Books
* 📘 Book Description + Index
* ➕ Add/Delete Book
* 📥 Issue/Return Book
* 🤖 Recommendation Panel

---

## 📈 Future Enhancements

* 📧 Email notifications for book due reminders.
* 🔍 Search & filter system for faster book lookup.
* 🧾 Export issued book reports to CSV.
* 🛡️ OTP-based authentication.
* 📊 Admin Analytics Dashboard.

---

## 👨‍💻 Developers

| Name                     | Role                     |
| ------------------------ | ------------------------ |
| Khandakar Nafees Hossain | Project Lead & Developer |
| Dhritiman Bera           | Developer & Designer     |
| Parthib Mahapatra        | Tester & Deployment      |
| Mr. Subhabrata Sengupta  | Faculty Guide            |
| Dr. Rupayan Das          | Faculty Guide            |

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🤝 Acknowledgments

* Built with ❤️ using Python and Streamlit
* Inspired by the real-world challenges of manual library systems
]

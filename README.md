# 🗳️ Electronic Voting System — Pakistan
### Final Year University Database Project

A fully functional desktop Electronic Voting System built with Python (Tkinter), MySQL, and MVC architecture — styled for Pakistan's National & Provincial Assembly elections.

---

## 📋 Features

### Admin Portal
- Secure admin login
- Dashboard with live statistics
- Approve / Reject voter registrations
- Manage constituencies (NA + PP)
- Manage candidates with party symbol images
- Schedule & control elections
- View live results with bar & pie charts
- Full audit log with CSV export

### Voter Portal
- Registration (pending admin approval)
- Secure login (approved voters only)
- Vote once for National Assembly
- Vote once for Provincial Assembly
- Constituency-restricted voting
- Election-time enforcement
- Vote history with timestamps

---

## ⚙️ Requirements

- Python 3.10 or higher
- MySQL 8.0 or higher
- pip packages (see requirements.txt)

---

## 🚀 Setup Instructions

### Step 1 — Install Python packages

```bash
pip install -r requirements.txt
```

### Step 2 — Set up MySQL

Open MySQL Workbench or the MySQL command line and run:

```sql
CREATE DATABASE IF NOT EXISTS evs_pakistan;
```

Then run the schema file:

```bash
mysql -u root -p evs_pakistan < sql/schema.sql
```

Or paste the contents of `sql/schema.sql` into MySQL Workbench and execute.

### Step 3 — Configure database credentials

Open `database/connection.py` and update:

```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "YOUR_MYSQL_PASSWORD",   # ← change this
    "database": "evs_pakistan",
    ...
}
```

### Step 4 — Run the application

```bash
python app.py
```

---

## 🔐 Default Accounts

### Admin
| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `Admin@123`|

### Sample Voters (approved)
| Username       | Password    | Status   |
|----------------|-------------|----------|
| `ahmed_hassan` | `Voter@123` | Approved |
| `fatima_noor`  | `Voter@123` | Approved |
| `usman_ali`    | `Voter@123` | Approved |
| `sara_khan`    | `Voter@123` | Pending  |
| `bilal_asif`   | `Voter@123` | Pending  |

---

## 📁 Project Structure

```
electronic_voting_system/
│
├── app.py                      # Entry point
│
├── database/
│   ├── __init__.py
│   └── connection.py           # DB connection & query helper
│
├── models/
│   ├── __init__.py
│   ├── admin_model.py          # Admin data access
│   ├── voter_model.py          # Voter data access
│   └── models.py               # Constituency, Candidate, Vote, Election, Audit
│
├── controllers/
│   ├── __init__.py
│   └── controllers.py          # Auth, Voter, Admin business logic
│
├── views/
│   ├── __init__.py
│   ├── theme.py                # Dark theme, colors, widget factories
│   ├── auth_view.py            # Login + Registration window
│   ├── voter_view.py           # Voter portal (dashboard, voting, history)
│   └── admin_view.py           # Admin portal (all management tabs)
│
├── assets/
│   └── symbols/                # Party symbol images stored here
│
├── sql/
│   └── schema.sql              # Full DB schema + sample data
│
├── utils/
│   ├── __init__.py
│   └── helpers.py              # Hashing, validation, session management
│
├── requirements.txt
└── README.md
```

---

## 🗄️ Database Schema

| Table               | Purpose                              |
|---------------------|--------------------------------------|
| `admins`            | Admin accounts                       |
| `voters`            | Registered voters (pending/approved) |
| `constituencies`    | NA and PA constituencies             |
| `candidates`        | Election candidates with party info  |
| `election_schedule` | Election timing and status           |
| `votes`             | Cast votes (duplicate prevention)    |
| `audit_logs`        | Full system audit trail              |

---

## 🛡️ Security Features

- Passwords hashed with **bcrypt**
- Parameterized queries prevent **SQL injection**
- Duplicate voting prevented at **database level** (UNIQUE constraint)
- Session management for login state
- Input validation for CNIC, username, password strength
- Audit logging for all actions

---

## 📊 Results & Analytics

- Real-time vote counts per candidate
- Constituency-wise results
- Winner highlighted in gold
- Turnout percentage
- **Bar chart** — top candidates by vote count
- **Pie chart** — party-wise vote share
- CSV export for audit logs

---

## 💡 Notes

- The first run automatically initialises all database tables
- Party symbol images can be uploaded via Admin → Candidates → Browse
- Election timing is enforced: voters cannot vote outside scheduled windows
- An active election must be scheduled for voting to work
- Voters can only vote for candidates in their own constituency

---

*Built for Final Year University Database Project — Pakistan Electoral System Simulation*

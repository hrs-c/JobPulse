# 🚀 JobPulse — Job Portal Web Application

A full-featured job portal built with **Flask + SQLite + Bootstrap**, covering all course requirements.

---

## 📁 Project Structure

```
job_portal/
├── app.py                  ← Main Flask app (routes, models, logic)
├── requirements.txt        ← Python dependencies
├── jobportal.db            ← SQLite database (auto-created)
└── templates/
    ├── base.html           ← Shared layout + design system
    ├── index.html          ← Homepage (hero, stats, categories, job grid)
    ├── jobs.html           ← Job listing + search/filter
    ├── job_detail.html     ← Individual job view + apply button
    ├── login.html          ← Login form
    ├── register.html       ← Registration with role selector
    ├── apply.html          ← Job application form
    ├── seeker_dashboard.html   ← Job seeker: view applications
    ├── employer_dashboard.html ← Employer: manage listings
    ├── post_job.html       ← Employer: create/edit job
    ├── applications.html   ← Employer: review applicants
    └── admin_dashboard.html    ← Admin: manage users & jobs
```

---

## ⚙️ Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
http://127.0.0.1:5000
```

The SQLite database and seed data are created **automatically** on first run.

---

## 👤 Demo Accounts

| Role     | Email                  | Password     |
|----------|------------------------|--------------|
| Admin    | admin@jobportal.com    | admin123     |
| Employer | hr@techcorp.com        | employer123  |
| Employer | hr@datasol.com         | employer123  |
| Seeker   | alice@email.com        | seeker123    |

---

## ✅ Features Implemented

### User Roles & Auth
- [x] Registration with role selection (Job Seeker / Employer)
- [x] Login / Logout with session management
- [x] Password hashing with Werkzeug
- [x] Role-based access control (decorators)

### Job Seeker
- [x] Browse all job listings
- [x] Search by keyword, location, category, job type
- [x] View detailed job page
- [x] Apply with optional cover letter
- [x] Dashboard showing all applications + status

### Employer
- [x] Post new job (title, description, salary, location, category, type)
- [x] Edit existing job listings
- [x] Toggle jobs active/closed
- [x] View all applicants per job
- [x] Update application status (Pending → Reviewed → Accepted/Rejected)

### Admin
- [x] View all users with roles
- [x] Delete any user
- [x] View all jobs + application counts
- [x] Delete any job listing
- [x] Platform-wide stats (users, jobs, applications)

### Frontend
- [x] Responsive design (Bootstrap 5)
- [x] Custom design system (CSS variables, Syne + DM Sans fonts)
- [x] Category browsing cards
- [x] Animated hover effects on job cards
- [x] Job type filter pills
- [x] Stat boxes on homepage + dashboards

---

## 🗄️ Database Models

### User
| Field     | Type    | Notes                         |
|-----------|---------|-------------------------------|
| id        | Integer | Primary key                   |
| name      | String  |                               |
| email     | String  | Unique                        |
| password  | String  | Hashed (Werkzeug)             |
| role      | String  | seeker / employer / admin     |
| company   | String  | Employer only                 |
| created_at| DateTime|                               |

### Job
| Field       | Type    | Notes                       |
|-------------|---------|-----------------------------|
| id          | Integer | Primary key                 |
| title       | String  |                             |
| description | Text    |                             |
| salary      | String  | Optional                    |
| location    | String  |                             |
| category    | String  | Technology, Design, etc.    |
| job_type    | String  | Full-time, Part-time, Remote|
| employer_id | FK→User |                             |
| is_active   | Boolean |                             |

### Application
| Field        | Type     | Notes                         |
|--------------|----------|-------------------------------|
| id           | Integer  | Primary key                   |
| job_id       | FK→Job   |                               |
| applicant_id | FK→User  |                               |
| cover_letter | Text     | Optional                      |
| status       | String   | pending/reviewed/accepted/rejected |
| applied_at   | DateTime |                               |

---

## 🛠️ Tech Stack

| Layer      | Technology           |
|------------|----------------------|
| Backend    | Python 3 + Flask     |
| ORM        | Flask-SQLAlchemy     |
| Database   | SQLite               |
| Frontend   | HTML5 + CSS3         |
| CSS Fx     | Bootstrap 5          |
| Icons      | Bootstrap Icons      |
| Fonts      | Google Fonts (Syne + DM Sans) |
| Auth       | Werkzeug (password hashing) |

---

## 🔑 Key Flask Concepts Demonstrated

- **Blueprints / Routes** — GET/POST routes for all features
- **SQLAlchemy ORM** — Models with relationships, queries with filters
- **Session management** — Login state, role checks
- **Jinja2 templating** — Template inheritance (`extends`), `for`/`if`, filters
- **Flash messages** — User feedback on actions
- **Form handling** — `request.form`, redirect after POST
- **Decorators** — `login_required`, `role_required(*roles)`

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jobportal-secret-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobportal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'seeker', 'employer', 'admin'
    company = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    jobs = db.relationship('Job', backref='employer', lazy=True)
    applications = db.relationship('Application', backref='applicant', lazy=True)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary = db.Column(db.String(100))
    location = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    job_type = db.Column(db.String(50))  # Full-time, Part-time, Remote
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('Application', backref='job', lazy=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(30), default='pending')  # pending, reviewed, accepted, rejected
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─────────────────────────────────────────
# AUTH DECORATORS
# ─────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ─────────────────────────────────────────
# ROUTES — PUBLIC
# ─────────────────────────────────────────

@app.route('/')
def index():
    recent_jobs = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).limit(6).all()
    total_jobs = Job.query.filter_by(is_active=True).count()
    total_companies = db.session.query(User.company).filter(User.role == 'employer').distinct().count()
    total_seekers = User.query.filter_by(role='seeker').count()
    categories = db.session.query(Job.category, db.func.count(Job.id)).group_by(Job.category).all()
    return render_template('index.html', jobs=recent_jobs, total_jobs=total_jobs,
                           total_companies=total_companies, total_seekers=total_seekers,
                           categories=categories)

@app.route('/jobs')
def jobs():
    query = request.args.get('q', '')
    location = request.args.get('location', '')
    category = request.args.get('category', '')
    job_type = request.args.get('type', '')

    job_query = Job.query.filter_by(is_active=True)
    if query:
        job_query = job_query.filter(
            db.or_(Job.title.ilike(f'%{query}%'), Job.description.ilike(f'%{query}%'))
        )
    if location:
        job_query = job_query.filter(Job.location.ilike(f'%{location}%'))
    if category:
        job_query = job_query.filter_by(category=category)
    if job_type:
        job_query = job_query.filter_by(job_type=job_type)

    all_jobs = job_query.order_by(Job.created_at.desc()).all()
    categories = db.session.query(Job.category).distinct().all()
    locations = db.session.query(Job.location).distinct().all()
    return render_template('jobs.html', jobs=all_jobs, categories=categories,
                           locations=locations, query=query, sel_location=location,
                           sel_category=category, sel_type=job_type)

@app.route('/jobs/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    already_applied = False
    if 'user_id' in session:
        already_applied = Application.query.filter_by(
            job_id=job_id, applicant_id=session['user_id']
        ).first() is not None
    return render_template('job_detail.html', job=job, already_applied=already_applied)

# ─────────────────────────────────────────
# ROUTES — AUTH
# ─────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        company = request.form.get('company', '')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        user = User(
            name=name, email=email,
            password=generate_password_hash(password),
            role=role, company=company
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['name'] = user.name
            session['role'] = user.role
            flash(f'Welcome back, {user.name}!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'employer':
                return redirect(url_for('employer_dashboard'))
            else:
                return redirect(url_for('seeker_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# ─────────────────────────────────────────
# ROUTES — JOB SEEKER
# ─────────────────────────────────────────

@app.route('/dashboard/seeker')
@role_required('seeker')
def seeker_dashboard():
    user = User.query.get(session['user_id'])
    applications = Application.query.filter_by(applicant_id=user.id).order_by(Application.applied_at.desc()).all()
    return render_template('seeker_dashboard.html', user=user, applications=applications)

@app.route('/jobs/<int:job_id>/apply', methods=['GET', 'POST'])
@role_required('seeker')
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)
    existing = Application.query.filter_by(job_id=job_id, applicant_id=session['user_id']).first()
    if existing:
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('job_detail', job_id=job_id))
    if request.method == 'POST':
        application = Application(
            job_id=job_id,
            applicant_id=session['user_id'],
            cover_letter=request.form.get('cover_letter', '')
        )
        db.session.add(application)
        db.session.commit()
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('seeker_dashboard'))
    return render_template('apply.html', job=job)

# ─────────────────────────────────────────
# ROUTES — EMPLOYER
# ─────────────────────────────────────────

@app.route('/dashboard/employer')
@role_required('employer')
def employer_dashboard():
    user = User.query.get(session['user_id'])
    jobs = Job.query.filter_by(employer_id=user.id).order_by(Job.created_at.desc()).all()
    return render_template('employer_dashboard.html', user=user, jobs=jobs)

@app.route('/jobs/post', methods=['GET', 'POST'])
@role_required('employer')
def post_job():
    if request.method == 'POST':
        job = Job(
            title=request.form['title'],
            description=request.form['description'],
            salary=request.form.get('salary', ''),
            location=request.form['location'],
            category=request.form['category'],
            job_type=request.form.get('job_type', 'Full-time'),
            employer_id=session['user_id']
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('employer_dashboard'))
    return render_template('post_job.html')

@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@role_required('employer')
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != session['user_id']:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('employer_dashboard'))
    if request.method == 'POST':
        job.title = request.form['title']
        job.description = request.form['description']
        job.salary = request.form.get('salary', '')
        job.location = request.form['location']
        job.category = request.form['category']
        job.job_type = request.form.get('job_type', 'Full-time')
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('employer_dashboard'))
    return render_template('post_job.html', job=job)

@app.route('/jobs/<int:job_id>/toggle', methods=['POST'])
@role_required('employer')
def toggle_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    job.is_active = not job.is_active
    db.session.commit()
    return jsonify({'status': 'active' if job.is_active else 'inactive'})

@app.route('/jobs/<int:job_id>/applications')
@role_required('employer')
def view_applications(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != session['user_id']:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('employer_dashboard'))
    applications = Application.query.filter_by(job_id=job_id).all()
    return render_template('applications.html', job=job, applications=applications)

@app.route('/applications/<int:app_id>/status', methods=['POST'])
@role_required('employer')
def update_status(app_id):
    application = Application.query.get_or_404(app_id)
    new_status = request.form['status']
    application.status = new_status
    db.session.commit()
    flash('Application status updated.', 'success')
    return redirect(request.referrer or url_for('employer_dashboard'))

# ─────────────────────────────────────────
# ROUTES — ADMIN
# ─────────────────────────────────────────

@app.route('/dashboard/admin')
@role_required('admin')
def admin_dashboard():
    users = User.query.all()
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    applications = Application.query.all()
    stats = {
        'total_users': len(users),
        'total_jobs': len(jobs),
        'total_applications': len(applications),
        'active_jobs': sum(1 for j in jobs if j.is_active),
    }
    return render_template('admin_dashboard.html', users=users, jobs=jobs, stats=stats)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/jobs/<int:job_id>/delete', methods=['POST'])
@role_required('admin')
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

# ─────────────────────────────────────────
# INIT DB + SEED
# ─────────────────────────────────────────

def seed_data():
    if User.query.count() > 0:
        return
    admin = User(name='Admin', email='admin@jobportal.com',
                 password=generate_password_hash('admin123'), role='admin')
    employer = User(name='TechCorp HR', email='hr@techcorp.com',
                    password=generate_password_hash('employer123'),
                    role='employer', company='TechCorp Inc.')
    employer2 = User(name='DataSolutions', email='hr@datasol.com',
                     password=generate_password_hash('employer123'),
                     role='employer', company='DataSolutions Ltd.')
    seeker = User(name='Alice Johnson', email='alice@email.com',
                  password=generate_password_hash('seeker123'), role='seeker')
    db.session.add_all([admin, employer, employer2, seeker])
    db.session.commit()

    jobs_data = [
        ('Senior Python Developer', 'We are looking for an experienced Python developer to join our team. You will work on backend services, APIs, and data pipelines.', '₹12,00,000 – ₹18,00,000', 'Bangalore', 'Technology', 'Full-time', employer.id),
        ('React Frontend Engineer', 'Build stunning user interfaces with React and TypeScript. Experience with REST APIs and state management required.', '₹8,00,000 – ₹14,00,000', 'Mumbai', 'Technology', 'Full-time', employer.id),
        ('Data Scientist', 'Analyze large datasets and build ML models to drive business decisions. Python, scikit-learn, and SQL required.', '₹10,00,000 – ₹20,00,000', 'Remote', 'Data Science', 'Remote', employer2.id),
        ('DevOps Engineer', 'Manage CI/CD pipelines, containerization with Docker/Kubernetes, and cloud infrastructure on AWS.', '₹9,00,000 – ₹15,00,000', 'Hyderabad', 'Technology', 'Full-time', employer.id),
        ('Product Manager', 'Lead product strategy, work cross-functionally with engineering and design to ship great products.', '₹15,00,000 – ₹25,00,000', 'Delhi', 'Management', 'Full-time', employer2.id),
        ('UI/UX Designer', 'Create beautiful and intuitive designs for web and mobile. Figma and design systems experience needed.', '₹6,00,000 – ₹12,00,000', 'Pune', 'Design', 'Part-time', employer.id),
    ]
    for title, desc, salary, loc, cat, jtype, emp_id in jobs_data:
        db.session.add(Job(title=title, description=desc, salary=salary,
                           location=loc, category=cat, job_type=jtype, employer_id=emp_id))
    db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

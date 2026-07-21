from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import date, timedelta, datetime
from functools import wraps
from sqlalchemy import select, or_, func
from werkzeug.security import generate_password_hash
import secrets
import os
from werkzeug.utils import secure_filename
from flask import current_app

auth = Blueprint('auth', __name__)
main = Blueprint('main', __name__)


def db():
    from flask_sqlalchemy import SQLAlchemy
    for ext in current_app.extensions.values():
        if isinstance(ext, SQLAlchemy):
            return ext
    raise RuntimeError("No SQLAlchemy extension found")


def m():
    import models
    return models


# ─── Role Decorators ───────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def librarian_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
            flash('Librarian access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


# ─── Auth ──────────────────────────────────────────

@auth.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


# ─── Member Login ──────────────────────────────────

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        session = db().session

        user = session.execute(
            select(m().User).where(m().User.email == email)
        ).scalar_one_or_none()

        if user is None:
            flash('User not found.', 'danger')
            return render_template('login.html')

        if not user.check_password(password):
            flash('Incorrect password.', 'danger')
            return render_template('login.html')

        # Member login should only allow members
        if user.role == 'admin':
            flash('Please login through the Admin portal.', 'warning')
            return redirect(url_for('auth.admin_login'))

        if user.role == 'librarian':
            flash('Please login through the Librarian portal.', 'warning')
            return redirect(url_for('auth.librarian_login'))

        login_user(user, remember=('remember' in request.form))
        flash(f'Welcome {user.name}!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')


# ─── Logout ────────────────────────────────────────

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


# ─── Register ──────────────────────────────────────

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        session = db().session

        name = request.form.get('name')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        student_id = request.form.get('student_id')
        department = request.form.get('department')

        existing = session.execute(
            select(m().User).where(m().User.email == email)
        ).scalar_one_or_none()

        if existing:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        user = m().User(
            name=name,
            email=email,
            role='member',
            student_id=student_id or None,
            department=department,
            password_hash=generate_password_hash(password)
        )

        session.add(user)
        session.commit()

        flash('Account created! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# ─── Admin Login ───────────────────────────────────

@auth.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        session = db().session

        user = session.execute(
            select(m().User).where(m().User.email == email)
        ).scalar_one_or_none()

        if user is None:
            flash('Admin account not found.', 'danger')
            return render_template('admin_login.html')

        if not user.check_password(password):
            flash('Incorrect password.', 'danger')
            return render_template('admin_login.html')

        if user.role.lower() != 'admin':
            flash(f'Access denied. Your role is "{user.role}".', 'danger')
            return render_template('admin_login.html')

        login_user(user)
        flash(f'Welcome Admin {user.name}!', 'success')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('admin_login.html')


# ─── Librarian Login ───────────────────────────────
@auth.route('/librarian/login', methods=['GET', 'POST'])
def librarian_login():

    if current_user.is_authenticated:
        logout_user()

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        session = db().session

        user = session.execute(
            select(m().User).where(m().User.email == email)
        ).scalar_one_or_none()

        if user is None:
            flash("Librarian account not found.", "danger")
            return render_template('librarian_login.html')

        if not user.check_password(password):
            flash("Incorrect password.", "danger")
            return render_template('librarian_login.html')

        # Allow librarian and admin
        if user.role not in ['librarian', 'admin']:
            flash("This account is not authorized as a librarian.", "danger")
            return render_template('librarian_login.html')

        login_user(user)
        flash(f"Welcome {user.name}!", "success")
        return redirect(url_for('main.librarian_desk'))

    return render_template('librarian_login.html')


# ─── Google OAuth ──────────────────────────────────
@auth.route('/auth/google')
def google_login():
    google = current_app.extensions['google_oauth']
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@auth.route('/auth/google/callback')
def google_callback():
    google  = current_app.extensions['google_oauth']
    token   = google.authorize_access_token()
    info    = token.get('userinfo')

    if not info:
        flash('Google login failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    session = db().session
    email   = info['email']
    name    = info.get('name', email)

    user = session.execute(
        select(m().User).where(m().User.email == email)
    ).scalar_one_or_none()

    if not user:
        user = m().User(
            name=name, email=email, role='member',
            password_hash=generate_password_hash(secrets.token_hex(16))
        )
        session.add(user)
        session.commit()
        flash(f'Account created for {name}! Welcome to SmartLib.', 'success')

    login_user(user)
    flash(f'Welcome, {user.name}!', 'success')
    return redirect(url_for('main.dashboard'))


# ─── GitHub OAuth ──────────────────────────────────
@auth.route('/auth/github')
def github_login():
    github = current_app.extensions['github_oauth']
    redirect_uri = url_for('auth.github_callback', _external=True)
    return github.authorize_redirect(redirect_uri)


@auth.route('/auth/github/callback')
def github_callback():
    github  = current_app.extensions['github_oauth']
    token   = github.authorize_access_token()

    user_resp = github.get('user', token=token)
    info      = user_resp.json()

    email = info.get('email')
    if not email:
        emails_resp = github.get('user/emails', token=token)
        for e in emails_resp.json():
            if e.get('primary') and e.get('verified'):
                email = e.get('email')
                break

    if not email:
        flash('Could not get email from GitHub.', 'danger')
        return redirect(url_for('auth.login'))

    name    = info.get('name') or info.get('login') or email
    session = db().session

    user = session.execute(
        select(m().User).where(m().User.email == email)
    ).scalar_one_or_none()

    if not user:
        user = m().User(
            name=name, email=email, role='member',
            password_hash=generate_password_hash(secrets.token_hex(16))
        )
        session.add(user)
        session.commit()
        flash(f'Account created for {name}! Welcome to SmartLib.', 'success')

    login_user(user)
    flash(f'Welcome, {user.name}!', 'success')
    return redirect(url_for('main.dashboard'))


# ─── Dashboard ─────────────────────────────────────
@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    if current_user.role == 'librarian':
        return redirect(url_for('main.librarian_desk'))

    session = db().session
    active_loans = session.execute(
        select(m().IssuedBook).where(
            m().IssuedBook.user_id == current_user.id,
            m().IssuedBook.status == 'active'
        )
    ).scalars().all()
    overdue = [b for b in active_loans if b.is_overdue]
    unpaid_fines = session.execute(
        select(m().Fine).where(
            m().Fine.user_id == current_user.id,
            m().Fine.status == 'unpaid'
        )
    ).scalars().all()
    notifications = session.execute(
        select(m().Notification).where(
            m().Notification.user_id == current_user.id,
            m().Notification.is_read == False
        ).order_by(m().Notification.created_at.desc()).limit(5)
    ).scalars().all()

    return render_template('dashboard.html',
                           active_loans=active_loans,
                           overdue=overdue,
                           unpaid_fines=unpaid_fines,
                           notifications=notifications,
                           today=date.today())


@main.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    session       = db().session
    total_books   = session.execute(select(func.count(m().Book.id))).scalar()
    total_members = session.execute(
        select(func.count(m().User.id)).where(m().User.role == 'member')
    ).scalar()
    active_loans  = session.execute(
        select(func.count(m().IssuedBook.id)).where(m().IssuedBook.status == 'active')
    ).scalar()
    all_active    = session.execute(
        select(m().IssuedBook).where(m().IssuedBook.status == 'active')
    ).scalars().all()
    overdue_books = [b for b in all_active if b.is_overdue]
    total_fines   = session.execute(
        select(func.sum(m().Fine.amount)).where(m().Fine.status == 'unpaid')
    ).scalar() or 0

    return render_template('admin_dashboard.html',
                           total_books=total_books,
                           total_members=total_members,
                           active_loans=active_loans,
                           overdue_books=overdue_books,
                           total_fines=total_fines)


@main.route('/librarian')
@login_required
@librarian_required
def librarian_desk():
    session      = db().session
    all_active   = session.execute(
        select(m().IssuedBook).where(m().IssuedBook.status == 'active')
    ).scalars().all()
    overdue      = [b for b in all_active if b.is_overdue]
    pending_fines = session.execute(
        select(func.sum(m().Fine.amount)).where(m().Fine.status == 'unpaid')
    ).scalar() or 0

    return render_template('librarian_desk.html',
                           active_loans=len(all_active),
                           overdue=overdue,
                           pending_fines=pending_fines)


# ─── Books ─────────────────────────────────────────
@main.route('/books')
@login_required
def books():
    session      = db().session
    category_id  = request.args.get('category')
    search       = request.args.get('search', '')
    availability = request.args.get('availability')

    stmt = select(m().Book)
    if search:
        stmt = stmt.where(or_(
            m().Book.title.ilike(f'%{search}%'),
            m().Book.author.ilike(f'%{search}%')
        ))
    if category_id:
        stmt = stmt.where(m().Book.category_id == category_id)
    if availability == 'available':
        stmt = stmt.where(m().Book.available_qty > 0)

    all_books  = session.execute(stmt).scalars().all()
    categories = session.execute(select(m().Category)).scalars().all()
    return render_template('books.html', books=all_books,
                           categories=categories, search=search)


@main.route('/books/<int:book_id>')
@login_required
def book_detail(book_id):
    session = db().session
    book = session.get(m().Book, book_id)

    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('main.books'))

    history = session.execute(
        select(m().IssuedBook)
        .where(m().IssuedBook.book_id == book_id)
        .order_by(m().IssuedBook.issue_date.desc())
        .limit(10)
    ).scalars().all()

    active_loan = None
    if current_user.role == 'member':
        active_loan = session.execute(
            select(m().IssuedBook).where(
                m().IssuedBook.user_id == current_user.id,
                m().IssuedBook.book_id == book_id,
                m().IssuedBook.status == 'active'
            )
        ).scalar_one_or_none()

    preview_url = None

    try:
        query = f'intitle:"{book.title}" inauthor:"{book.author}"'

        response = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={
                "q": query,
                "maxResults": 1
            },
            timeout=10
        )

        print("Status Code:", response.status_code)

        if response.status_code == 200:
            data = response.json()
            print("Google Books Response:", data)

            if data.get("items"):
                volume = data["items"][0]
                volume_id = volume["id"]

                preview_url = (
                    f"https://books.google.com/books?id={volume_id}"
                    "&printsec=frontcover&output=embed"
                )

    except Exception as e:
        print("Google Books Error:", e)

    return render_template(
        "book_detail.html",
        book=book,
        history=history,
        active_loan=active_loan,
        preview_url=preview_url
    )
v

# ─── Issue Book ────────────────────────────────────
@main.route('/issue', methods=['GET', 'POST'])
@login_required
@librarian_required
def issue_book():
    session = db().session
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        book_id    = int(request.form.get('book_id'))
        member = session.execute(
            select(m().User).where(m().User.student_id == student_id)
        ).scalar_one_or_none()
        if not member:
            flash('Student ID not found.', 'danger')
            return redirect(url_for('main.issue_book'))
        book = session.get(m().Book, book_id)
        if not book or book.available_qty < 1:
            flash('Book not available.', 'danger')
            return redirect(url_for('main.issue_book'))

        issue = m().IssuedBook(
            book_id=book.id, user_id=member.id,
            issued_by=current_user.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=14),
            status='active'
        )
        book.available_qty -= 1
        session.add(issue)
        session.add(m().Notification(
            user_id=member.id, type='reminder',
            title='Book Issued',
            message=f'"{book.title}" issued. Due: {date.today() + timedelta(days=14)}'
        ))
        session.commit()
        flash(f'"{book.title}" issued to {member.name}!', 'success')
        return redirect(url_for('main.librarian_desk'))

    members   = session.execute(select(m().User).where(m().User.role == 'member')).scalars().all()
    all_books = session.execute(select(m().Book).where(m().Book.available_qty > 0)).scalars().all()
    return render_template('issue_book.html', members=members, books=all_books)


# ─── Return Book ───────────────────────────────────
@main.route('/return/<int:issue_id>', methods=['POST'])
@login_required
@librarian_required
def return_book(issue_id):
    session = db().session
    issue   = session.get(m().IssuedBook, issue_id)
    today   = date.today()
    issue.return_date = today
    issue.status = 'returned'
    issue.book.available_qty += 1

    if today > issue.due_date:
        days_late = (today - issue.due_date).days
        amount    = m().Fine.calculate(days_late)
        count     = session.execute(select(func.count(m().Fine.id))).scalar()
        session.add(m().Fine(
            transaction_id=f'FIN-{1000 + count + 1}',
            issued_book_id=issue.id, user_id=issue.user_id,
            days_late=days_late, amount=amount, status='unpaid'
        ))
        session.add(m().Notification(
            user_id=issue.user_id, type='overdue',
            title='Overdue Fine Applied',
            message=f'"{issue.book.title}" {days_late} days late. Fine: ${amount}'
        ))
        flash(f'Returned. Fine ${amount} applied.', 'warning')
    else:
        flash(f'"{issue.book.title}" returned. No fine!', 'success')
    session.commit()
    return redirect(url_for('main.librarian_desk'))
@main.route('/member/return/<int:issue_id>', methods=['POST'])
@login_required
def member_return_book(issue_id):
    session = db().session
    issue   = session.get(m().IssuedBook, issue_id)

    if not issue or issue.user_id != current_user.id:
        flash('Invalid request.', 'danger')
        return redirect(url_for('main.dashboard'))

    today = date.today()
    issue.return_date = today
    issue.status = 'returned'
    issue.book.available_qty += 1

    if today > issue.due_date:
        days_late = (today - issue.due_date).days
        amount    = m().Fine.calculate(days_late)
        count     = session.execute(select(func.count(m().Fine.id))).scalar()
        session.add(m().Fine(
            transaction_id=f'FIN-{1000 + count + 1}',
            issued_book_id=issue.id,
            user_id=issue.user_id,
            days_late=days_late,
            amount=amount,
            status='unpaid'
        ))
        session.add(m().Notification(
            user_id=issue.user_id, type='overdue',
            title='Book Returned Late',
            message=f'"{issue.book.title}" returned {days_late} days late. Fine: ${amount}'
        ))
        flash(f'Book returned. Fine of ${amount} applied ({days_late} days late).', 'warning')
    else:
        flash(f'"{issue.book.title}" returned successfully. No fine!', 'success')

    db().session.commit()
    return redirect(url_for('main.my_books'))


@main.route('/my-books')
@login_required
def my_books():
    session = db().session

    active_loans = session.execute(
        select(m().IssuedBook).where(
            m().IssuedBook.user_id == current_user.id,
            m().IssuedBook.status == 'active'
        ).order_by(m().IssuedBook.issue_date.desc())
    ).scalars().all()

    returned_books = session.execute(
        select(m().IssuedBook).where(
            m().IssuedBook.user_id == current_user.id,
            m().IssuedBook.status == 'returned'
        ).order_by(m().IssuedBook.issue_date.desc())
    ).scalars().all()

    unpaid_fines = session.execute(
        select(m().Fine).where(
            m().Fine.user_id == current_user.id,
            m().Fine.status == 'unpaid'
        )
    ).scalars().all()

    return render_template('my_books.html',
                           active_loans=active_loans,
                           returned_books=returned_books,
                           unpaid_fines=unpaid_fines,
                           today=date.today())
@main.route('/books/<int:book_id>/request', methods=['POST'])
@login_required
def request_book(book_id):
    session = db().session
    book    = session.get(m().Book, book_id)

    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('main.books'))

    if not book.is_available:
        flash('Book is not available.', 'danger')
        return redirect(url_for('main.book_detail', book_id=book_id))

    # Check if already borrowed
    existing = session.execute(
        select(m().IssuedBook).where(
            m().IssuedBook.user_id == current_user.id,
            m().IssuedBook.book_id == book_id,
            m().IssuedBook.status == 'active'
        )
    ).scalar_one_or_none()

    if existing:
        flash('You already have this book borrowed!', 'warning')
        return redirect(url_for('main.book_detail', book_id=book_id))

    # Check if already requested
    existing_request = session.execute(
        select(m().Notification).where(
            m().Notification.user_id == current_user.id,
            m().Notification.type == 'book_request',
            m().Notification.message.contains(book.title)
        )
    ).scalar_one_or_none()

    if existing_request:
        flash('You already requested this book!', 'warning')
        return redirect(url_for('main.book_detail', book_id=book_id))

    # Send notification to all librarians and admins
    staff = session.execute(
        select(m().User).where(
            m().User.role.in_(['admin', 'librarian'])
        )
    ).scalars().all()

    for staff_member in staff:
        session.add(m().Notification(
            user_id=staff_member.id,
            type='book_request',
            title=f'Book Request from {current_user.name}',
            message=f'{current_user.name} (ID: {current_user.student_id}) '
                    f'has requested "{book.title}" by {book.author}. '
                    f'Student Email: {current_user.email}'
        ))

    # Confirm notification to member
    session.add(m().Notification(
        user_id=current_user.id,
        type='reservation',
        title='Book Request Sent!',
        message=f'Your request for "{book.title}" has been sent to the librarian. '
                f'Please visit the library desk to collect it.'
    ))

    session.commit()
    flash(f'Request sent for "{book.title}"! Visit the library desk to collect it.', 'success')
    return redirect(url_for('main.book_detail', book_id=book_id))


# ─── Members ───────────────────────────────────────
@main.route('/members')
@login_required
@librarian_required
def members():
    session    = db().session
    search     = request.args.get('search', '')
    department = request.args.get('department', '')
    stmt = select(m().User).where(m().User.role == 'member')
    if search:
        stmt = stmt.where(m().User.name.ilike(f'%{search}%'))
    if department:
        stmt = stmt.where(m().User.department == department)
    all_members = session.execute(stmt).scalars().all()
    depts = session.execute(
        select(m().User.department).where(m().User.role == 'member').distinct()
    ).scalars().all()
    return render_template('members.html', members=all_members,
                           departments=[d for d in depts if d])
@main.route('/members/<int:member_id>/history')
@login_required
@admin_required
def member_history(member_id):
    session = db().session
    member  = session.get(m().User, member_id)
    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('main.members'))

    history = session.execute(
        select(m().IssuedBook).where(
            m().IssuedBook.user_id == member_id
        ).order_by(m().IssuedBook.issue_date.desc())
    ).scalars().all()

    fines = session.execute(
        select(m().Fine).where(
            m().Fine.user_id == member_id
        ).order_by(m().Fine.created_at.desc())
    ).scalars().all()

    return render_template('member_history.html',
                           member=member,
                           history=history,
                           fines=fines)


# ─── Add Member ────────────────────────────────────
@main.route('/members/add', methods=['GET', 'POST'])
@login_required
@librarian_required
def add_member():
    session = db().session
    if request.method == 'POST':
        name       = request.form.get('name')
        email      = request.form.get('email')
        student_id = request.form.get('student_id')
        department = request.form.get('department')
        password   = request.form.get('password')

        existing = session.execute(
            select(m().User).where(m().User.email == email)
        ).scalar_one_or_none()
        if existing:
            flash('Email already exists.', 'danger')
            return redirect(url_for('main.add_member'))

        user = m().User(
            name=name, email=email, role='member',
            student_id=student_id, department=department,
            password_hash=generate_password_hash(password)
        )
        session.add(user)
        session.commit()
        flash('Member added successfully!', 'success')
        return redirect(url_for('main.members'))
    return render_template('add_member.html')


# ─── Fines ─────────────────────────────────────────
@main.route('/fines')
@login_required
def fines():
    session = db().session
    status  = request.args.get('status', 'all')
    stmt    = select(m().Fine)
    if current_user.role == 'member':
        stmt = stmt.where(m().Fine.user_id == current_user.id)
    if status == 'paid':
        stmt = stmt.where(m().Fine.status == 'paid')
    elif status == 'unpaid':
        stmt = stmt.where(m().Fine.status == 'unpaid')
    all_fines = session.execute(stmt.order_by(m().Fine.created_at.desc())).scalars().all()
    return render_template('fines.html', fines=all_fines, status=status)


@main.route('/fines/pay/<int:fine_id>', methods=['POST'])
@login_required
def pay_fine(fine_id):
    session      = db().session
    fine         = session.get(m().Fine, fine_id)
    fine.status  = 'paid'
    fine.paid_at = datetime.utcnow()
    session.commit()
    flash(f'Fine {fine.transaction_id} paid!', 'success')
    return redirect(url_for('main.fines'))


# ─── Notifications ─────────────────────────────────
@main.route('/notifications')
@login_required
def notifications():
    session = db().session
    notifs  = session.execute(
        select(m().Notification).where(
            m().Notification.user_id == current_user.id
        ).order_by(m().Notification.created_at.desc())
    ).scalars().all()
    for n in notifs:
        n.is_read = True
    session.commit()
    return render_template('notifications.html', notifications=notifs)


# ─── Analytics ─────────────────────────────────────
@main.route('/analytics')
@login_required
@admin_required
def analytics():
    session               = db().session
    total_circulation     = session.execute(select(func.count(m().IssuedBook.id))).scalar()
    active_members        = session.execute(
        select(func.count(m().User.id)).where(
            m().User.role == 'member', m().User.is_active == True)
    ).scalar()
    total_fines_collected = session.execute(
        select(func.sum(m().Fine.amount)).where(m().Fine.status == 'paid')
    ).scalar() or 0
    all_active    = session.execute(
        select(m().IssuedBook).where(m().IssuedBook.status == 'active')
    ).scalars().all()
    overdue_count = len([b for b in all_active if b.is_overdue])
    return render_template('analytics.html',
                           total_circulation=total_circulation,
                           active_members=active_members,
                           total_fines_collected=total_fines_collected,
                           overdue_count=overdue_count)


# ─── Settings ──────────────────────────────────────
@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    session = db().session
    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name)
        new_pw = request.form.get('new_password')
        if new_pw:
            current_user.set_password(new_pw)
        session.commit()
        flash('Settings updated!', 'success')
    return render_template('settings.html')
#-------edit profile----------------
@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    session = db().session
    if request.method == 'POST':
        name       = request.form.get('name')
        email      = request.form.get('email')
        student_id = request.form.get('student_id')
        department = request.form.get('department')

        # Check if email already taken by another user
        existing = session.execute(
            select(m().User).where(
                m().User.email == email,
                m().User.id != current_user.id
            )
        ).scalar_one_or_none()

        if existing:
            flash('Email already taken by another user.', 'danger')
            return redirect(url_for('main.edit_profile'))

        current_user.name       = name
        current_user.email      = email
        current_user.student_id = student_id or current_user.student_id
        current_user.department = department or current_user.department
        session.commit()
        flash('Profile updated successfully!', 'success')

        if current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.role == 'librarian':
            return redirect(url_for('main.librarian_desk'))
        return redirect(url_for('main.dashboard'))

    return render_template('edit_profile.html')
#--------changepassword----------
@main.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    session = db().session
    if request.method == 'POST':
        current_pw  = request.form.get('current_password')
        new_pw      = request.form.get('new_password')
        confirm_pw  = request.form.get('confirm_password')

        if not current_user.check_password(current_pw):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('main.change_password'))

        if new_pw != confirm_pw:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('main.change_password'))

        if len(new_pw) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('main.change_password'))

        current_user.set_password(new_pw)
        session.commit()
        flash('Password changed successfully!', 'success')

        # Redirect based on role
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.role == 'librarian':
            return redirect(url_for('main.librarian_desk'))
        return redirect(url_for('main.dashboard'))

    return render_template('change_password.html')
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import date, timedelta, datetime
from functools import wraps
from sqlalchemy import select, or_, func
from werkzeug.security import generate_password_hash

auth = Blueprint('auth', __name__)
main = Blueprint('main', __name__)


def db():
    from flask_sqlalchemy import SQLAlchemy
    # Get the single db instance attached to the current app
    for ext in current_app.extensions.values():
        from flask_sqlalchemy import SQLAlchemy
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


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        session  = db().session
        user = session.execute(
            select(m().User).where(m().User.email == email)
        ).scalar_one_or_none()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        session    = db().session
        name       = request.form.get('name')
        email      = request.form.get('email')
        password   = request.form.get('password')
        student_id = request.form.get('student_id')
        department = request.form.get('department')

        existing = session.execute(
            select(m().User).where(m().User.email == email)
        ).scalar_one_or_none()
        if existing:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        user = m().User(
            name=name, email=email, role='member',
            student_id=student_id or None,
            department=department,
            password_hash=generate_password_hash(password)
        )
        session.add(user)
        session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')


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
    book    = session.get(m().Book, book_id)
    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('main.books'))
    history = session.execute(
        select(m().IssuedBook).where(m().IssuedBook.book_id == book_id)
        .order_by(m().IssuedBook.issue_date.desc()).limit(10)
    ).scalars().all()
    return render_template('book_detail.html', book=book, history=history)


@main.route('/books/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_book():
    session    = db().session
    categories = session.execute(select(m().Category)).scalars().all()
    if request.method == 'POST':
        qty  = int(request.form.get('quantity', 1))
        book = m().Book(
            title=request.form.get('title'),
            author=request.form.get('author'),
            category_id=request.form.get('category_id'),
            publication_year=request.form.get('publication_year'),
            description=request.form.get('description'),
            isbn=request.form.get('isbn') or None,
            total_quantity=qty, available_qty=qty
        )
        session.add(book)
        session.commit()
        flash('Book added!', 'success')
        return redirect(url_for('main.books'))
    return render_template('add_book.html', categories=categories)


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
    session              = db().session
    total_circulation    = session.execute(select(func.count(m().IssuedBook.id))).scalar()
    active_members       = session.execute(
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
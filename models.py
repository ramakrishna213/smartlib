from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash


def _db():
    from app import db
    return db


class User(UserMixin):
    pass


class Category:
    pass


class Book:
    pass


class IssuedBook:
    pass


class Fine:
    pass


class Notification:
    pass


def init_db_models(db):
    """Called once from app.py to define all models on the db instance."""

    class User(UserMixin, db.Model):
        __tablename__ = 'users'
        id            = db.Column(db.Integer, primary_key=True)
        name          = db.Column(db.String(100), nullable=False)
        email         = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(256), nullable=False)
        role          = db.Column(db.String(20), default='member')
        student_id    = db.Column(db.String(20), unique=True, nullable=True)
        department    = db.Column(db.String(60), nullable=True)
        avatar_url    = db.Column(db.String(200), nullable=True)
        is_active     = db.Column(db.Boolean, default=True)
        created_at    = db.Column(db.DateTime, default=datetime.utcnow)
        issued_books  = db.relationship('IssuedBook', foreign_keys='IssuedBook.user_id',
                                        backref='member', lazy=True)
        notifications = db.relationship('Notification', backref='user', lazy=True)
        fines         = db.relationship('Fine', backref='user', lazy=True)

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

    class Category(db.Model):
        __tablename__ = 'categories'
        id    = db.Column(db.Integer, primary_key=True)
        name  = db.Column(db.String(60), unique=True, nullable=False)
        books = db.relationship('Book', backref='category', lazy=True)

    class Book(db.Model):
        __tablename__    = 'books'
        id               = db.Column(db.Integer, primary_key=True)
        title            = db.Column(db.String(200), nullable=False)
        author           = db.Column(db.String(120), nullable=False)
        category_id      = db.Column(db.Integer, db.ForeignKey('categories.id'))
        publication_year = db.Column(db.Integer)
        rating           = db.Column(db.Float, default=0.0)
        total_quantity   = db.Column(db.Integer, default=1)
        available_qty    = db.Column(db.Integer, default=1)
        cover_image      = db.Column(db.String(200), nullable=True)
        description      = db.Column(db.Text, nullable=True)
        isbn             = db.Column(db.String(20), unique=True, nullable=True)
        created_at       = db.Column(db.DateTime, default=datetime.utcnow)
        issued_books     = db.relationship('IssuedBook', backref='book', lazy=True)

        @property
        def is_available(self):
            return self.available_qty > 0

    class IssuedBook(db.Model):
        __tablename__ = 'issued_books'
        id          = db.Column(db.Integer, primary_key=True)
        book_id     = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
        user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        issued_by   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
        issue_date  = db.Column(db.Date, default=date.today)
        due_date    = db.Column(db.Date, nullable=False)
        return_date = db.Column(db.Date, nullable=True)
        status      = db.Column(db.String(20), default='active')
        fine        = db.relationship('Fine', backref='issued_book', uselist=False)

        @property
        def days_left(self):
            if self.status == 'active':
                return (self.due_date - date.today()).days
            return 0

        @property
        def is_overdue(self):
            return date.today() > self.due_date and self.status == 'active'

    class Fine(db.Model):
        __tablename__  = 'fines'
        id             = db.Column(db.Integer, primary_key=True)
        transaction_id = db.Column(db.String(20), unique=True, nullable=False)
        issued_book_id = db.Column(db.Integer, db.ForeignKey('issued_books.id'), nullable=False)
        user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        days_late      = db.Column(db.Integer, default=0)
        amount         = db.Column(db.Float, default=0.0)
        status         = db.Column(db.String(10), default='unpaid')
        paid_at        = db.Column(db.DateTime, nullable=True)
        created_at     = db.Column(db.DateTime, default=datetime.utcnow)

        @staticmethod
        def calculate(days_late, rate=0.50):
            return round(max(0, days_late * rate), 2)

    class Notification(db.Model):
        __tablename__ = 'notifications'
        id         = db.Column(db.Integer, primary_key=True)
        user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        type       = db.Column(db.String(30))
        title      = db.Column(db.String(100))
        message    = db.Column(db.Text)
        is_read    = db.Column(db.Boolean, default=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Export to module level so routes can import them
    import models as _m
    _m.User         = User
    _m.Category     = Category
    _m.Book         = Book
    _m.IssuedBook   = IssuedBook
    _m.Fine         = Fine
    _m.Notification = Notification

    return User, Category, Book, IssuedBook, Fine, Notification
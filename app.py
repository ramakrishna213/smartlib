import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'smartlib-secret-key-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartlib.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # ── Google + GitHub OAuth ──────────────────────────────
    from authlib.integrations.flask_client import OAuth
    oauth = OAuth(app)

    # Google OAuth
    app.extensions['google_oauth'] = oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # GitHub OAuth
    app.extensions['github_oauth'] = oauth.register(
        name='github',
        client_id=os.environ.get('GITHUB_CLIENT_ID'),
        client_secret=os.environ.get('GITHUB_CLIENT_SECRET'),
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'read:user user:email'}
    )

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return db.session.get(User, int(user_id))

    with app.app_context():
        from models import init_db_models
        User, Book, Category, IssuedBook, Fine, Notification = init_db_models(db)
        db.create_all()
        _seed()

        from routes import auth, main
        app.register_blueprint(auth)
        app.register_blueprint(main)

    return app


def _seed():
    import models as m
    from sqlalchemy import select
    from werkzeug.security import generate_password_hash

    User = m.User
    Book = m.Book
    Category = m.Category

    # ---------- Create Categories ----------
    for name in ['Technology', 'Science', 'Fiction', 'Engineering', 'Business', 'Arts']:
        existing = db.session.execute(
            select(Category).where(Category.name == name)
        ).scalar_one_or_none()

        if not existing:
            db.session.add(Category(name=name))

    db.session.commit()

    # ---------- Create Admin ----------
    admin = db.session.execute(
        select(User).where(User.email == 'admin@smartlib.com')
    ).scalar_one_or_none()

    if not admin:
        admin = User(
            name='Admin User',
            email='admin@smartlib.com',
            role='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)

    # ---------- Create Librarian ----------
    librarian = db.session.execute(
        select(User).where(User.email == 'librarian@smartlib.com')
    ).scalar_one_or_none()

    if not librarian:
        librarian = User(
            name='Librarian One',
            email='librarian@smartlib.com',
            role='librarian',
            password_hash=generate_password_hash('lib123')
        )
        db.session.add(librarian)

    db.session.commit()

    # ---------- Create Sample Members ----------
    members = [
        ('Alex Chen', 'alex@example.com', 'STU-2024-001', 'Computer Science'),
        ('Sarah Johnson', 'sarah@example.com', 'STU-2024-042', 'Engineering'),
        ('Mike Smith', 'mike@example.com', 'STU-2023-115', 'Business'),
        ('Emma Davis', 'emma@example.com', 'STU-2023-089', 'Arts')
    ]

    for name, email, sid, dept in members:
        existing = db.session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if not existing:
            db.session.add(User(
                name=name,
                email=email,
                role='member',
                student_id=sid,
                department=dept,
                password_hash=generate_password_hash('member123')
            ))

    db.session.commit()

# ---------- Create Sample Books ----------

tech = db.session.execute(
    select(Category).where(Category.name == 'Technology')
).scalar_one()

fiction = db.session.execute(
    select(Category).where(Category.name == 'Fiction')
).scalar_one()

engg = db.session.execute(
    select(Category).where(Category.name == 'Engineering')
).scalar_one()

science = db.session.execute(
    select(Category).where(Category.name == 'Science')
).scalar_one()

business = db.session.execute(
    select(Category).where(Category.name == 'Business')
).scalar_one()

books = [
    # Technology
    ('The Pragmatic Programmer', 'David Thomas', tech.id, 2019, 4.8, 3),
    ('Clean Code', 'Robert C. Martin', tech.id, 2008, 4.7, 2),
    ('Design Patterns', 'Gang of Four', tech.id, 1994, 4.6, 2),
    ('Refactoring', 'Martin Fowler', tech.id, 2018, 4.5, 1),

    # Fiction
    ('The Great Gatsby', 'F. Scott Fitzgerald', fiction.id, 1925, 4.3, 3),
    ('1984', 'George Orwell', fiction.id, 1949, 4.9, 2),

    # Engineering - Java
    ('Head First Java', 'Kathy Sierra', engg.id, 2022, 4.8, 3),
    ('Effective Java', 'Joshua Bloch', engg.id, 2018, 4.9, 2),
    ('Java: The Complete Reference', 'Herbert Schildt', engg.id, 2021, 4.7, 2),
    ('Core Java Volume I', 'Cay Horstmann', engg.id, 2022, 4.6, 2),
    ('Spring Boot in Action', 'Craig Walls', engg.id, 2022, 4.5, 2),

    # Engineering - Python
    ('Python Crash Course', 'Eric Matthes', engg.id, 2023, 4.9, 3),
    ('Fluent Python', 'Luciano Ramalho', engg.id, 2022, 4.8, 2),
    ('Automate the Boring Stuff', 'Al Sweigart', engg.id, 2020, 4.7, 3),
    ('Python for Data Analysis', 'Wes McKinney', engg.id, 2022, 4.6, 2),
    ('Learning Python', 'Mark Lutz', engg.id, 2013, 4.5, 2),

    # Engineering - C
    ('The C Programming Language', 'Brian Kernighan', engg.id, 1988, 4.9, 3),
    ('C Programming: A Modern Approach', 'K.N. King', engg.id, 2008, 4.8, 2),
    ('Head First C', 'David Griffiths', engg.id, 2012, 4.6, 2),
    ('C: The Complete Reference', 'Herbert Schildt', engg.id, 2000, 4.5, 2),

    # Engineering - General
    ('Introduction to Algorithms', 'Thomas Cormen', engg.id, 2009, 4.9, 2),
    ('Computer Networks', 'Andrew Tanenbaum', engg.id, 2011, 4.7, 2),
    ('Operating System Concepts', 'Abraham Silberschatz', engg.id, 2018, 4.6, 2),
    ('Database System Concepts', 'Abraham Silberschatz', engg.id, 2019, 4.5, 2),
    ('Computer Organization', 'Carl Hamacher', engg.id, 2011, 4.4, 2),

    # Science
    ('A Brief History of Time', 'Stephen Hawking', science.id, 1988, 4.8, 3),
    ('The Selfish Gene', 'Richard Dawkins', science.id, 1976, 4.7, 2),

    # Business
    ('The Lean Startup', 'Eric Ries', business.id, 2011, 4.6, 3),
    ('Zero to One', 'Peter Thiel', business.id, 2014, 4.7, 2),
]

for title, author, cat, year, rating, qty in books:
    existing = db.session.execute(
        select(Book).where(Book.title == title)
    ).scalar_one_or_none()

    if not existing:
        db.session.add(Book(
            title=title,
            author=author,
            category_id=cat,
            publication_year=year,
            rating=rating,
            total_quantity=qty,
            available_qty=qty
        ))

db.session.commit()

print("✅ SmartLib seeded successfully!")


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'smartlib-secret-key-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartlib.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

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
    Fine = m.Fine
    IssuedBook = m.IssuedBook
    Notification = m.Notification

    if db.session.execute(select(User)).first():
        return

    # Categories
    for name in [
        'Technology',
        'Science',
        'Fiction',
        'Engineering',
        'Business',
        'Arts'
    ]:
        db.session.add(Category(name=name))

    db.session.flush()

    # Admin & Librarian
    db.session.add(
        User(
            name='Admin User',
            email='admin@smartlib.com',
            role='admin',
            password_hash=generate_password_hash('admin123')
        )
    )

    db.session.add(
        User(
            name='Librarian One',
            email='librarian@smartlib.com',
            role='librarian',
            password_hash=generate_password_hash('lib123')
        )
    )

    # Members
    members = [
        ('Alex Chen', 'alex@example.com', 'STU-2024-001', 'Computer Science'),
        ('Sarah Johnson', 'sarah@example.com', 'STU-2024-042', 'Engineering'),
        ('Mike Smith', 'mike@example.com', 'STU-2023-115', 'Business'),
        ('Emma Davis', 'emma@example.com', 'STU-2023-089', 'Arts')
    ]

    for name, email, sid, dept in members:
        db.session.add(
            User(
                name=name,
                email=email,
                role='member',
                student_id=sid,
                department=dept,
                password_hash=generate_password_hash('member123')
            )
        )

    db.session.flush()

    tech = db.session.execute(
        select(Category).where(Category.name == 'Technology')
    ).scalar_one()

    fiction = db.session.execute(
        select(Category).where(Category.name == 'Fiction')
    ).scalar_one()

    books = [
        ('The Pragmatic Programmer', 'David Thomas', tech.id, 2019, 4.8, 3),
        ('Clean Code', 'Robert C. Martin', tech.id, 2008, 4.7, 2),
        ('Design Patterns', 'Gang of Four', tech.id, 1994, 4.6, 2),
        ('Refactoring', 'Martin Fowler', tech.id, 2018, 4.5, 1),
        ('The Great Gatsby', 'F. Scott Fitzgerald', fiction.id, 1925, 4.3, 3),
        ('1984', 'George Orwell', fiction.id, 1949, 4.9, 2),
    ]

    for title, author, cat, year, rating, qty in books:
        db.session.add(
            Book(
                title=title,
                author=author,
                category_id=cat,
                publication_year=year,
                rating=rating,
                total_quantity=qty,
                available_qty=qty
            )
        )

    db.session.commit()
    print("✅ Database seeded!")


if __name__ == '__main__':
    import os
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
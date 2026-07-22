from app import create_app
from sqlalchemy import select
from models import User

def db():
    from app import db
    return db

app = create_app()

with app.app_context():
    session = db().session

    email = input("Enter registered email: ").strip().lower()

    user = session.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if user:
        user.role = "librarian"
        session.commit()
        print("✅ User promoted to Librarian successfully!")
    else:
        print("❌ User not found. Register first.")

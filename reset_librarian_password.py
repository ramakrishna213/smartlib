from app import create_app
from sqlalchemy import select
from models import User

def db():
    from app import db
    return db

app = create_app()

with app.app_context():
    session = db().session

    user = session.execute(
        select(User).where(User.email == "librarian@smartlib.com")
    ).scalar_one_or_none()

    if user:
        user.set_password("librarian123")
        session.commit()
        print("Password reset successfully!")
    else:
        print("Librarian not found.")
from app import create_app, db
from models import User

app = create_app()

with app.app_context():
    email = "admin@smartlib.com"

    admin = User.query.filter_by(email=email).first()

    if admin:
        print("Admin already exists.")
    else:
        admin = User(
            name="Administrator",
            email=email,
            role="admin"
        )

        admin.set_password("admin123")

        db.session.add(admin)
        db.session.commit()

        print("Admin created successfully!")
        print("Email: admin@smartlib.com")
        print("Password: admin123")

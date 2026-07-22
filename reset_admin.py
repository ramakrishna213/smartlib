from app import create_app, db
import models as m
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    User = m.User

    admin = User.query.filter_by(email="admin@smartlib.com").first()

    if admin:
        admin.password_hash = generate_password_hash("admin123")
        db.session.commit()
        print("Admin password changed to admin123")
    else:
        print("Admin user not found")
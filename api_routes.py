from flask import Blueprint, request, jsonify
from models import User
from werkzeug.security import check_password_hash

api = Blueprint("api", __name__)


@api.route("/api/login", methods=["POST"])
def api_login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):

        return jsonify({
            "success": True,
            "message": "Login successful",
            "role": user.role
        })

    return jsonify({
        "success": False,
        "message": "Invalid username or password"
    }), 401
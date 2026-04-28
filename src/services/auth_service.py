import bcrypt
from db.repository_factory import get_user_repository

class AuthService:
    @staticmethod
    def register_user(email, password):
        user_repo = get_user_repository()
        try:
            result = user_repo.create_user(email, password)
            if result.get("success"):
                return {"success": True, "message": result.get("message", "Registration successful."), "error": "", "user_id": result.get("user_id"), "user_email": email}
            else:
                return {"success": False, "message": "", "error": result.get("error", "Registration failed."), "user_id": None, "user_email": None}
        except Exception as e:
            print(f"Error registering user: {e}")
            return {"success": False, "message": "", "error": "An unexpected error occurred during registration.", "user_id": None, "user_email": None}

    @staticmethod
    def login_user(email, password):
        user_repo = get_user_repository()
        try:
            user = user_repo.get_user_by_email(email)
            if not user:
                return {"success": False, "message": "", "error": "No account found with that email.", "user_id": None, "user_email": None}
            
            user_id, user_email, password_hash = user
            if bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
                return {"success": True, "message": "Login successful.", "error": "", "user_id": user_id, "user_email": user_email}
            else:
                return {"success": False, "message": "", "error": "Incorrect password.", "user_id": None, "user_email": None}
        except Exception as e:
            print(f"Error logging in user: {e}")
            return {"success": False, "message": "", "error": "An unexpected error occurred during login.", "user_id": None, "user_email": None}

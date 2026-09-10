"""
Authentication & User Management Service Layer
------------------------------------------------
Provides secure user authentication, PBKDF2 password hashing,
admin approval management, user CRUD, and login auditing into MySQL.
"""

import hashlib
import secrets
import time
from typing import Dict, Any, List, Optional
from config.database import db_manager


def hash_password(password: str) -> str:
    """Securely hash password using PBKDF2-HMAC-SHA256 with a unique random 16-byte salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a plain password against the stored salt:hash string."""
    try:
        parts = stored_hash.split(':', 1)
        if len(parts) != 2:
            return False
        salt, key_hex = parts
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


class AuthService:
    """Service handling Admin & User authentication and User management."""

    def __init__(self):
        self._active_admin_tokens: Dict[str, Dict[str, Any]] = {}
        self.seed_default_accounts()

    def seed_default_accounts(self):
        """Seeds default Admin account and initial users from Screenshot 2 if not present."""
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                # Check default admin
                cursor.execute("SELECT `id` FROM `admins` WHERE `admin_id` = 'admin';")
                if not cursor.fetchone():
                    admin_hash = hash_password("admin123")
                    cursor.execute(
                        "INSERT INTO `admins` (`admin_id`, `name`, `password_hash`) VALUES (%s, %s, %s);",
                        ("admin", "Admin", admin_hash)
                    )
                    print("[AuthService] Seeded default admin account ('admin').")

                # Check sample users matching Screenshot 2
                cursor.execute("SELECT COUNT(*) as cnt FROM `users`;")
                res = cursor.fetchone()
                if res and res.get('cnt', 0) == 0:
                    default_pw = hash_password("password123")
                    sample_users = [
                        ("MOIL001", "Ravi Kumar", "ACTIVE"),
                        ("MOIL002", "Priya Singh", "ACTIVE"),
                        ("MOIL003", "Arun Das", "ACTIVE"),
                        ("MOIL004", "Sneha Patil", "INACTIVE"),
                        ("MOIL005", "Vikram Mehta", "ACTIVE"),
                    ]
                    for emp_id, name, status in sample_users:
                        cursor.execute(
                            """
                            INSERT INTO `users` (`employee_id`, `name`, `password_hash`, `status`, `role`)
                            VALUES (%s, %s, %s, %s, 'USER');
                            """,
                            (emp_id, name, default_pw, status)
                        )
                    print("[AuthService] Seeded 5 initial users matching reference UI.")
            conn.close()
        except Exception as exc:
            print(f"[AuthService Seed Warning] {exc}")

    def log_successful_login(self, user_type: str, identifier: str) -> Optional[int]:
        """
        Inserts a row into `login_logs` after a successful login.
        Strict requirement (Section 8A): Only successful logins, no passwords or hashes.
        """
        try:
            conn = db_manager.get_connection()
            query = """
                INSERT INTO `login_logs` (`user_type`, `identifier`, `status`)
                VALUES (%s, %s, 'SUCCESS');
            """
            with conn.cursor() as cursor:
                cursor.execute(query, (user_type.upper(), identifier.strip()))
                log_id = cursor.lastrowid
            conn.close()
            print(f"[AuthService] Recorded successful {user_type} login for '{identifier}' (Log #{log_id}).")
            return log_id
        except Exception as exc:
            print(f"[AuthService Log Error] Could not write to login_logs: {exc}")
            return None

    def admin_login(self, admin_id: str, password: str) -> Dict[str, Any]:
        """
        Validates Admin ID and password.
        On success, logs the event into login_logs and issues an auth token.
        """
        if not admin_id or not password:
            return {"success": False, "message": "Admin ID and password are required."}

        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT `id`, `admin_id`, `name`, `password_hash` FROM `admins` WHERE `admin_id` = %s;",
                    (admin_id.strip(),)
                )
                admin_row = cursor.fetchone()
            conn.close()

            if not admin_row or not verify_password(password, admin_row['password_hash']):
                return {"success": False, "message": "Invalid Admin ID or password."}

            # Log successful login to MySQL
            self.log_successful_login(user_type="ADMIN", identifier=admin_row['admin_id'])

            # Create token
            token = f"adm_{secrets.token_hex(24)}"
            self._active_admin_tokens[token] = {
                "admin_id": admin_row['admin_id'],
                "name": admin_row['name'],
                "role": "ADMIN",
                "issued_at": time.time()
            }

            return {
                "success": True,
                "token": token,
                "admin": {
                    "admin_id": admin_row['admin_id'],
                    "name": admin_row['name'],
                    "role": "ADMIN"
                }
            }
        except Exception as exc:
            return {"success": False, "message": f"Server database error: {exc}"}

    def verify_admin_token(self, token: Optional[str]) -> bool:
        """Validates whether the provided token belongs to an active Admin session."""
        if not token:
            return False
        # Remove 'Bearer ' prefix if present
        clean_token = token.replace("Bearer ", "").strip()
        return clean_token in self._active_admin_tokens

    def user_login(self, employee_id: str, password: str) -> Dict[str, Any]:
        """
        Validates Employee ID and password, and strictly enforces account approval (status == 'ACTIVE').
        - If invalid credentials: returns "Invalid Employee ID or password."
        - If valid credentials but status == 'INACTIVE': returns "Your account is pending administrator approval."
        - If valid credentials and status == 'ACTIVE': logs to login_logs and returns session info.
        """
        if not employee_id or not password:
            return {"success": False, "message": "Employee ID and password are required."}

        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT `id`, `employee_id`, `name`, `password_hash`, `status`, `role` FROM `users` WHERE `employee_id` = %s;",
                    (employee_id.strip(),)
                )
                user_row = cursor.fetchone()
            conn.close()

            if not user_row or not verify_password(password, user_row['password_hash']):
                return {
                    "success": False,
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid Employee ID or password."
                }

            # Check Approval Status
            if user_row['status'] != 'ACTIVE':
                return {
                    "success": False,
                    "code": "PENDING_APPROVAL",
                    "message": "Your account is pending administrator approval."
                }

            # Log successful login to MySQL
            self.log_successful_login(user_type="USER", identifier=user_row['employee_id'])

            token = f"usr_{secrets.token_hex(24)}"
            return {
                "success": True,
                "token": token,
                "user": {
                    "employee_id": user_row['employee_id'],
                    "name": user_row['name'],
                    "role": user_row['role'],
                    "status": user_row['status']
                }
            }
        except Exception as exc:
            return {"success": False, "message": f"Server database error: {exc}"}

    def get_users(self) -> List[Dict[str, Any]]:
        """
        Returns all users for the Admin User Management table.
        Security (Section 3 & 10):
        The backend must NEVER return real passwords or password hashes.
        Renders fixed masked placeholder "••••••" instead.
        """
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT `id`, `employee_id`, `name`, `status`, `role`, `created_at`
                    FROM `users`
                    ORDER BY `id` ASC;
                    """
                )
                rows = cursor.fetchall()
            conn.close()

            user_list = []
            for r in rows:
                user_list.append({
                    "id": r["id"],
                    "employee_id": r["employee_id"],
                    "name": r["name"],
                    "password": "••••••",  # Fixed masked display as strictly required
                    "status": r["status"],
                    "role": r.get("role", "USER"),
                    "created_at": str(r["created_at"]) if r.get("created_at") else ""
                })
            return user_list
        except Exception as exc:
            print(f"[AuthService get_users Error] {exc}")
            return []

    def create_user(self, employee_id: str, name: str, password: str) -> Dict[str, Any]:
        """
        Creates a new user with status INACTIVE by default (waiting for Admin approval).
        """
        emp_id = employee_id.strip()
        user_name = name.strip()
        if not emp_id or not user_name or not password:
            return {"success": False, "message": "Employee ID, Name, and Password are required."}

        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT `id` FROM `users` WHERE `employee_id` = %s;", (emp_id,))
                if cursor.fetchone():
                    conn.close()
                    return {"success": False, "message": f"User with Employee ID '{emp_id}' already exists."}

                hashed = hash_password(password)
                query = """
                    INSERT INTO `users` (`employee_id`, `name`, `password_hash`, `status`, `role`)
                    VALUES (%s, %s, %s, 'INACTIVE', 'USER');
                """
                cursor.execute(query, (emp_id, user_name, hashed))
                new_id = cursor.lastrowid
            conn.close()

            return {
                "success": True,
                "user": {
                    "id": new_id,
                    "employee_id": emp_id,
                    "name": user_name,
                    "password": "••••••",
                    "status": "INACTIVE"
                }
            }
        except Exception as exc:
            return {"success": False, "message": f"Database error creating user: {exc}"}

    def update_user(self, user_id: int, name: Optional[str] = None, status: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Updates an existing user's details or status (ACTIVE / INACTIVE).
        """
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM `users` WHERE `id` = %s;", (user_id,))
                user = cursor.fetchone()
                if not user:
                    conn.close()
                    return {"success": False, "message": "User not found."}

                updates = []
                params = []

                if name and name.strip():
                    updates.append("`name` = %s")
                    params.append(name.strip())

                if status and status.strip():
                    norm_status = status.strip().upper()
                    if norm_status not in ("ACTIVE", "INACTIVE"):
                        conn.close()
                        return {"success": False, "message": "Status must be either 'ACTIVE' or 'INACTIVE'."}
                    updates.append("`status` = %s")
                    params.append(norm_status)

                if password and password.strip():
                    hashed = hash_password(password.strip())
                    updates.append("`password_hash` = %s")
                    params.append(hashed)

                if not updates:
                    conn.close()
                    return {"success": True, "message": "No updates provided."}

                params.append(user_id)
                query = f"UPDATE `users` SET {', '.join(updates)} WHERE `id` = %s;"
                cursor.execute(query, tuple(params))
            conn.close()

            return {"success": True, "message": "User updated successfully."}
        except Exception as exc:
            return {"success": False, "message": f"Database error updating user: {exc}"}

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Deletes a user account by ID."""
        try:
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM `users` WHERE `id` = %s;", (user_id,))
                affected = cursor.rowcount
            conn.close()

            if affected > 0:
                return {"success": True, "message": "User deleted successfully."}
            return {"success": False, "message": "User not found or already deleted."}
        except Exception as exc:
            return {"success": False, "message": f"Database error deleting user: {exc}"}

    def logout_admin(self, token: Optional[str]) -> bool:
        """Cleans up active admin token session."""
        if token:
            clean = token.replace("Bearer ", "").strip()
            self._active_admin_tokens.pop(clean, None)
        return True


auth_service = AuthService()

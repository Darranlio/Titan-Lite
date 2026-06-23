import os
import sqlite3
import jwt
import time
import random
import logging
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from pydantic import BaseModel
from config import settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = settings.LLM_API_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

logger = logging.getLogger("TitanUserManager")

class User(BaseModel):
    username: str
    role: str = "BASIC"
    password_hash: str

class UserManager:
    """
    Titan-Lite Authentication & User Management.
    Supports email verification and multi-tenancy context.
    """
    def __init__(self):
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.db_dir = os.path.join(base_path, "app", "data", "users")
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "users.db")
        self._init_db()
        
        # Temporary store for verification codes {email: {"code": str, "expiry": float}}
        self._verification_codes = {}

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # 1. Ensure table exists with initial schema
            conn.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT,
                role TEXT DEFAULT 'BASIC',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # 2. Migration: Check and add 'email' column if missing
            try:
                cursor.execute("SELECT email FROM users LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("Migrating database: Adding 'email' column to 'users' table.")
                # SQLite doesn't support adding UNIQUE columns via ALTER TABLE
                cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            
            # 3. Migration: Check and add 'avatar_url' column if missing
            try:
                cursor.execute("SELECT avatar_url FROM users LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("Migrating database: Adding 'avatar_url' column to 'users' table.")
                cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
            conn.commit()

    def update_avatar(self, username: str, avatar_url: str) -> bool:
        """Updates user's avatar URL."""
        with self._get_conn() as conn:
            conn.execute("UPDATE users SET avatar_url = ? WHERE username = ?", (avatar_url, username))
            conn.commit()
        return True

    def send_verification_code(self, email: str) -> str:
        """Generates and 'sends' a verification code to the email. Returns the code."""
        code = f"{random.randint(100000, 999999)}"
        expiry = time.time() + 600 # 10 minutes
        self._verification_codes[email] = {"code": code, "expiry": expiry}
        print(f"\n[AUTH] 验证码已发送至 {email}: {code} (10分钟内有效)\n")
        return code

    def register_user(self, username: str, password: str, email: str, code: str, role: str = "BASIC") -> bool:
        """Registers a new user after verifying the code."""
        auth_data = self._verification_codes.get(email)
        if not auth_data or auth_data["code"] != code or time.time() > auth_data["expiry"]:
            return False
            
        hashed_password = pwd_context.hash(password)
        try:
            with self._get_conn() as conn:
                conn.execute("INSERT INTO users (username, email, password_hash, role) VALUES (?,?,?,?)",
                             (username, email, hashed_password, role))
                conn.commit()
            del self._verification_codes[email]
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticates a user and returns their info if successful."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Supports login via username or email
            cursor.execute("SELECT username, password_hash, role, avatar_url FROM users WHERE username = ? OR email = ?", (username, username))
            row = cursor.fetchone()
            if not row:
                return None
            
            u, ph, r, av = row
            if not pwd_context.verify(password, ph):
                return None
                
            return {"username": u, "role": r, "avatar_url": av}

    def create_access_token(self, data: dict):
        """Creates a JWT access token."""
        to_encode = data.copy()
        expire = time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifies a JWT token and returns the payload."""
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None

# Singleton export
user_manager = UserManager()

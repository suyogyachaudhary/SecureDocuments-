import sqlite3
from auth import hash_password, verify_password

conn = sqlite3.connect("secure.db")
cursor = conn.cursor()

# Create table with additional columns for credential storage and role
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    certificate BLOB,
    password_hash BLOB,
    salt BLOB,
    is_admin INTEGER DEFAULT 0,
    must_change INTEGER DEFAULT 0,
    revoked INTEGER DEFAULT 0
)
""")
conn.commit()

# For backwards compatibility: ensure new columns exist (SQLite allows ADD COLUMN)
def _ensure_columns():
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(users)")}
    if 'password_hash' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash BLOB")
    if 'salt' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN salt BLOB")
    if 'is_admin' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    if 'must_change' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN must_change INTEGER DEFAULT 0")
    conn.commit()

_ensure_columns()

def add_user(username, cert=None, password=None, is_admin=0, must_change=0):
    """Add or replace a user. If password provided it will be hashed and stored; cert may be None."""
    salt = None
    password_hash = None
    if password is not None:
        salt, password_hash = hash_password(password)
    cursor.execute(
        "INSERT OR REPLACE INTO users (username, certificate, password_hash, salt, is_admin, must_change, revoked) VALUES (?, ?, ?, ?, ?, ?, 0)",
        (username, cert, password_hash, salt, is_admin, must_change)
    )
    conn.commit()

def get_user(username):
    """Return (certificate, revoked) for compatibility."""
    cursor.execute("SELECT certificate, revoked FROM users WHERE username=?", (username,))
    return cursor.fetchone()

def get_user_full(username):
    """Return (certificate, revoked, password_hash, salt, is_admin, must_change)"""
    cursor.execute("SELECT certificate, revoked, password_hash, salt, is_admin, must_change FROM users WHERE username=?", (username,))
    return cursor.fetchone()

def verify_credentials(username, password):
    """Return (ok: bool, is_admin: bool, must_change: bool)"""
    row = get_user_full(username)
    if not row:
        return False, False, False
    _, revoked, password_hash, salt, is_admin, must_change = row
    if revoked:
        return False, False, False
    if password_hash is None or salt is None:
        # No password set; treat as non-login-capable unless admin
        return False, bool(is_admin), bool(must_change)
    ok = verify_password(password, salt, password_hash)
    return ok, bool(is_admin), bool(must_change)

# Password management
def set_password(username, new_password, must_change=False):
    salt, password_hash = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash=?, salt=?, must_change=? WHERE username=?", (password_hash, salt, int(must_change), username))
    conn.commit()

def change_password(username, old_password, new_password):
    ok, is_admin, _ = verify_credentials(username, old_password)
    if not ok:
        return False
    set_password(username, new_password, must_change=False)
    return True

def admin_force_change_password(username, new_password):
    # Admin override to set password without knowing old one
    set_password(username, new_password, must_change=False)
    return True

def create_default_admin(password="admin123"):
    # ensure an admin record exists with a usable password
    row = get_user_full('admin')
    if row:
        # row is (certificate, revoked, password_hash, salt, is_admin, must_change)
        _, revoked, pw_hash, salt, is_admin, must_change = row
        # if user is revoked we don't touch it; otherwise repair
        if not revoked:
            updates = []
            params = []
            if not is_admin:
                updates.append("is_admin=1")
            if pw_hash is None or salt is None:
                # set the provided default and force change next login
                salt, pw_hash = hash_password(password)
                updates.append("password_hash=?")
                params.append(pw_hash)
                updates.append("salt=?")
                params.append(salt)
                updates.append("must_change=1")
            if updates:
                cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE username='admin'", params)
                conn.commit()
        return
    # set must_change=1 to force password change on first login
    add_user('admin', cert=None, password=password, is_admin=1, must_change=1)

def revoke_user(username):
    cursor.execute("UPDATE users SET revoked=1 WHERE username=?", (username,))
    conn.commit()

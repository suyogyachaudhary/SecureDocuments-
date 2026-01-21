import sqlite3

conn = sqlite3.connect("secure.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    certificate BLOB,
    revoked INTEGER DEFAULT 0
)
""")
conn.commit()

def add_user(username, cert):
    cursor.execute("INSERT INTO users VALUES (?, ?, 0)", (username, cert))
    conn.commit()

def get_user(username):
    cursor.execute("SELECT certificate, revoked FROM users WHERE username=?", (username,))
    return cursor.fetchone()

def revoke_user(username):
    cursor.execute("UPDATE users SET revoked=1 WHERE username=?", (username,))
    conn.commit()

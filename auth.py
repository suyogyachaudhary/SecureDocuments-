import os
import hashlib
import hmac

# Use PBKDF2-HMAC-SHA256 with a strong iteration count
ITERATIONS = 200_000

def hash_password(password: str):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
    return salt, dk

def verify_password(password: str, salt: bytes, dk: bytes):
    test = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
    return hmac.compare_digest(test, dk)

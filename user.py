from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from ca import issue_certificate, verify_certificate
from database import add_user, get_user
from security_utils import sign_data

def register_user(username):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    cert = issue_certificate(username, public_key)
    add_user(username, cert)

    with open(f"{username}_private.pem", "wb") as f:
        f.write(private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption()
        ))

    print(f"[✔] User '{username}' registered and certificate issued")

def authenticate_user(username):
    record = get_user(username)
    if not record:
        print("[❌] User not found")
        return False

    cert_bytes, revoked = record
    if revoked:
        print("[❌] Certificate revoked")
        return False

    cert = verify_certificate(cert_bytes)
    print("[✔] Certificate valid for:", cert.subject)
    return True

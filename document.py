from cryptography.hazmat.primitives import serialization
from cryptography import x509
from security_utils import sign_data, verify_signature

def sign_document(username, document_path):
    with open(f"{username}_private.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    with open(document_path, "rb") as f:
        data = f.read()

    signature = sign_data(private_key, data)

    with open(document_path + ".sig", "wb") as f:
        f.write(signature)

    print("[✔] Document signed")

def verify_document(document_path, cert_bytes):
    cert = x509.load_pem_x509_certificate(cert_bytes)
    public_key = cert.public_key()

    with open(document_path, "rb") as f:
        data = f.read()

    with open(document_path + ".sig", "rb") as f:
        signature = f.read()

    verify_signature(public_key, signature, data)
    print("[✔] Signature valid. Document authentic.")

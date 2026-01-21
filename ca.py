import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from datetime import datetime, timedelta

CA_KEY_FILE = "ca_private_key.pem"

# -------------------------------
# Load or create CA private key
# -------------------------------
if os.path.exists(CA_KEY_FILE):
    with open(CA_KEY_FILE, "rb") as f:
        ca_private_key = serialization.load_pem_private_key(
            f.read(), password=None
        )
else:
    ca_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    with open(CA_KEY_FILE, "wb") as f:
        f.write(
            ca_private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            )
        )

ca_public_key = ca_private_key.public_key()

ca_name = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "Secure Root CA")
])

# -------------------------------
def issue_certificate(username, public_key):
    cert = (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, username)])
        )
        .issuer_name(ca_name)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .sign(ca_private_key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM)

# -------------------------------
def verify_certificate(cert_bytes):
    cert = x509.load_pem_x509_certificate(cert_bytes)

    ca_public_key.verify(
        cert.signature,
        cert.tbs_certificate_bytes,
        padding.PKCS1v15(),
        cert.signature_hash_algorithm
    )

    now = datetime.utcnow()
    if not (cert.not_valid_before <= now <= cert.not_valid_after):
        raise Exception("Certificate expired or not yet valid")

    return cert

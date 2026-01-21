import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography import x509

from ca import issue_certificate, verify_certificate
from crypto_utils import sign, verify
from database import add_user, get_user, revoke_user

os.makedirs("users", exist_ok=True)

class PKIApp:
    def __init__(self, root):
        self.root = root
        root.title("PKI Secure Document System")
        root.geometry("450x400")

        tk.Button(root, text="Register User", command=self.register).pack(pady=10)
        tk.Button(root, text="Authenticate User", command=self.authenticate).pack(pady=10)
        tk.Button(root, text="Sign Document", command=self.sign_document).pack(pady=10)
        tk.Button(root, text="Verify Document", command=self.verify_document).pack(pady=10)
        tk.Button(root, text="Revoke Certificate", command=self.revoke).pack(pady=10)

    # ---------------------------
    def register(self):
        username = simpledialog.askstring("Register", "Enter username:")
        if not username:
            return

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        cert = issue_certificate(username, public_key)
        add_user(username, cert)

        with open(f"users/{username}.pem", "wb") as f:
            f.write(private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            ))

        messagebox.showinfo("Success", "User registered and certificate issued")

    # ---------------------------
    def authenticate(self):
        username = simpledialog.askstring("Authenticate", "Username:")
        record = get_user(username)

        if not record:
            messagebox.showerror("Error", "User not found")
            return

        cert_bytes, revoked = record
        if revoked:
            messagebox.showerror("Error", "Certificate revoked")
            return

        verify_certificate(cert_bytes)
        messagebox.showinfo("Success", "Certificate valid. User authenticated.")

    # ---------------------------
    def sign_document(self):
        username = simpledialog.askstring("Sign", "Username:")
        path = filedialog.askopenfilename()
        if not username or not path:
            return

        with open(f"users/{username}.pem", "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), None)

        with open(path, "rb") as f:
            data = f.read()

        signature = sign(private_key, data)
        with open(path + ".sig", "wb") as f:
            f.write(signature)

        messagebox.showinfo("Signed", "Document signed successfully")

    # ---------------------------
    def verify_document(self):
        path = filedialog.askopenfilename(title="Select document")
        if not path:
            return

        username = simpledialog.askstring("Verify", "Signer username:")
        record = get_user(username)

        cert_bytes, revoked = record
        if revoked:
            messagebox.showerror("Error", "Certificate revoked")
            return

        cert = x509.load_pem_x509_certificate(cert_bytes)
        public_key = cert.public_key()

        with open(path, "rb") as f:
            data = f.read()
        with open(path + ".sig", "rb") as f:
            sig = f.read()

        try:
            verify(public_key, sig, data)
            messagebox.showinfo("Valid", "Signature valid. Document authentic.")
        except:
            messagebox.showerror("Invalid", "Signature invalid or document modified")

    # ---------------------------
    def revoke(self):
        username = simpledialog.askstring("Revoke", "Username:")
        revoke_user(username)
        messagebox.showinfo("Revoked", "Certificate revoked")

if __name__ == "__main__":
    root = tk.Tk()
    PKIApp(root)
    root.mainloop()

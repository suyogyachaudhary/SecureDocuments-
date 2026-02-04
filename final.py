import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.x509.oid import NameOID
import subprocess
import webbrowser
import sys
import tempfile
import shutil

from ca import issue_certificate, verify_certificate
from crypto_utils import sign, verify
from database import add_user, get_user, revoke_user, verify_credentials, create_default_admin, change_password, admin_force_change_password, set_password

os.makedirs("users", exist_ok=True)

# Lightweight Tooltip helper
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind('<Enter>', self.show)
        widget.bind('<Leave>', self.hide)
    def show(self, _=None):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tip, text=self.text, background="#ffffe0", relief='solid', borderwidth=1, font=(None, 9))
        label.pack()
    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

class PKIApp:
    def __init__(self, root, current_user, is_admin=False):
        self.root = root
        self.current_user = current_user
        self.is_admin = is_admin
        root.title(f"PKI Secure Document System - {current_user}{' (admin)' if is_admin else ''}")
        root.geometry("640x420")
        root.configure(bg="#f6f9fc")

        # Header
        header = tk.Frame(root, bg="#263238", height=70)
        header.pack(fill='x')
        title = tk.Label(header, text="🔐 PKI Secure Document System", fg="#ffffff", bg="#263238", font=("Helvetica", 16, 'bold'))
        title.pack(side='left', padx=16, pady=14)
        user_badge = tk.Label(header, text=f"User: {current_user}", fg="#ffffff", bg="#37474f", font=("Helvetica", 10))
        user_badge.pack(side='right', padx=12, pady=18)
        if is_admin:
            admin_badge = tk.Label(header, text="ADMIN", fg="#ffffff", bg="#ff7043", font=("Helvetica", 9, 'bold'))
            admin_badge.pack(side='right', padx=(0,6), pady=18)

        # Main content frames
        content = tk.Frame(root, bg="#f6f9fc")
        content.pack(fill='both', expand=True, padx=12, pady=12)

        # Left: actions grouped
        left = tk.Frame(content, bg="#f6f9fc")
        left.pack(side='left', fill='y', padx=(0,12))

        # Certificate actions
        cert_frame = tk.LabelFrame(left, text="Certificate & User", padx=8, pady=8, bg="#f6f9fc")
        cert_frame.pack(fill='x', pady=6)
        btn_reg = tk.Button(cert_frame, text="🆕 Register (cert)", command=self.register, bg="#e8f5e9")
        btn_reg.pack(fill='x', pady=4)
        Tooltip(btn_reg, "Create a cert-only user and save private key locally")

        btn_auth = tk.Button(cert_frame, text="🔎 Authenticate (cert)", command=self.authenticate, bg="#e3f2fd")
        btn_auth.pack(fill='x', pady=4)
        Tooltip(btn_auth, "Validate a user's certificate")

        btn_revoke = tk.Button(cert_frame, text="🚫 Revoke", command=self.revoke, bg="#ffebee")
        btn_revoke.pack(fill='x', pady=4)
        Tooltip(btn_revoke, "Revoke a user's certificate")

        # Document actions
        doc_frame = tk.LabelFrame(left, text="Document", padx=8, pady=8, bg="#f6f9fc")
        doc_frame.pack(fill='x', pady=6)
        btn_sign = tk.Button(doc_frame, text="✍️ Sign Document", command=self.sign_document, bg="#fff8e1")
        btn_sign.pack(fill='x', pady=4)
        Tooltip(btn_sign, "Sign a selected file with a user's private key")

        btn_verify = tk.Button(doc_frame, text="✅ Verify Signature", command=self.verify_document, bg="#e8f5e9")
        btn_verify.pack(fill='x', pady=4)
        Tooltip(btn_verify, "Verify a file's signature using signer's certificate")

        # Right: admin panel or info
        right = tk.Frame(content, bg="#f6f9fc")
        right.pack(side='left', fill='both', expand=True)

        # Actions area
        actions_frame = tk.LabelFrame(right, text="Account", padx=8, pady=8, bg="#f6f9fc")
        actions_frame.pack(fill='x', pady=6)
        btn_chpwd = tk.Button(actions_frame, text="🔁 Change Password", command=self.change_password_ui, bg="#fff3e0")
        btn_chpwd.pack(fill='x', pady=4)
        Tooltip(btn_chpwd, "Change your account password")

        btn_logout = tk.Button(actions_frame, text="🚪 Logout", command=self.logout, bg="#eceff1")
        btn_logout.pack(fill='x', pady=4)
        Tooltip(btn_logout, "Logout and return to login screen")

        # Admin specific
        if self.is_admin:
            admin_frame = tk.LabelFrame(right, text="Admin Tools", padx=8, pady=8, bg="#f6f9fc")
            admin_frame.pack(fill='x', pady=6)
            btn_add = tk.Button(admin_frame, text="➕ Add User", command=self.add_user_admin, bg="#e0f7fa")
            btn_add.pack(fill='x', pady=4)
            Tooltip(btn_add, "Create a username+password and issue certificate")

            btn_reset = tk.Button(admin_frame, text="🔐 Reset User Password", command=self.admin_reset_password, bg="#fff3e0")
            btn_reset.pack(fill='x', pady=4)
            Tooltip(btn_reset, "Administratively set a user's password")

        # Status bar
        self.status = tk.Label(root, text="Ready", bd=1, relief='sunken', anchor='w')
        self.status.pack(side='bottom', fill='x')

    # ---------------------------
    def set_status(self, text):
        try:
            self.status.config(text=text)
        except Exception:
            pass

    def register(self):
        # Register a user with certificate only
        username = simpledialog.askstring("Register", "Enter username:")
        if not username:
            return

        self.set_status(f"Registering {username}...")
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

        self.set_status("Ready")
        messagebox.showinfo("Success", "User registered and certificate issued")

    # ---------------------------
    def add_user_admin(self):
        # Admin flow: create user with username and password
        username = simpledialog.askstring("Add User", "Enter new username:")
        if not username:
            return
        password = simpledialog.askstring("Add User", "Enter password for user:", show='*')
        if not password:
            messagebox.showwarning("Missing", "Password required")
            return

        self.set_status(f"Adding user {username}...")
        # Generate cert and private key
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        cert = issue_certificate(username, public_key)

        # Store in DB with password
        add_user(username, cert, password=password)

        with open(f"users/{username}.pem", "wb") as f:
            f.write(private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            ))

        self.set_status("Ready")
        messagebox.showinfo("Added", f"User '{username}' added with credentials")

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
        path = filedialog.askopenfilename(title="Select document to sign")
        if not username or not path:
            return

        key_path = f"users/{username}.pem"
        if not os.path.exists(key_path):
            messagebox.showerror("Missing Key", f"Private key for user '{username}' not found (expected {key_path}).\nPlease register the user or place the private key file there.")
            return

        try:
            with open(key_path, "rb") as f:
                private_key = serialization.load_pem_private_key(f.read(), None)
        except Exception as e:
            messagebox.showerror("Key Error", f"Failed to load private key for '{username}': {e}")
            return

        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to read document: {e}")
            return

        try:
            signature = sign(private_key, data)
            sig_path = path + ".sig"
            with open(sig_path, "wb") as f:
                f.write(signature)
        except Exception as e:
            messagebox.showerror("Signing Error", f"Failed to sign document: {e}")
            return

        messagebox.showinfo("Signed", f"Document signed successfully. Signature saved: {sig_path}")

    # ---------------------------
    def verify_document(self):
        path = filedialog.askopenfilename(title="Select document or signature")
        if not path:
            return

        # If user selected a .sig file, treat accordingly
        if path.lower().endswith('.sig'):
            sig_path = path
            doc_candidate = path[:-4]
            if os.path.exists(doc_candidate):
                doc_path = doc_candidate
            else:
                # try to find a matching non-.sig file in the same directory
                base = os.path.basename(path)[:-4]
                dirp = os.path.dirname(path) or '.'
                matches = [f for f in os.listdir(dirp) if f.startswith(base) and not f.endswith('.sig')]
                if len(matches) == 1:
                    doc_path = os.path.join(dirp, matches[0])
                else:
                    messagebox.showinfo("Select Document", "You selected a signature file. Please select the signed document file.")
                    doc_path = filedialog.askopenfilename(initialdir=dirp)
                    if not doc_path:
                        return
        else:
            doc_path = path
            sig_path = doc_path + '.sig'
            if not os.path.exists(sig_path):
                res = messagebox.askyesno("Signature not found", f"Signature file not found: {sig_path}\nWould you like to locate it?")
                if res:
                    sig_path = filedialog.askopenfilename(initialdir=os.path.dirname(doc_path) or '.')
                    if not sig_path:
                        return
                else:
                    return

        username = simpledialog.askstring("Verify", "Signer username:")
        if not username:
            return

        record = get_user(username)
        if not record:
            messagebox.showerror("Error", "User not found")
            return

        cert_bytes, revoked = record
        if revoked:
            messagebox.showerror("Error", "Certificate revoked")
            return

        try:
            cert = x509.load_pem_x509_certificate(cert_bytes)
        except Exception:
            messagebox.showerror("Error", "Invalid stored certificate for user")
            return

        public_key = cert.public_key()

        # Read document and signature (with graceful errors)
        try:
            with open(doc_path, "rb") as f:
                data = f.read()
        except Exception:
            messagebox.showerror("Error", f"Could not read document: {doc_path}")
            return

        try:
            with open(sig_path, "rb") as f:
                sig = f.read()
        except Exception:
            messagebox.showerror("Missing", f"Signature file not found: {sig_path}")
            return

        try:
            verify(public_key, sig, data)
        except Exception:
            messagebox.showerror("Invalid", "Signature invalid or document modified")
            return

        # Verification succeeded — offer extract + view options
        try:
            cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        except Exception:
            cn = username

        dlg = tk.Toplevel(self.root)
        dlg.title("Verified — Extract options")
        dlg.geometry("520x180")
        tk.Label(dlg, text=f"Signature valid. Signed by: {cn}", font=(None, 11, 'bold')).pack(pady=(10,6))

        def save_certificate():
            p = filedialog.asksaveasfilename(defaultextension=".pem", filetypes=[("Certificate","*.pem")], initialfile=f"{username}_cert.pem")
            if p:
                with open(p, "wb") as out:
                    out.write(cert_bytes)
                messagebox.showinfo("Saved", f"Certificate saved to {p}")

        def save_signature():
            p = filedialog.asksaveasfilename(defaultextension=".sig", filetypes=[("Signature","*.sig"), ("All files","*.*")], initialfile=os.path.basename(sig_path))
            if p:
                with open(sig_path, "rb") as fr:
                    sig_data = fr.read()
                with open(p, "wb") as fw:
                    fw.write(sig_data)
                messagebox.showinfo("Saved", f"Signature saved to {p}")

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="🔁 Extract Certificate", command=save_certificate, bg="#e3f2fd").grid(row=0, column=0, padx=8)
        tk.Button(btn_frame, text="📄 Save Signature file", command=save_signature, bg="#fff8e1").grid(row=0, column=1, padx=8)

        # Save document copy
        def save_document():
            p = filedialog.asksaveasfilename(defaultextension=os.path.splitext(doc_path)[1] or "", initialfile=os.path.basename(doc_path))
            if p:
                with open(doc_path, "rb") as fr:
                    data = fr.read()
                with open(p, "wb") as fw:
                    fw.write(data)
                messagebox.showinfo("Saved", f"Document saved to {p}")

        # View/open document using platform default application
        def view_document():
            # Try to open with system default; on failure allow saving and re-opening
            try:
                if os.name == 'nt':
                    os.startfile(doc_path)
                elif sys.platform == 'darwin':
                    subprocess.run(['open', doc_path], check=True)
                else:
                    # Linux/Unix
                    subprocess.run(['xdg-open', doc_path], check=True)
                return
            except Exception as e:
                # Provide a clear error and offer to save & open
                res = messagebox.askyesno("Open Failed", f"Failed to open file with system viewer.\nError: {e}\n\nSave a copy and try to open it? ")
                if not res:
                    # fallback to text preview if possible
                    try:
                        with open(doc_path, 'rb') as fr:
                            raw = fr.read()
                        try:
                            txt = raw.decode('utf-8')
                        except Exception:
                            txt = None
                        if txt is None:
                            messagebox.showwarning("Cannot Open", "Could not open file directly and cannot preview binary files.")
                            return
                        v = tk.Toplevel(self.root)
                        v.title(f"Viewing: {os.path.basename(doc_path)}")
                        text = tk.Text(v, wrap='word')
                        text.insert('1.0', txt)
                        text.config(state='disabled')
                        text.pack(fill='both', expand=True)
                        return
                    except Exception:
                        messagebox.showwarning("Cannot Open", "Failed to preview the file.")
                        return

                # Save as dialog
                p = filedialog.asksaveasfilename(defaultextension=os.path.splitext(doc_path)[1] or "", initialfile=os.path.basename(doc_path))
                if not p:
                    return
                try:
                    shutil.copyfile(doc_path, p)
                    # Try to open saved copy
                    try:
                        if os.name == 'nt':
                            os.startfile(p)
                        elif sys.platform == 'darwin':
                            subprocess.run(['open', p], check=True)
                        else:
                            subprocess.run(['xdg-open', p], check=True)
                    except Exception as e2:
                        messagebox.showerror("Open Error", f"Saved to {p} but failed to open. Error: {e2}")
                    else:
                        messagebox.showinfo("Saved & Opening", f"Saved and opened {p}")
                except Exception as e3:
                    messagebox.showerror("Save Failed", f"Failed to save file: {e3}")

        tk.Button(btn_frame, text="📁 Save Document", command=save_document, bg="#e8f5e9").grid(row=0, column=2, padx=8)
        tk.Button(btn_frame, text="👁️ View Document", command=view_document, bg="#e3f2fd").grid(row=0, column=3, padx=8)

        tk.Button(dlg, text="Close", command=dlg.destroy, bg="#eceff1").pack(pady=6)

    # ---------------------------
    def revoke(self):
        username = simpledialog.askstring("Revoke", "Username:")
        revoke_user(username)
        messagebox.showinfo("Revoked", "Certificate revoked")

    def change_password_ui(self):
        old = simpledialog.askstring("Change Password", "Enter current password:", show='*')
        if old is None:
            return
        new = simpledialog.askstring("Change Password", "Enter new password:", show='*')
        if new is None:
            return
        confirm = simpledialog.askstring("Change Password", "Confirm new password:", show='*')
        if confirm is None:
            return
        if new != confirm:
            messagebox.showerror("Mismatch", "New passwords do not match")
            return
        if change_password(self.current_user, old, new):
            messagebox.showinfo("Changed", "Password changed successfully")
        else:
            messagebox.showerror("Error", "Current password is incorrect")

    def admin_reset_password(self):
        target = simpledialog.askstring("Reset User Password", "Enter username to reset:")
        if not target:
            return
        new = simpledialog.askstring("Reset Password", f"Enter new password for '{target}':", show='*')
        if not new:
            messagebox.showwarning("Missing", "Password required")
            return
        admin_force_change_password(target, new)
        messagebox.showinfo("Reset", f"Password for '{target}' has been reset")

    def logout(self):
        # Clear current UI and show login screen
        for widget in self.root.winfo_children():
            widget.destroy()
        show_login_and_launch()

# ---------------------------
# Login landing page
# ---------------------------

def show_login_and_launch():
    create_default_admin()  # ensure default admin exists

    root = tk.Tk()
    root.title("PKI Secure System - Login")
    root.geometry("420x260")
    root.configure(bg="#eceff1")

    frm = tk.Frame(root, bg="#eceff1")
    frm.pack(fill='both', expand=True)

    header = tk.Label(frm, text="🔐 Please log in", font=("Helvetica", 14, 'bold'), bg="#eceff1")
    header.pack(pady=(18,6))

    inner = tk.Frame(frm, bg="#ffffff", padx=12, pady=12, bd=1, relief='groove')
    inner.pack(padx=18, pady=8)

    tk.Label(inner, text="Username:", bg="#ffffff").grid(row=0, column=0, sticky='w')
    username_entry = tk.Entry(inner)
    username_entry.grid(row=0, column=1, pady=6)

    tk.Label(inner, text="Password:", bg="#ffffff").grid(row=1, column=0, sticky='w')
    password_entry = tk.Entry(inner, show='*')
    password_entry.grid(row=1, column=1, pady=6)

    def attempt_login():
        user = username_entry.get()
        pwd = password_entry.get()
        ok, is_admin, must_change = verify_credentials(user, pwd)
        if not ok:
            messagebox.showerror("Login Failed", "Invalid credentials or user revoked")
            return

        # If user must change password (e.g., default admin) force a change now
        if must_change:
            new = simpledialog.askstring("Change Password", "Enter new password:", show='*')
            if not new:
                messagebox.showwarning("Required", "You must set a new password before proceeding")
                return
            confirm = simpledialog.askstring("Change Password", "Confirm new password:", show='*')
            if new != confirm:
                messagebox.showerror("Mismatch", "New passwords do not match")
                return
            # attempt to change using old pwd
            if not change_password(user, pwd, new):
                messagebox.showerror("Error", "Failed to change password. Login aborted.")
                return
            messagebox.showinfo("Changed", "Password updated. Proceeding to application")

        # Destroy login UI and launch main app in same root
        for widget in root.winfo_children():
            widget.destroy()
        PKIApp(root, current_user=user, is_admin=is_admin)

    login_btn = tk.Button(frm, text="Login 🔐", command=attempt_login, bg="#2e7d32", fg="#ffffff", padx=12, pady=8, font=(None,10,'bold'))
    login_btn.pack(pady=12)

    root.mainloop()

if __name__ == "__main__":
    show_login_and_launch()

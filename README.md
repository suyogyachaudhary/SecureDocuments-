# SecureDocuments - PKI File Signing & Encryption 🛡️

A simple local desktop application that demonstrates basic PKI-based user management, document signing and verification, file encryption, and secure credential storage. Built with Python and Tkinter for educational and prototype purposes.

## Features
- Login landing page with default admin account (must change on first login)
- Admin: add users (username + password) and reset passwords
- Register users (certificate issuance) and store private key locally
- Sign and verify documents using RSA keys and X.509 certificates
- Revoke certificates, change passwords, and extract certificates/signatures
- Secure password storage using PBKDF2-HMAC-SHA256
- Unit tests for credential flows

## Quick Start 🚀
Prerequisites:
- Python 3.8+ (3.13 tested)
- Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the app:

```bash
python final.py
# or
py final.py
```

Default admin credentials (first-run):
- Username: `admin`
- Password: `admin123`

You will be forced to change the admin password on first login.

## UI Notes
- Login screen is the entry point. Admins see an **Admin Tools** panel after signing in.
- You can select either the document or its `.sig` file when verifying; the app will try to resolve both.
- After verification you can extract certificate, save signature, save or view document.

## Testing ✅
Run unit tests:

```bash
python -m unittest discover -v tests
```

## Security & Best Practices ⚠️
- **Do not commit** private keys and database files. This repo includes a `.gitignore` that excludes `users/*.pem`, `*.db`, and virtual environments.
- If sensitive files were committed previously, contact me and we can remove them from history (requires history rewrite and force-push).
- Consider using Git LFS for large binaries (the repo currently contains large files that triggered GitHub warnings).

## Dev workflow
- Work in feature branches. I pushed the current development to the `developer` branch on your remote.
- To push new changes:

```bash
git checkout -b my-feature
# make changes
git add -A
git commit -m "Describe changes"
git push origin my-feature
```

## Troubleshooting
- If the app cannot open a file for viewing, it will offer to save a copy and attempt to open that copy.
- If you see errors about missing signature files, select the signed document or point the app to the `.sig` file when prompted.

## Contributing
Open issues or pull requests on the repo. If you want me to add features (password complexity enforcement, LFS, remove secrets, CI, packaging), tell me which and I can implement them.

---

Licensed under the MIT License. (Add your preferred license file if needed.)

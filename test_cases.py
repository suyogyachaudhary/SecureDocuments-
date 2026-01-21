from user import register_user, authenticate_user
from document import sign_document, verify_document
from database import get_user, revoke_user

# Register users
register_user("alice")
register_user("bob")

# Authenticate
authenticate_user("alice")

# Sign document
sign_document("alice", "sample.txt")

# Verify document
cert, _ = get_user("alice")
verify_document("sample.txt", cert)

# Simulate revocation
revoke_user("alice")
authenticate_user("alice")  # Should fail


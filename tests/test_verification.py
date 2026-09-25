import os
import sys
from pathlib import Path

# Add project root (LocaBazaar) to sys.path and ensure .env is found from any directory
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from app.core.verification import generate_verification_token, verify_verification_token

def test_verification_token():
    email = "test@example.com"
    token = generate_verification_token(email)
    print("\nGenerated token:", token)
    result = verify_verification_token(token)
    print("Verified email:", result)
    assert result == email


def test_tampered_token():
    email = "test@example.com"

    token = generate_verification_token(email)

    # Corrupt the signature
    tampered_token = token[:-5] + ("xxxxx" if not token.endswith("xxxxx") else "yyyyy")

    result = verify_verification_token(tampered_token)

    assert result is None

from app.core.security import create_access_token


def test_access_token_rejected():
    token = create_access_token(
        data={
            "sub": "test@example.com",
            "id": 1,
            "role": "customer",
        }
    )

    result = verify_verification_token(token)

    assert result is None
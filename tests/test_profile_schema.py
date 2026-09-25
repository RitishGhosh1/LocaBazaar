import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from app.schemas.user import UserUpdate, UserRead
from app.models.user import UserRole

def test_user_update_schema():
    # Partial updates
    update_data = UserUpdate(name="John Doe", phone="9876543210")
    dump = update_data.model_dump(exclude_unset=True)
    assert dump == {"name": "John Doe", "phone": "9876543210"}
    assert "bio" not in dump

    # All fields
    update_full = UserUpdate(name="Jane Doe", phone="1234567890", bio="Hello world")
    dump_full = update_full.model_dump(exclude_unset=True)
    assert dump_full == {"name": "Jane Doe", "phone": "1234567890", "bio": "Hello world"}

def test_user_read_schema():
    read_data = UserRead(
        id=1,
        name="John Doe",
        email="john@example.com",
        phone="9876543210",
        bio="Test bio",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
    )
    assert read_data.id == 1
    assert read_data.phone == "9876543210"
    assert read_data.bio == "Test bio"

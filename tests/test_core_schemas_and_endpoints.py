import pytest
from app.schemas.service import ServiceUpdate, ServiceCreate
from app.schemas.booking import BookingStatusUpdate, BookingStatus
from app.schemas.user import UserCreate, UserBase
from pydantic import ValidationError

def test_service_update_schema():
    # Partial updates should be valid
    update = ServiceUpdate(name="Updated AC Repair", price=1500)
    assert update.name == "Updated AC Repair"
    assert update.price == 1500
    assert update.description is None
    assert update.category_id is None

def test_booking_status_cancellation_schema():
    status_update = BookingStatusUpdate(status=BookingStatus.CANCELLED, note="Customer requested cancellation")
    assert status_update.status == BookingStatus.CANCELLED
    assert status_update.note == "Customer requested cancellation"

def test_user_base_validation_bounds():
    # Empty name should fail validation
    with pytest.raises(ValidationError):
        UserBase(name="", email="test@example.com")
    
    # Valid name should pass
    user = UserBase(name="John Doe", email="john@example.com")
    assert user.name == "John Doe"

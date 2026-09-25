import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from app.schemas.reviews import ReviewCreate, ReviewRead, ReviewUpdate, ReviewListResponse
from app.schemas.service import ServiceCreate, ServiceRead, ServiceUpdate, ServiceShortRead
from app.schemas.user import UserRead, UserUpdate, UserBase, UserRole

def test_review_create_schema():
    payload = ReviewCreate(rating=5, comment="Exceptional service!", service_id=1)
    assert payload.rating == 5
    assert payload.comment == "Exceptional service!"
    assert payload.service_id == 1

def test_review_rating_validation():
    # Rating < 1 must fail
    with pytest.raises(ValidationError):
        ReviewCreate(rating=0, comment="Bad", service_id=1)

    # Rating > 5 must fail
    with pytest.raises(ValidationError):
        ReviewCreate(rating=6, comment="Super", service_id=1)

def test_review_read_schema_persisted_fields():
    now = datetime.now(timezone.utc)
    read = ReviewRead(
        id=42,
        user_id=10,
        service_id=1,
        rating=4,
        comment="Great job",
        created_at=now,
        updated_at=now,
    )
    assert read.id == 42
    assert read.user_id == 10
    assert read.service_id == 1
    assert read.rating == 4
    assert read.created_at == now
    assert read.updated_at == now

def test_review_update_schema():
    update = ReviewUpdate(rating=4, comment="Updated experience")
    assert update.rating == 4
    assert update.comment == "Updated experience"

    partial = ReviewUpdate(comment="Just comment")
    assert partial.rating is None
    assert partial.comment == "Just comment"

    with pytest.raises(ValidationError):
        ReviewUpdate(rating=10)

def test_service_image_url_schema():
    svc = ServiceCreate(
        name="House Deep Cleaning",
        category_id=2,
        description="Comprehensive cleaning",
        price=2999,
        image_url="/uploads/deep_clean.jpg"
    )
    assert svc.image_url == "/uploads/deep_clean.jpg"

    svc_update = ServiceUpdate(image_url="/uploads/new_clean.webp")
    assert svc_update.image_url == "/uploads/new_clean.webp"

def test_user_avatar_url_schema():
    user = UserBase(
        name="Alice Kumar",
        email="alice@example.com",
        avatar_url="/uploads/alice.png"
    )
    assert user.avatar_url == "/uploads/alice.png"

    user_update = UserUpdate(avatar_url="/uploads/alice_new.jpg")
    assert user_update.avatar_url == "/uploads/alice_new.jpg"

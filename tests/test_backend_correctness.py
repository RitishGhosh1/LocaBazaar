import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.sql.schema import MetaData

# Patch create_all before importing app to avoid DB connection requirement during unit testing
with patch.object(MetaData, 'create_all'):
    from app.main import app
    from app.core.redis import redis_cache
    from app.models.user import User, UserRole
    from app.models.services import Service
    from app.models.booking import Booking, BookingStatus
    from app.models.reviews import Review
    from app.models.category import Category
    from app.schemas.reviews import ReviewCreate, ReviewRead, ReviewListResponse
    from app.schemas.service import ServiceCreate, ServiceRead, ServiceShortRead, ServiceListResponse

client = TestClient(app)

def test_openapi_schema():
    """Verify that OpenAPI schema generates properly and contains expected paths."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]
    
    # Check that key endpoints exist in the schema
    assert "/api/v1/services/mine" in paths
    assert "/api/v1/services/{service_id}" in paths
    assert "/api/v1/services/{service_id}/toggle" in paths
    assert "/api/v1/services/" in paths
    assert "/api/v1/reviews/" in paths
    assert "/api/v1/reviews/service/{service_id}" in paths
    assert "/api/v1/reviews/{review_id}" in paths
    assert "/api/v1/categories/" in paths
    assert "/api/v1/categories/{category_id}" in paths
    assert "/api/v1/categories/create" in paths
    assert "/api/v1/admin/services/{service_id}/suspend" in paths
    assert "/api/v1/admin/services/{service_id}/unsuspend" in paths
    assert "/api/v1/admin/reviews/{review_id}" in paths
    assert "/api/v1/admin/users/{user_id}/deactivate" in paths
    assert "/api/v1/admin/users/{user_id}/reactivate" in paths

def test_reviews_route_ordering():
    """Verify that /reviews/service/{service_id} matches before /reviews/{review_id}."""
    # Find route matches in FastAPI router
    matched_endpoint = None
    for route in app.routes:
        if hasattr(route, "path") and route.path == "/api/v1/reviews/service/{service_id}":
            matched_endpoint = route.endpoint.__name__
            break
    assert matched_endpoint == "get_reviews_for_service"

    # Also verify route index order
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    service_review_idx = routes.index("/api/v1/reviews/service/{service_id}")
    single_review_idx = routes.index("/api/v1/reviews/{review_id}")
    assert service_review_idx < single_review_idx, "Route /service/{service_id} must be registered before /{review_id}"

def test_services_route_ordering():
    """Verify that /services/mine is registered before /services/{service_id}."""
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    mine_idx = routes.index("/api/v1/services/mine")
    service_idx = routes.index("/api/v1/services/{service_id}")
    assert mine_idx < service_idx, "Route /services/mine must be registered before /services/{service_id}"

@pytest.mark.asyncio
async def test_review_create_serialization():
    """Verify that ReviewCreate can serialize from ORM model without validation error."""
    mock_review = MagicMock()
    mock_review.rating = 5
    mock_review.comment = "Excellent"
    mock_review.service_id = 42
    mock_review.id = 1
    mock_review.user_id = 10
    
    validated = ReviewCreate.model_validate(mock_review)
    assert validated.rating == 5
    assert validated.service_id == 42
    assert validated.comment == "Excellent"

@pytest.mark.asyncio
async def test_services_cache_invalidation_on_create():
    """Verify that create_service clears pattern 'services:q:*'."""
    from app.api.v1.endpoints.services import create_service
    
    mock_db = AsyncMock()
    mock_user = MagicMock(id=1, is_active=True, role=UserRole.PROVIDER)
    service_in = ServiceCreate(name="Plumbing", category_id=1, price=100, description="Pipe repair")
    
    with patch.object(redis_cache, "clear_pattern", new_callable=AsyncMock) as mock_clear_pattern:
        await create_service(service_in=service_in, db=mock_db, user=mock_user)
        mock_clear_pattern.assert_awaited_once_with("services:q:*")

@pytest.mark.asyncio
async def test_services_cache_invalidation_on_toggle():
    """Verify that toggle_service_status clears 'service_id:{id}' and pattern 'services:q:*'."""
    from app.api.v1.endpoints.services import toggle_service_status
    
    mock_service = MagicMock(id=10, owner_id=1, is_active=True)
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_service
    mock_db.execute.return_value = mock_result
    mock_user = MagicMock(id=1, is_active=True)
    
    with patch.object(redis_cache, "clear", new_callable=AsyncMock) as mock_clear, \
         patch.object(redis_cache, "clear_pattern", new_callable=AsyncMock) as mock_clear_pattern:
        await toggle_service_status(service_id=10, db=mock_db, user=mock_user)
        mock_clear.assert_awaited_once_with("service_id:10")
        mock_clear_pattern.assert_awaited_once_with("services:q:*")

@pytest.mark.asyncio
async def test_reviews_cache_invalidation_on_create():
    """Verify that create_review clears pattern 'reviews:svc:{service_id}:*'."""
    from app.api.v1.endpoints.reviews import create_review
    
    mock_db = AsyncMock()
    mock_booking_res = MagicMock()
    mock_booking_res.scalars.return_value.first.return_value = MagicMock(id=1)
    mock_review_res = MagicMock()
    mock_review_res.scalars.return_value.first.return_value = None
    
    mock_db.execute.side_effect = [mock_booking_res, mock_review_res]
    mock_user = MagicMock(id=2, role="customer")
    review_in = ReviewCreate(rating=5, comment="Great service", service_id=42)
    
    with patch.object(redis_cache, "clear_pattern", new_callable=AsyncMock) as mock_clear_pattern:
        await create_review(review=review_in, db=mock_db, current_user=mock_user)
        mock_clear_pattern.assert_awaited_once_with("reviews:svc:42:*")

@pytest.mark.asyncio
async def test_admin_suspend_service_cache_invalidation():
    """Verify admin_suspend_service clears 'service_id:{id}' and pattern 'services:q:*'."""
    from app.api.v1.endpoints.admin import admin_suspend_service
    
    mock_service = MagicMock(id=7, is_active=True)
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.first.return_value = mock_service
    mock_db.execute.return_value = mock_res
    mock_admin = MagicMock(id=99, is_superuser=True)
    
    with patch.object(redis_cache, "clear", new_callable=AsyncMock) as mock_clear, \
         patch.object(redis_cache, "clear_pattern", new_callable=AsyncMock) as mock_clear_pattern:
        await admin_suspend_service(service_id=7, db=mock_db, admin=mock_admin)
        mock_clear.assert_awaited_once_with("service_id:7")
        mock_clear_pattern.assert_awaited_once_with("services:q:*")

@pytest.mark.asyncio
async def test_admin_unsuspend_service_cache_invalidation():
    """Verify admin_unsuspend_service clears 'service_id:{id}' and pattern 'services:q:*'."""
    from app.api.v1.endpoints.admin import admin_unsuspend_service
    
    mock_service = MagicMock(id=7, is_active=False)
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.first.return_value = mock_service
    mock_db.execute.return_value = mock_res
    mock_admin = MagicMock(id=99, is_superuser=True)
    
    with patch.object(redis_cache, "clear", new_callable=AsyncMock) as mock_clear, \
         patch.object(redis_cache, "clear_pattern", new_callable=AsyncMock) as mock_clear_pattern:
        await admin_unsuspend_service(service_id=7, db=mock_db, admin=mock_admin)
        mock_clear.assert_awaited_once_with("service_id:7")
        mock_clear_pattern.assert_awaited_once_with("services:q:*")

@pytest.mark.asyncio
async def test_admin_delete_review_cache_invalidation():
    """Verify admin_delete_review fetches service_id and clears pattern 'reviews:svc:{service_id}:*'."""
    from app.api.v1.endpoints.admin import admin_delete_review
    
    mock_review = MagicMock(id=15, service_id=88)
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.first.return_value = mock_review
    mock_db.execute.return_value = mock_res
    mock_admin = MagicMock(id=99, is_superuser=True)
    
    with patch.object(redis_cache, "clear_pattern", new_callable=AsyncMock) as mock_clear_pattern:
        await admin_delete_review(review_id=15, db=mock_db, admin=mock_admin)
        mock_clear_pattern.assert_awaited_once_with("reviews:svc:88:*")

@pytest.mark.asyncio
async def test_admin_deactivate_user_cache_invalidation():
    """Verify admin_deactivate_user clears 'service_id:*' and 'services:q:*' without fake user/booking keys."""
    from app.api.v1.endpoints.admin import admin_deactivate_user
    
    mock_target = MagicMock(id=5, is_active=True, is_superuser=False)
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.first.return_value = mock_target
    mock_db.execute.return_value = mock_res
    mock_admin = MagicMock(id=99, is_superuser=True)
    
    with patch.object(redis_cache, "clear_pattern", new_callable=AsyncMock) as mock_clear_pattern, \
         patch.object(redis_cache, "clear", new_callable=AsyncMock) as mock_clear:
        await admin_deactivate_user(user_id=5, db=mock_db, admin=mock_admin)
        assert mock_clear.call_count == 0
        mock_clear_pattern.assert_any_await("service_id:*")
        mock_clear_pattern.assert_any_await("services:q:*")

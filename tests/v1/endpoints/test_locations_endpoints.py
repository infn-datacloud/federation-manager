"""Integration tests for fed_mgr.v1.locations.endpoints.

Tests in this file:
- test_options_locations
- test_create_location_success
- test_create_location_conflict
- test_create_location_not_null_error
- test_get_locations_success
- test_get_location_success
- test_get_location_not_found
- test_edit_location_success
- test_edit_location_not_found
- test_edit_location_conflict
- test_edit_location_not_null_error
- test_delete_location_success
"""

import uuid

from fed_mgr.exceptions import ConflictError, NoItemToUpdateError, NotNullError
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.locations.crud import get_location

DUMMY_NAME = "Test Location"
DUMMY_COUNTRY = "IT"
DUMMY_LAT = 45.0
DUMMY_LON = 9.0
DUMMY_DESC = "A test location."
DUMMY_CREATED_AT = "2024-01-01T00:00:00Z"


def fake_add_location(fake_id):
    """Return a fake location object with the given id."""

    class FakeLocation:
        id = fake_id

    return FakeLocation()


def test_options_locations(client):
    """Test OPTIONS /locations/ returns 204 and Allow header."""
    resp = client.options("/api/v1/locations/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


def test_create_location_success(client, monkeypatch):
    """Test POST /locations/ creates a location and returns 201 with id."""
    fake_id = str(uuid.uuid4())
    location_data = {
        "name": DUMMY_NAME,
        "country": DUMMY_COUNTRY,
        "lat": DUMMY_LAT,
        "lon": DUMMY_LON,
        "description": DUMMY_DESC,
    }
    monkeypatch.setattr(
        "fed_mgr.v1.locations.endpoints.add_location",
        lambda session, location, created_by: fake_add_location(fake_id),
    )
    resp = client.post("/api/v1/locations/", json=location_data)
    assert resp.status_code == 201
    assert resp.json() == {"id": fake_id}


def test_create_location_conflict(client, monkeypatch):
    """Test POST /locations/ returns 409 if location already exists."""
    location_data = {
        "name": DUMMY_NAME,
        "country": DUMMY_COUNTRY,
        "lat": DUMMY_LAT,
        "lon": DUMMY_LON,
        "description": DUMMY_DESC,
    }

    def fake_add_location(session, location, created_by):
        raise ConflictError("Location already exists")

    monkeypatch.setattr(
        "fed_mgr.v1.locations.endpoints.add_location", fake_add_location
    )
    resp = client.post("/api/v1/locations/", json=location_data)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Location already exists"


def test_create_location_not_null_error(client, monkeypatch):
    """Test POST /locations/ returns 422 if a not null error occurs."""
    location_data = {
        "name": DUMMY_NAME,
        "country": DUMMY_COUNTRY,
        "lat": DUMMY_LAT,
        "lon": DUMMY_LON,
        "description": DUMMY_DESC,
    }

    def fake_add_location(session, location, created_by):
        raise NotNullError("Field 'name' cannot be null")

    monkeypatch.setattr(
        "fed_mgr.v1.locations.endpoints.add_location", fake_add_location
    )
    resp = client.post("/api/v1/locations/", json=location_data)
    assert resp.status_code == 422
    assert "cannot be null" in resp.json()["detail"]


def test_get_locations_success(client, monkeypatch):
    """Test GET /locations/ returns paginated location list."""
    fake_locations = []
    fake_total = 0

    def fake_get_locations(session, skip, limit, sort, **kwargs):
        return fake_locations, fake_total

    monkeypatch.setattr(
        "fed_mgr.v1.locations.endpoints.get_locations", fake_get_locations
    )
    resp = client.get("/api/v1/locations/")
    assert resp.status_code == 200
    assert "data" in resp.json()


def test_get_location_success(client):
    """Test GET /locations/{location_id} returns location if found."""
    fake_id = str(uuid.uuid4())

    class FakeLocation:
        id = fake_id
        name = DUMMY_NAME
        country = DUMMY_COUNTRY
        lat = DUMMY_LAT
        lon = DUMMY_LON
        description = DUMMY_DESC
        created_at = DUMMY_CREATED_AT
        created_by = fake_id
        updated_at = DUMMY_CREATED_AT
        updated_by = fake_id

        def model_dump(self):
            return {
                "id": self.id,
                "name": self.name,
                "country": self.country,
                "lat": self.lat,
                "lon": self.lon,
                "description": self.description,
                "created_at": self.created_at,
                "created_by": self.created_by,
                "updated_at": self.updated_at,
                "updated_by": self.updated_by,
            }

    def fake_get_location(location_id, session=None):
        return FakeLocation()

    sub_app_v1.dependency_overrides[get_location] = fake_get_location
    resp = client.get(f"/api/v1/locations/{fake_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == fake_id


def test_get_location_not_found(client):
    """Test GET /locations/{location_id} returns 404 if not found."""
    fake_id = str(uuid.uuid4())
    sub_app_v1.dependency_overrides[get_location] = (
        lambda location_id, session=None: None
    )
    resp = client.get(f"/api/v1/locations/{fake_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_location_success(client, monkeypatch):
    """Test PUT /locations/{location_id} returns 204 on successful update."""
    fake_id = str(uuid.uuid4())
    location_data = {
        "name": DUMMY_NAME,
        "country": DUMMY_COUNTRY,
        "lat": DUMMY_LAT,
        "lon": DUMMY_LON,
        "description": DUMMY_DESC,
    }

    def fake_update_location(session, location_id, new_location, updated_by):
        return None

    monkeypatch.setattr(
        "fed_mgr.v1.locations.endpoints.update_location", fake_update_location
    )
    resp = client.put(f"/api/v1/locations/{fake_id}", json=location_data)
    assert resp.status_code == 204


def test_edit_location_not_found(client, monkeypatch):
    """Test PUT /locations/{location_id} returns 404 if not found."""
    fake_id = str(uuid.uuid4())
    location_data = {
        "name": DUMMY_NAME,
        "country": DUMMY_COUNTRY,
        "lat": DUMMY_LAT,
        "lon": DUMMY_LON,
        "description": DUMMY_DESC,
    }

    def fake_update_location(session, location_id, new_location, updated_by):
        raise NoItemToUpdateError("Location not found")

    monkeypatch.setattr(
        "fed_mgr.v1.locations.endpoints.update_location", fake_update_location
    )
    resp = client.put(f"/api/v1/locations/{fake_id}", json=location_data)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Location not found"


def test_edit_location_conflict(client, monkeypatch):
    """Test PUT /locations/{location_id} returns 409 if conflict error occurs."""
    fake_id = str(uuid.uuid4())
    location_data = {
        "name": DUMMY_NAME,
        "country": DUMMY_COUNTRY,
        "lat": DUMMY_LAT,
        "lon": DUMMY_LON,
        "description": DUMMY_DESC,
    }

    def fake_update_location(session, location_id, new_location, updated_by):
        raise ConflictError("Location already exists")

    monkeypatch.setattr(
        "fed_mgr.v1.locations.endpoints.update_location", fake_update_location
    )
    resp = client.put(f"/api/v1/locations/{fake_id}", json=location_data)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Location already exists"


def test_edit_location_not_null_error(client, monkeypatch):
    """Test PUT /locations/{location_id} returns 422 if not null error occurs."""
    fake_id = str(uuid.uuid4())
    location_data = {
        "name": DUMMY_NAME,
        "country": DUMMY_COUNTRY,
        "lat": DUMMY_LAT,
        "lon": DUMMY_LON,
        "description": DUMMY_DESC,
    }

    def fake_update_location(session, location_id, new_location, updated_by):
        raise NotNullError("Field 'name' cannot be null")

    monkeypatch.setattr(
        "fed_mgr.v1.locations.endpoints.update_location", fake_update_location
    )
    resp = client.put(f"/api/v1/locations/{fake_id}", json=location_data)
    assert resp.status_code == 422
    assert "cannot be null" in resp.json()["detail"]


def test_delete_location_success(client, monkeypatch):
    """Test DELETE /locations/{location_id} returns 204 on success."""
    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "fed_mgr.v1.locations.endpoints.delete_location",
        lambda session, location_id: None,
    )
    resp = client.delete(f"/api/v1/locations/{fake_id}")
    assert resp.status_code == 204

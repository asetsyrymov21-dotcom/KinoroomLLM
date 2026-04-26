from collections.abc import Iterable

from fastapi.testclient import TestClient

from app.api.deps import get_session
from app.main import app
from app.models.staff import Staff, StaffRole
from app.services.auth import hash_password


PASSWORD = "secret123"
PASSWORD_HASH = hash_password(PASSWORD)


class FakeScalarResult:
    def __init__(self, rows: Iterable[Staff]) -> None:
        self._rows = list(rows)

    def all(self) -> list[Staff]:
        return self._rows


class FakeExecuteResult:
    def __init__(self, rows: Iterable[Staff]) -> None:
        self._rows = list(rows)

    def scalars(self) -> FakeScalarResult:
        return FakeScalarResult(self._rows)


class FakeStaffSession:
    def __init__(self, staff: Iterable[Staff]) -> None:
        self._staff = list(staff)

    async def execute(self, statement) -> FakeExecuteResult:
        filters = {}
        for criterion in getattr(statement, "_where_criteria", ()):
            left = criterion.left
            table_name = getattr(getattr(left, "table", None), "name", None)
            column_name = getattr(left, "name", None)
            filters[(table_name, column_name)] = getattr(criterion.right, "value", None)

        username = filters.get(("staff", "username"))
        tenant_slug = filters.get(("tenants", "slug"))

        rows = [staff for staff in self._staff if staff.username == username]
        if tenant_slug is not None:
            rows = [
                staff
                for staff in rows
                if getattr(staff, "tenant_slug", None) == tenant_slug
            ]
        return FakeExecuteResult(sorted(rows, key=lambda staff: staff.id)[:2])


def make_staff(staff_id: int, tenant_id: int, tenant_slug: str) -> Staff:
    staff = Staff(
        id=staff_id,
        tenant_id=tenant_id,
        username="admin",
        password_hash=PASSWORD_HASH,
        role=StaffRole.admin,
    )
    staff.tenant_slug = tenant_slug
    return staff


def post_login(session: FakeStaffSession, payload: dict) -> tuple[int, dict]:
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/staff/login", json=payload)
        return response.status_code, response.json()
    finally:
        app.dependency_overrides.clear()


def test_login_requires_tenant_slug_when_username_matches_multiple_tenants() -> None:
    session = FakeStaffSession(
        [
            make_staff(staff_id=1, tenant_id=10, tenant_slug="alpha"),
            make_staff(staff_id=2, tenant_id=20, tenant_slug="beta"),
        ]
    )

    status_code, body = post_login(
        session,
        {"username": "admin", "password": PASSWORD},
    )

    assert status_code == 400
    assert body == {"detail": "Укажите tenant_slug для входа"}


def test_login_uses_tenant_slug_to_select_matching_staff() -> None:
    session = FakeStaffSession(
        [
            make_staff(staff_id=1, tenant_id=10, tenant_slug="alpha"),
            make_staff(staff_id=2, tenant_id=20, tenant_slug="beta"),
        ]
    )

    status_code, body = post_login(
        session,
        {"username": "admin", "password": PASSWORD, "tenant_slug": "beta"},
    )

    assert status_code == 200
    assert body["role"] == StaffRole.admin
    assert body["username"] == "admin"
    assert body["tenant_id"] == 20
    assert body["token"]

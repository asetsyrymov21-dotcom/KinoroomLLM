from collections.abc import Iterable

from fastapi.testclient import TestClient

from app.api.deps import get_session
from app.main import app
from app.models.staff import Staff, StaffRole
from app.models.tenant import Tenant
from app.services.auth import hash_password, verify_password


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

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


class FakeStaffSession:
    def __init__(self, staff: Iterable[Staff], tenants: Iterable[Tenant] = ()) -> None:
        self._staff = list(staff)
        self._tenants = list(tenants)

    async def execute(self, statement) -> FakeExecuteResult:
        filters = {}
        for criterion in getattr(statement, "_where_criteria", ()):
            left = criterion.left
            table_name = getattr(getattr(left, "table", None), "name", None)
            column_name = getattr(left, "name", None)
            filters[(table_name, column_name)] = getattr(criterion.right, "value", None)

        username = filters.get(("staff", "username"))
        slug = filters.get(("tenants", "slug"))
        if username is not None:
            rows = [staff for staff in self._staff if staff.username == username]
        elif slug is not None:
            rows = [tenant for tenant in self._tenants if tenant.slug == slug]
        else:
            rows = []
        return FakeExecuteResult(sorted(rows, key=lambda staff: staff.id)[:2])

    def add(self, obj) -> None:
        if isinstance(obj, Tenant):
            obj.id = len(self._tenants) + 1
            self._tenants.append(obj)
        elif isinstance(obj, Staff):
            obj.id = len(self._staff) + 1
            self._staff.append(obj)

    async def flush(self) -> None:
        return None

    async def refresh(self, obj) -> None:
        return None


def make_staff(staff_id: int, tenant_id: int, username: str = "admin") -> Staff:
    staff = Staff(
        id=staff_id,
        tenant_id=tenant_id,
        username=username,
        password_hash=PASSWORD_HASH,
        role=StaffRole.admin,
    )
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


def post_register(session: FakeStaffSession, payload: dict) -> tuple[int, dict]:
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/staff/register", json=payload)
        return response.status_code, response.json()
    finally:
        app.dependency_overrides.clear()


def test_login_rejects_username_that_matches_multiple_tenants() -> None:
    session = FakeStaffSession(
        [
            make_staff(staff_id=1, tenant_id=10),
            make_staff(staff_id=2, tenant_id=20),
        ]
    )

    status_code, body = post_login(
        session,
        {"username": "admin", "password": PASSWORD},
    )

    assert status_code == 400
    assert body == {
        "detail": "Логин найден в нескольких организациях. Создайте уникальные логины для сотрудников."
    }


def test_login_accepts_unique_username() -> None:
    session = FakeStaffSession([make_staff(staff_id=2, tenant_id=20)])

    status_code, body = post_login(
        session,
        {"username": "admin", "password": PASSWORD},
    )

    assert status_code == 200
    assert body["role"] == StaffRole.admin
    assert body["username"] == "admin"
    assert body["tenant_id"] == 20
    assert body["token"]


def test_register_creates_tenant_and_first_admin() -> None:
    session = FakeStaffSession(
        staff=[],
        tenants=[Tenant(id=1, name="KinoRoom Sirius", slug="kinoroom-sirius")],
    )

    status_code, body = post_register(
        session,
        {
            "tenant_name": "KinoRoom Sirius",
            "phone": "+777713659988",
            "email": "SIRIUS@ROOMPILOT.KZ",
            "password": PASSWORD,
        },
    )

    assert status_code == 201
    assert body["role"] == StaffRole.admin
    assert body["username"] == "sirius@roompilot.kz"
    assert body["tenant_id"] == 2
    assert body["token"]
    assert session._tenants[1].slug == "kinoroom-sirius-2"
    assert session._tenants[1].phone == "+777713659988"
    assert session._staff[0].tenant_id == 2
    assert session._staff[0].username == "sirius@roompilot.kz"
    assert verify_password(PASSWORD, session._staff[0].password_hash)


def test_register_rejects_existing_username() -> None:
    session = FakeStaffSession([make_staff(staff_id=1, tenant_id=10, username="admin@roompilot.kz")])

    status_code, body = post_register(
        session,
        {"tenant_name": "New KinoRoom", "email": "admin@roompilot.kz", "password": PASSWORD},
    )

    assert status_code == 400
    assert body == {"detail": "Пользователь с таким именем уже существует"}

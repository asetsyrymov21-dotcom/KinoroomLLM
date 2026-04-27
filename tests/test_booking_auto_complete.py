from app.services.booking import auto_complete_expired_bookings
import pytest


pytestmark = pytest.mark.anyio


class FakeResult:
    rowcount = 2


class FakeSession:
    def __init__(self) -> None:
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return FakeResult()


async def test_auto_complete_expired_bookings_updates_only_finished_regular_bookings() -> None:
    session = FakeSession()

    updated = await auto_complete_expired_bookings(session)

    assert updated == 2
    sql = str(session.statement)
    assert "bookings.status IN" in sql
    assert "bookings.is_open_ended IS false" in sql
    assert "bookings.end_time <=" in sql
    assert "status=" in sql
    assert "completed_at=bookings.end_time" in sql

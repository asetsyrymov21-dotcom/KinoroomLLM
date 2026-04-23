import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffRole(str, enum.Enum):
    admin = "admin"
    operator = "operator"


class Staff(Base):
    __tablename__ = "staff"
    __table_args__ = (UniqueConstraint("tenant_id", "username", name="uq_staff_tenant_username"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[StaffRole] = mapped_column(String(20), nullable=False, default=StaffRole.operator)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Staff id={self.id} tenant={self.tenant_id} username={self.username!r} role={self.role}>"

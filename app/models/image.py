
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, LargeBinary, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Image(Base):
    __tablename__ = "images"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Image id={self.id!r} filename={self.filename!r} type={self.content_type!r}>"
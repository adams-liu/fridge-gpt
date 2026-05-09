from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


Money = Annotated[float, Field(ge=0)]


class CheckoutItemAmount(StrEnum):
    full = "full"
    half = "half"
    done = "done"


class CheckoutItem(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    quantity: float | None = Field(default=None, ge=0)
    unit_price: Money | None = None
    line_total: Money | None = None
    shelf_life: int | None = Field(default=None, ge=0)
    amount: CheckoutItemAmount = CheckoutItemAmount.full

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Item name cannot be blank")
        return stripped


class CheckoutSnapshotCreate(BaseModel):
    source: str = Field(default="nofrills", min_length=1, max_length=80)
    page_url: HttpUrl
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: datetime | None = None
    subtotal: Money | None = None
    total: Money | None = None
    items: list[CheckoutItem] = Field(min_length=1)
    raw_parser_warnings: list[str] = Field(default_factory=list)


class CheckoutSnapshot(CheckoutSnapshotCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

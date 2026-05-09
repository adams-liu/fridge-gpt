import json
from datetime import datetime

from .database import connect
from .models import CheckoutSnapshot, CheckoutSnapshotCreate


def _row_to_snapshot(row) -> CheckoutSnapshot:
    data = dict(row)
    return CheckoutSnapshot(
        id=data["id"],
        source=data["source"],
        page_url=data["page_url"],
        captured_at=datetime.fromisoformat(data["captured_at"]),
        delivered_at=(
            datetime.fromisoformat(data["delivered_at"])
            if data["delivered_at"] is not None
            else None
        ),
        subtotal=data["subtotal"],
        total=data["total"],
        items=json.loads(data["items_json"]),
        raw_parser_warnings=json.loads(data["raw_parser_warnings_json"]),
        created_at=datetime.fromisoformat(data["created_at"]),
    )


def create_snapshot(snapshot: CheckoutSnapshotCreate) -> CheckoutSnapshot:
    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO checkout_snapshots (
                source,
                page_url,
                captured_at,
                delivered_at,
                subtotal,
                total,
                items_json,
                raw_parser_warnings_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot.source,
                str(snapshot.page_url),
                snapshot.captured_at.isoformat(),
                snapshot.delivered_at.isoformat()
                if snapshot.delivered_at is not None
                else None,
                snapshot.subtotal,
                snapshot.total,
                json.dumps([item.model_dump() for item in snapshot.items]),
                json.dumps(snapshot.raw_parser_warnings),
            ),
        )

        row = connection.execute(
            "SELECT * FROM checkout_snapshots WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return _row_to_snapshot(row)


def list_snapshots() -> list[CheckoutSnapshot]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM checkout_snapshots ORDER BY created_at DESC, id DESC"
        ).fetchall()
    return [_row_to_snapshot(row) for row in rows]


def get_snapshot(snapshot_id: int) -> CheckoutSnapshot | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM checkout_snapshots WHERE id = ?",
            (snapshot_id,),
        ).fetchone()
    return _row_to_snapshot(row) if row else None

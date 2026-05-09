from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .models import CheckoutSnapshot, CheckoutSnapshotCreate
from .repository import create_snapshot, get_snapshot, list_snapshots
from .security import require_token


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="fridge-gpt API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://127.0.0.1", "http://localhost"],
    allow_origin_regex=r"chrome-extension://.*",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/checkout-snapshots",
    response_model=CheckoutSnapshot,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_token)],
)
def save_checkout_snapshot(snapshot: CheckoutSnapshotCreate) -> CheckoutSnapshot:
    return create_snapshot(snapshot)


@app.get(
    "/api/checkout-snapshots",
    response_model=list[CheckoutSnapshot],
    dependencies=[Depends(require_token)],
)
def read_checkout_snapshots() -> list[CheckoutSnapshot]:
    return list_snapshots()


@app.get(
    "/api/checkout-snapshots/{snapshot_id}",
    response_model=CheckoutSnapshot,
    dependencies=[Depends(require_token)],
)
def read_checkout_snapshot(snapshot_id: int) -> CheckoutSnapshot:
    snapshot = get_snapshot(snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return snapshot

from fastapi import Depends, FastAPI

from apps.api.app.api.admin import router as admin_router
from apps.api.app.api.auth import require_viewer, router as auth_router
from apps.api.app.api.cms import router as cms_router
from apps.api.app.api.health import router as health_router
from apps.api.app.api.meta import router as meta_router
from apps.api.app.api.ndc import router as ndc_router
from apps.api.app.api.samples import router as samples_router
from apps.api.app.services.users import ensure_seed_users
from shared.db.session import get_session_factory
from shared.logging import configure_logging

configure_logging()

app = FastAPI(title="Pharmaceutical Economic Data Hub API", version="0.1.0")


@app.on_event("startup")
def seed_default_users() -> None:
    db = get_session_factory()()
    try:
        ensure_seed_users(db)
    finally:
        db.close()


app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(health_router, dependencies=[Depends(require_viewer)])
app.include_router(meta_router, dependencies=[Depends(require_viewer)])
app.include_router(ndc_router, dependencies=[Depends(require_viewer)])
app.include_router(cms_router, dependencies=[Depends(require_viewer)])
app.include_router(samples_router, dependencies=[Depends(require_viewer)])

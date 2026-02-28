from fastapi import FastAPI

from apps.api.app.api.cms import router as cms_router
from apps.api.app.api.health import router as health_router
from apps.api.app.api.meta import router as meta_router
from apps.api.app.api.ndc import router as ndc_router
from apps.api.app.api.samples import router as samples_router
from shared.logging import configure_logging

configure_logging()

app = FastAPI(title="Pharmaceutical Economic Data Hub API", version="0.1.0")

app.include_router(health_router)
app.include_router(meta_router)
app.include_router(ndc_router)
app.include_router(cms_router)
app.include_router(samples_router)

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from apps.api.app.db.session import get_db
from apps.api.app.services.samples import (
    get_exact_cms_pricing_rows,
    get_exact_master_dataframe_rows,
    get_exact_nadac_rows,
    get_exact_openfda_rows,
    get_exact_orange_book_rows,
    get_exact_purple_book_rows,
    get_master_dataframe_rows,
    get_random_cms_pricing_rows,
    get_random_nadac_rows,
    get_random_openfda_rows,
    get_random_orange_book_rows,
    get_random_purple_book_rows,
)

router = APIRouter(prefix="/samples", tags=["samples"])


@router.get("/raw/cms-pricing")
def sample_raw_cms_pricing(
    n: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return get_random_cms_pricing_rows(db, n)


@router.get("/raw/nadac")
def sample_raw_nadac(
    n: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return get_random_nadac_rows(db, n)


@router.get("/raw/openfda")
def sample_raw_openfda(
    n: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return get_random_openfda_rows(db, n)


@router.get("/raw/orange-book")
def sample_raw_orange_book(
    n: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return get_random_orange_book_rows(db, n)


@router.get("/raw/purple-book")
def sample_raw_purple_book(
    n: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return get_random_purple_book_rows(db, n)


@router.get("/master-dataframe")
def sample_master_dataframe(
    n: int = Query(default=100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    return get_master_dataframe_rows(n)


@router.get("/exact/cms-pricing")
def exact_raw_cms_pricing(
    request: Request,
    n: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    filters = {k: v for k, v in request.query_params.multi_items() if k != "n"}
    try:
        return get_exact_cms_pricing_rows(db, filters, n)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/exact/nadac")
def exact_raw_nadac(
    request: Request,
    n: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    filters = {k: v for k, v in request.query_params.multi_items() if k != "n"}
    try:
        return get_exact_nadac_rows(db, filters, n)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/exact/openfda")
def exact_raw_openfda(
    request: Request,
    n: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    filters = {k: v for k, v in request.query_params.multi_items() if k != "n"}
    try:
        return get_exact_openfda_rows(db, filters, n)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/exact/orange-book")
def exact_raw_orange_book(
    request: Request,
    n: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    filters = {k: v for k, v in request.query_params.multi_items() if k != "n"}
    try:
        return get_exact_orange_book_rows(db, filters, n)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/exact/purple-book")
def exact_raw_purple_book(
    request: Request,
    n: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    filters = {k: v for k, v in request.query_params.multi_items() if k != "n"}
    try:
        return get_exact_purple_book_rows(db, filters, n)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/exact/master-dataframe")
def exact_master_dataframe(
    request: Request,
    n: int = Query(default=100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    filters = {k: v for k, v in request.query_params.multi_items() if k != "n"}
    try:
        return get_exact_master_dataframe_rows(filters, n)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

import logging

from fastapi import Depends, HTTPException, openapi, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlmodel import Session

from app.api.v1 import router
from app.databases.database import get_session

log = logging.getLogger(__name__)


@router.get("/")
async def index():
    return {"message": "Response!!!"}


@router.get("/health")
async def health(db: Session = Depends(get_session)):
    db_conn = check_db_connection(db)

    if not db_conn:
        return HTTPException(status_code=500, detail="Database connection failed")

    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})


def check_db_connection(db: Session):
    try:
        conn_count = db.exec(
            text("SELECT COUNT(sa.*) FROM pg_catalog.pg_stat_activity sa")
        ).first()
        try:
            log.info(f"{conn_count[0]} active connections")
        except Exception as e:
            log.warning(f"Issue accessing connection count: {e}")
        return True
    except Exception as e:
        log.error(f"Database connection failed: {e}")
        return False


@router.get("/docs", include_in_schema=False)
async def get_docs():
    return openapi.docs.get_swagger_ui_html(
        openapi_url="/openapi.json", title="Common App API Docs"
    )


@router.get("/redoc", include_in_schema=False)
async def get_redoc():
    return openapi.docs.get_redoc_html(
        openapi_url="/openapi.json", title="Common App API Redoc"
    )


@router.get("/openapi.json", include_in_schema=False)
async def get_openapi():
    return openapi.utils.get_openapi(
        title="Common App API Spec", version="0.1.0", routes=router.routes
    )

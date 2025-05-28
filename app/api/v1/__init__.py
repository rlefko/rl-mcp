from fastapi import APIRouter

from .item.routes_item import router as item_router
from .item.tables_item import Item

router = APIRouter(prefix="/v1")

router.include_router(item_router, prefix="/item", tags=["Item"])

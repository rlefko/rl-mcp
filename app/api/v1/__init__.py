from fastapi import APIRouter

from .item.routes_item import router as item_router
from .item.tables_item import Item
from .stock.routes_stock import router as stock_router
from .stock.tables_stock import MarketCache, StockData, VectorEmbedding

router = APIRouter(prefix="/v1")

router.include_router(item_router, prefix="/item", tags=["Item"])
router.include_router(
    stock_router, prefix="/stock", tags=["Stock Market & Vector Search"]
)

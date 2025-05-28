from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.api.auth import authenticate
from app.api.v1.stock.controllers_stock import StockController
from app.api.v1.stock.models_stock import (
    CacheStats,
    MarketSummary,
    StockAnalysis,
    StockDataCreate,
    StockDataRead,
    StockDataUpdate,
    StockNews,
    StockPrice,
    VectorSearchQuery,
    VectorSearchResult,
)
from app.databases.database import get_session

router = APIRouter()


# Stock Data CRUD Operations
@router.get(
    "", response_model=list[StockDataRead], dependencies=[Depends(authenticate)]
)
def get_stock_data(
    db: Session = Depends(get_session),
    symbol: str | None = Query(None, description="Filter by stock symbol"),
    data_type: str | None = Query(
        None, description="Filter by data type (news, analysis, price)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> list[StockDataRead]:
    """Get stock data with optional filtering and pagination"""
    try:
        return StockController.get_stock_data(
            db=db, symbol=symbol, data_type=data_type, limit=limit, offset=offset
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "",
    response_model=StockDataRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate)],
)
async def create_stock_data(
    stock_data: StockDataCreate, db: Session = Depends(get_session)
) -> StockDataRead:
    """Create new stock data with vector embedding"""
    try:
        return await StockController.create_stock_data(db, stock_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# Vector Search Operations
@router.post(
    "/search",
    response_model=list[VectorSearchResult],
    dependencies=[Depends(authenticate)],
)
async def search_stock_data(
    query: VectorSearchQuery, db: Session = Depends(get_session)
) -> list[VectorSearchResult]:
    """Perform vector similarity search on stock data"""
    try:
        return await StockController.search_stock_data(db, query)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# Market Data Operations
@router.get(
    "/price/{symbol}", response_model=StockPrice, dependencies=[Depends(authenticate)]
)
async def get_stock_price(symbol: str) -> StockPrice:
    """Get current stock price"""
    try:
        price_data = await StockController.get_stock_price(symbol)
        if not price_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Price data not found for symbol: {symbol}",
            )
        return price_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/news", response_model=list[StockNews], dependencies=[Depends(authenticate)]
)
async def get_stock_news(
    symbol: str | None = Query(None, description="Filter by stock symbol"),
    limit: int = Query(
        20, ge=1, le=100, description="Number of news articles to return"
    ),
) -> list[StockNews]:
    """Get stock news with sentiment analysis"""
    try:
        return await StockController.get_stock_news(symbol, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/analysis/{symbol}",
    response_model=StockAnalysis,
    dependencies=[Depends(authenticate)],
)
async def analyze_stock(
    symbol: str, db: Session = Depends(get_session)
) -> StockAnalysis:
    """Perform comprehensive stock analysis"""
    try:
        return await StockController.analyze_stock(db, symbol)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/market/summary",
    response_model=MarketSummary,
    dependencies=[Depends(authenticate)],
)
async def get_market_summary(db: Session = Depends(get_session)) -> MarketSummary:
    """Get market summary with top gainers/losers and sentiment"""
    try:
        return await StockController.get_market_summary(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/market/trending", dependencies=[Depends(authenticate)])
def get_trending_symbols(
    db: Session = Depends(get_session),
    limit: int = Query(
        10, ge=1, le=50, description="Number of trending symbols to return"
    ),
) -> list[dict]:
    """Get trending stock symbols based on data volume"""
    try:
        return StockController.get_trending_symbols(db, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/ingest/news", dependencies=[Depends(authenticate)])
async def ingest_news_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    symbol: str | None = Query(None, description="Filter news by stock symbol"),
) -> dict:
    """Ingest news data in the background"""
    try:
        background_tasks.add_task(StockController.ingest_news_data, db, symbol)
        return {
            "message": "News ingestion started in background",
            "symbol": symbol,
            "status": "processing",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/ingest/news/sync", dependencies=[Depends(authenticate)])
async def ingest_news_data_sync(
    db: Session = Depends(get_session),
    symbol: str | None = Query(None, description="Filter news by stock symbol"),
) -> dict:
    """Ingest news data synchronously"""
    try:
        count = await StockController.ingest_news_data(db, symbol)
        return {
            "message": "News ingestion completed",
            "symbol": symbol,
            "ingested_count": count,
            "status": "completed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/cache/stats", response_model=CacheStats, dependencies=[Depends(authenticate)]
)
async def get_cache_stats(db: Session = Depends(get_session)) -> CacheStats:
    """Get cache performance statistics"""
    try:
        return await StockController.get_cache_stats(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/cache/cleanup", dependencies=[Depends(authenticate)])
async def cleanup_cache(
    background_tasks: BackgroundTasks, db: Session = Depends(get_session)
) -> dict:
    """Clean up expired cache entries"""
    try:
        background_tasks.add_task(StockController.cleanup_cache, db)
        return {
            "message": "Cache cleanup started in background",
            "status": "processing",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/health", dependencies=[Depends(authenticate)])
async def stock_health_check(db: Session = Depends(get_session)) -> dict:
    """Health check for stock service"""
    try:
        # Simple health check - count total stock data entries
        from sqlmodel import func, select

        from app.api.v1.stock.tables_stock import StockData

        stmt = select(func.count(StockData.id))
        total_entries = db.exec(stmt).first()

        cache_stats = await StockController.get_cache_stats(db)

        return {
            "status": "healthy",
            "service": "stock",
            "total_entries": total_entries,
            "cache_stats": cache_stats.model_dump(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}",
        )


# These routes with path parameters must come AFTER all specific routes
@router.get(
    "/{stock_data_id}",
    response_model=StockDataRead,
    dependencies=[Depends(authenticate)],
)
def get_stock_data_by_id(
    stock_data_id: int, db: Session = Depends(get_session)
) -> StockDataRead:
    """Get specific stock data by ID"""
    try:
        return StockController.get_stock_data_by_id(db, stock_data_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stock data not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.patch(
    "/{stock_data_id}",
    response_model=StockDataRead,
    dependencies=[Depends(authenticate)],
)
async def update_stock_data(
    stock_data_id: int,
    stock_data_update: StockDataUpdate,
    db: Session = Depends(get_session),
) -> StockDataRead:
    """Update existing stock data"""
    try:
        return await StockController.update_stock_data(
            db, stock_data_id, stock_data_update
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stock data not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete(
    "/{stock_data_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(authenticate)],
)
def delete_stock_data(stock_data_id: int, db: Session = Depends(get_session)):
    """Delete stock data"""
    try:
        StockController.delete_stock_data(db, stock_data_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stock data not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

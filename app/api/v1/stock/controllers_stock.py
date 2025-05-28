import logging
from datetime import datetime, timezone

from sqlmodel import Session, and_, desc, or_, select

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
from app.api.v1.stock.services.market_service import market_service
from app.api.v1.stock.services.vector_service import vector_service
from app.api.v1.stock.tables_stock import MarketCache, StockData, VectorEmbedding

log = logging.getLogger(__name__)


class StockController:
    """Controller for stock data operations with vector search capabilities"""

    @staticmethod
    def get_stock_data(
        db: Session,
        symbol: str | None = None,
        data_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StockDataRead]:
        """Get stock data with optional filtering"""
        try:
            stmt = select(StockData)

            # Apply filters
            conditions = []
            if symbol:
                conditions.append(StockData.symbol == symbol.upper())
            if data_type:
                conditions.append(StockData.data_type == data_type)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Order by most recent first
            stmt = stmt.order_by(desc(StockData.created_at))

            # Apply pagination
            stmt = stmt.offset(offset).limit(limit)

            stock_data_items = db.exec(stmt).all()

            # Convert to read models
            results = []
            for item in stock_data_items:
                stock_data_read = StockDataRead(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    symbol=item.symbol,
                    data_type=item.data_type,
                    content=item.content,
                    extra_metadata=item.extra_metadata,
                    embedding_id=item.embedding_id,
                    similarity_score=item.similarity_score,
                )
                results.append(stock_data_read)

            log.info(f"Retrieved {len(results)} stock data items")
            return results

        except Exception as e:
            log.error(f"Failed to get stock data: {e}")
            raise

    @staticmethod
    def get_stock_data_by_id(db: Session, stock_data_id: int) -> StockDataRead:
        """Get specific stock data by ID"""
        try:
            stmt = select(StockData).where(StockData.id == stock_data_id)
            stock_data = db.exec(stmt).first()

            if not stock_data:
                raise KeyError(f"Stock data with ID {stock_data_id} not found")

            return StockDataRead(
                id=stock_data.id,
                name=stock_data.name,
                description=stock_data.description,
                created_at=stock_data.created_at,
                updated_at=stock_data.updated_at,
                symbol=stock_data.symbol,
                data_type=stock_data.data_type,
                content=stock_data.content,
                extra_metadata=stock_data.extra_metadata,
                embedding_id=stock_data.embedding_id,
                similarity_score=stock_data.similarity_score,
            )

        except KeyError:
            raise
        except Exception as e:
            log.error(f"Failed to get stock data by ID {stock_data_id}: {e}")
            raise

    @staticmethod
    async def create_stock_data(
        db: Session, stock_data: StockDataCreate
    ) -> StockDataRead:
        """Create new stock data with vector embedding"""
        try:
            # Generate embedding for content
            embedding_id, embedding_vector = await vector_service.get_embedding(
                db, stock_data.content
            )

            # Create stock data entry
            db_stock_data = StockData(
                name=stock_data.name,
                description=stock_data.description,
                symbol=stock_data.symbol.upper(),
                data_type=stock_data.data_type,
                content=stock_data.content,
                extra_metadata=stock_data.extra_metadata,
                embedding_id=embedding_id,
                embedding_model=vector_service.model_name,
                data_timestamp=datetime.now(timezone.utc),
            )

            db.add(db_stock_data)
            db.commit()
            db.refresh(db_stock_data)

            log.info(
                f"Created stock data for {stock_data.symbol}: {stock_data.data_type}"
            )

            return StockDataRead(
                id=db_stock_data.id,
                name=db_stock_data.name,
                description=db_stock_data.description,
                created_at=db_stock_data.created_at,
                updated_at=db_stock_data.updated_at,
                symbol=db_stock_data.symbol,
                data_type=db_stock_data.data_type,
                content=db_stock_data.content,
                extra_metadata=db_stock_data.extra_metadata,
                embedding_id=db_stock_data.embedding_id,
            )

        except Exception as e:
            log.error(f"Failed to create stock data: {e}")
            db.rollback()
            raise

    @staticmethod
    async def update_stock_data(
        db: Session, stock_data_id: int, stock_data_update: StockDataUpdate
    ) -> StockDataRead:
        """Update existing stock data"""
        try:
            stmt = select(StockData).where(StockData.id == stock_data_id)
            db_stock_data = db.exec(stmt).first()

            if not db_stock_data:
                raise KeyError(f"Stock data with ID {stock_data_id} not found")

            # Update fields
            update_data = stock_data_update.model_dump(exclude_unset=True)

            # If content is updated, regenerate embedding
            if "content" in update_data:
                embedding_id, embedding_vector = await vector_service.get_embedding(
                    db, update_data["content"], force_refresh=True
                )
                update_data["embedding_id"] = embedding_id
                update_data["embedding_model"] = vector_service.model_name

            # Apply updates
            for field, value in update_data.items():
                setattr(db_stock_data, field, value)

            db_stock_data.updated_at = datetime.now(timezone.utc)

            db.add(db_stock_data)
            db.commit()
            db.refresh(db_stock_data)

            log.info(f"Updated stock data ID {stock_data_id}")

            return StockDataRead(
                id=db_stock_data.id,
                name=db_stock_data.name,
                description=db_stock_data.description,
                created_at=db_stock_data.created_at,
                updated_at=db_stock_data.updated_at,
                symbol=db_stock_data.symbol,
                data_type=db_stock_data.data_type,
                content=db_stock_data.content,
                extra_metadata=db_stock_data.extra_metadata,
                embedding_id=db_stock_data.embedding_id,
            )

        except KeyError:
            raise
        except Exception as e:
            log.error(f"Failed to update stock data ID {stock_data_id}: {e}")
            db.rollback()
            raise

    @staticmethod
    def delete_stock_data(db: Session, stock_data_id: int):
        """Delete stock data"""
        try:
            stmt = select(StockData).where(StockData.id == stock_data_id)
            db_stock_data = db.exec(stmt).first()

            if not db_stock_data:
                raise KeyError(f"Stock data with ID {stock_data_id} not found")

            db.delete(db_stock_data)
            db.commit()

            log.info(f"Deleted stock data ID {stock_data_id}")

        except KeyError:
            raise
        except Exception as e:
            log.error(f"Failed to delete stock data ID {stock_data_id}: {e}")
            db.rollback()
            raise

    @staticmethod
    async def search_stock_data(
        db: Session, query: VectorSearchQuery
    ) -> list[VectorSearchResult]:
        """Perform vector similarity search on stock data"""
        try:
            results = await vector_service.search_similar_content(db, query)
            log.info(f"Vector search returned {len(results)} results")
            return results

        except Exception as e:
            log.error(f"Failed to perform vector search: {e}")
            raise

    @staticmethod
    async def get_stock_price(symbol: str) -> StockPrice | None:
        """Get current stock price"""
        try:
            return await market_service.get_stock_price(symbol)
        except Exception as e:
            log.error(f"Failed to get stock price for {symbol}: {e}")
            raise

    @staticmethod
    async def get_stock_news(
        symbol: str | None = None, limit: int = 20
    ) -> list[StockNews]:
        """Get stock news"""
        try:
            return await market_service.get_stock_news(symbol, limit)
        except Exception as e:
            log.error(f"Failed to get stock news: {e}")
            raise

    @staticmethod
    async def analyze_stock(db: Session, symbol: str) -> StockAnalysis:
        """Perform comprehensive stock analysis"""
        try:
            return await market_service.analyze_stock(symbol, db)
        except Exception as e:
            log.error(f"Failed to analyze stock {symbol}: {e}")
            raise

    @staticmethod
    async def get_market_summary(db: Session) -> MarketSummary:
        """Get market summary"""
        try:
            return await market_service.get_market_summary(db)
        except Exception as e:
            log.error(f"Failed to get market summary: {e}")
            raise

    @staticmethod
    async def ingest_news_data(db: Session, symbol: str | None = None) -> int:
        """Ingest news data and store with embeddings"""
        try:
            news_articles = await market_service.get_stock_news(symbol, limit=50)

            ingested_count = 0
            for article in news_articles:
                try:
                    # Create content for embedding
                    content = f"{article.title} {article.summary}"

                    # Generate embedding
                    embedding_id, embedding_vector = await vector_service.get_embedding(
                        db, content
                    )

                    # Create stock data entry
                    stock_data = StockData(
                        name=f"News: {article.title[:50]}...",
                        description=f"News article from {article.source}",
                        symbol=article.symbols[0] if article.symbols else "GENERAL",
                        data_type="news",
                        content=content,
                        extra_metadata={
                            "title": article.title,
                            "url": article.url,
                            "source": article.source,
                            "symbols": article.symbols,
                            "sentiment_score": article.sentiment_score,
                            "relevance_score": article.relevance_score,
                        },
                        embedding_id=embedding_id,
                        embedding_model=vector_service.model_name,
                        sentiment_score=article.sentiment_score,
                        relevance_score=article.relevance_score,
                        data_timestamp=article.published_at,
                    )

                    db.add(stock_data)
                    ingested_count += 1

                except Exception as e:
                    log.warning(f"Failed to ingest news article: {e}")
                    continue

            db.commit()
            log.info(f"Ingested {ingested_count} news articles")
            return ingested_count

        except Exception as e:
            log.error(f"Failed to ingest news data: {e}")
            db.rollback()
            raise

    @staticmethod
    async def get_cache_stats(db: Session) -> CacheStats:
        """Get cache performance statistics"""
        try:
            stats = await vector_service.get_cache_stats(db)

            # Calculate hit rate
            total_requests = stats.get("search_cache_hits", 0) + stats.get(
                "embedding_total_usage", 0
            )
            hit_rate = (
                stats.get("search_cache_hits", 0) / max(total_requests, 1)
            ) * 100

            return CacheStats(
                cache_hits=stats.get("search_cache_hits", 0),
                cache_misses=max(0, total_requests - stats.get("search_cache_hits", 0)),
                cache_size=stats.get("search_cache_entries", 0)
                + stats.get("embedding_cache_entries", 0),
                hit_rate=hit_rate,
                last_updated=datetime.now(timezone.utc),
            )

        except Exception as e:
            log.error(f"Failed to get cache stats: {e}")
            raise

    @staticmethod
    async def cleanup_cache(db: Session):
        """Clean up expired cache entries"""
        try:
            await vector_service.cleanup_expired_cache(db)
            log.info("Cache cleanup completed")
        except Exception as e:
            log.error(f"Failed to cleanup cache: {e}")
            raise

    @staticmethod
    def get_trending_symbols(db: Session, limit: int = 10) -> list[dict]:
        """Get trending stock symbols based on data volume"""
        try:
            # Query to get symbols with most recent activity
            from sqlalchemy import func, text

            stmt = text(
                """
                SELECT symbol, 
                       COUNT(*) as activity_count,
                       AVG(sentiment_score) as avg_sentiment,
                       MAX(data_timestamp) as latest_activity
                FROM stock_data 
                WHERE data_timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY symbol 
                ORDER BY activity_count DESC, latest_activity DESC
                LIMIT :limit
            """
            )

            result = db.exec(stmt, {"limit": limit})

            trending = []
            for row in result:
                trending.append(
                    {
                        "symbol": row.symbol,
                        "activity_count": row.activity_count,
                        "avg_sentiment": (
                            float(row.avg_sentiment) if row.avg_sentiment else 0.0
                        ),
                        "latest_activity": row.latest_activity,
                    }
                )

            log.info(f"Retrieved {len(trending)} trending symbols")
            return trending

        except Exception as e:
            log.error(f"Failed to get trending symbols: {e}")
            # Fallback to simple query
            stmt = (
                select(StockData.symbol, func.count(StockData.id).label("count"))
                .group_by(StockData.symbol)
                .order_by(desc("count"))
                .limit(limit)
            )

            result = db.exec(stmt).all()
            return [
                {"symbol": row.symbol, "activity_count": row.count} for row in result
            ]

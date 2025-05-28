import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import func
from sqlmodel import Session, and_, or_, select

from app.api.v1.stock.models_stock import VectorSearchQuery, VectorSearchResult
from app.api.v1.stock.tables_stock import MarketCache, StockData, VectorEmbedding

log = logging.getLogger(__name__)


class VectorSearchService:
    """High-performance vector search service with intelligent caching"""

    def __init__(self):
        self.model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = None
        self.cache_ttl_hours = int(os.getenv("CACHE_TTL_HOURS", "24"))
        self.similarity_cache = {}
        self.embedding_cache = {}

    def _get_model(self) -> SentenceTransformer:
        """Lazy load the embedding model"""
        if self.model is None:
            log.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            log.info("Embedding model loaded successfully")
        return self.model

    def _generate_cache_key(self, content: str, model_name: str) -> str:
        """Generate a deterministic cache key for content"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return f"embedding:{model_name}:{content_hash[:16]}"

    def _generate_search_cache_key(self, query: VectorSearchQuery) -> str:
        """Generate cache key for search queries"""
        query_dict = {
            "query": query.query,
            "symbols": sorted(query.symbols) if query.symbols else None,
            "limit": query.limit,
            "threshold": query.similarity_threshold,
            "include_news": query.include_news,
            "include_analysis": query.include_analysis,
            "date_from": query.date_from.isoformat() if query.date_from else None,
            "date_to": query.date_to.isoformat() if query.date_to else None,
        }
        query_str = json.dumps(query_dict, sort_keys=True)
        query_hash = hashlib.sha256(query_str.encode()).hexdigest()
        return f"search:{query_hash[:16]}"

    async def get_embedding(
        self, db: Session, content: str, force_refresh: bool = False
    ) -> tuple[str, list[float]]:
        """Get or generate embedding for content with caching"""
        cache_key = self._generate_cache_key(content, self.model_name)

        # Check memory cache first
        if not force_refresh and cache_key in self.embedding_cache:
            log.debug(f"Embedding cache hit (memory): {cache_key}")
            return cache_key, self.embedding_cache[cache_key]

        # Check database cache
        if not force_refresh:
            stmt = select(VectorEmbedding).where(
                VectorEmbedding.embedding_id == cache_key
            )
            cached_embedding = db.exec(stmt).first()

            if cached_embedding:
                log.debug(f"Embedding cache hit (database): {cache_key}")
                # Update usage statistics
                cached_embedding.last_used = datetime.now(timezone.utc)
                cached_embedding.usage_count += 1
                db.add(cached_embedding)
                db.commit()

                # Store in memory cache
                self.embedding_cache[cache_key] = cached_embedding.embedding_vector
                return cache_key, cached_embedding.embedding_vector

        # Generate new embedding
        log.debug(f"Generating new embedding: {cache_key}")
        model = self._get_model()
        embedding_vector = model.encode(content).tolist()

        # Store in database
        vector_embedding = VectorEmbedding(
            embedding_id=cache_key,
            embedding_vector=embedding_vector,
            model_name=self.model_name,
            dimension=len(embedding_vector),
            usage_count=1,
        )

        try:
            db.add(vector_embedding)
            db.commit()
            log.debug(f"Stored embedding in database: {cache_key}")
        except Exception as e:
            log.warning(f"Failed to store embedding in database: {e}")
            db.rollback()

        # Store in memory cache
        self.embedding_cache[cache_key] = embedding_vector

        return cache_key, embedding_vector

    async def search_similar_content(
        self, db: Session, query: VectorSearchQuery
    ) -> list[VectorSearchResult]:
        """Perform vector similarity search with intelligent caching"""

        # Check search cache first
        search_cache_key = self._generate_search_cache_key(query)
        cached_results = await self._get_cached_search_results(db, search_cache_key)

        if cached_results:
            log.debug(f"Search cache hit: {search_cache_key}")
            return cached_results

        # Generate query embedding
        query_embedding_id, query_vector = await self.get_embedding(db, query.query)

        # Build database query
        stmt = select(StockData).where(
            and_(
                StockData.embedding_id.isnot(None), self._build_filter_conditions(query)
            )
        )

        # Execute query
        stock_data_items = db.exec(stmt).all()

        if not stock_data_items:
            log.info("No stock data found for search query")
            return []

        # Get embeddings for comparison
        embedding_ids = [
            item.embedding_id for item in stock_data_items if item.embedding_id
        ]
        embeddings_stmt = select(VectorEmbedding).where(
            VectorEmbedding.embedding_id.in_(embedding_ids)
        )
        embeddings = {
            emb.embedding_id: emb.embedding_vector
            for emb in db.exec(embeddings_stmt).all()
        }

        # Calculate similarities
        results = []
        query_vector_np = np.array(query_vector).reshape(1, -1)

        for item in stock_data_items:
            if item.embedding_id not in embeddings:
                continue

            item_vector = np.array(embeddings[item.embedding_id]).reshape(1, -1)
            similarity = cosine_similarity(query_vector_np, item_vector)[0][0]

            if similarity >= query.similarity_threshold:
                result = VectorSearchResult(
                    content=item.content,
                    content_type=item.data_type,
                    symbol=item.symbol,
                    similarity_score=float(similarity),
                    extra_metadata=item.extra_metadata,
                    timestamp=item.data_timestamp or item.created_at,
                )
                results.append(result)

        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        results = results[: query.limit]

        # Cache the results
        await self._cache_search_results(db, search_cache_key, results)

        log.info(f"Vector search completed: {len(results)} results found")
        return results

    def _build_filter_conditions(self, query: VectorSearchQuery):
        """Build SQLAlchemy filter conditions based on query parameters"""
        conditions = []

        # Symbol filter
        if query.symbols:
            conditions.append(StockData.symbol.in_(query.symbols))

        # Content type filter
        content_types = []
        if query.include_news:
            content_types.append("news")
        if query.include_analysis:
            content_types.append("analysis")

        if content_types:
            conditions.append(StockData.data_type.in_(content_types))

        # Date filters
        if query.date_from:
            conditions.append(
                or_(
                    StockData.data_timestamp >= query.date_from,
                    and_(
                        StockData.data_timestamp.is_(None),
                        StockData.created_at >= query.date_from,
                    ),
                )
            )

        if query.date_to:
            conditions.append(
                or_(
                    StockData.data_timestamp <= query.date_to,
                    and_(
                        StockData.data_timestamp.is_(None),
                        StockData.created_at <= query.date_to,
                    ),
                )
            )

        return and_(*conditions) if conditions else True

    async def _get_cached_search_results(
        self, db: Session, cache_key: str
    ) -> list[VectorSearchResult] | None:
        """Retrieve cached search results"""
        try:
            stmt = select(MarketCache).where(
                and_(
                    MarketCache.cache_key == cache_key,
                    MarketCache.cache_type == "search",
                    MarketCache.expires_at > datetime.now(timezone.utc),
                )
            )
            cached_item = db.exec(stmt).first()

            if cached_item:
                # Update access statistics
                cached_item.hit_count += 1
                cached_item.last_accessed = datetime.now(timezone.utc)
                db.add(cached_item)
                db.commit()

                # Deserialize results
                results_data = cached_item.cache_value.get("results", [])
                return [VectorSearchResult(**result) for result in results_data]

        except Exception as e:
            log.warning(f"Failed to retrieve cached search results: {e}")

        return None

    async def _cache_search_results(
        self, db: Session, cache_key: str, results: list[VectorSearchResult]
    ):
        """Cache search results"""
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=self.cache_ttl_hours
            )

            # Serialize results with JSON mode to handle datetime objects
            results_data = [result.model_dump(mode="json") for result in results]

            cache_item = MarketCache(
                cache_key=cache_key,
                cache_value={"results": results_data},
                cache_type="search",
                expires_at=expires_at,
                hit_count=0,
            )

            # Use merge to handle potential duplicates
            db.merge(cache_item)
            db.commit()

            log.debug(f"Cached search results: {cache_key}")

        except Exception as e:
            log.warning(f"Failed to cache search results: {e}")
            db.rollback()

    async def cleanup_expired_cache(self, db: Session):
        """Clean up expired cache entries"""
        try:
            # Clean up expired search cache
            expired_search = select(MarketCache).where(
                MarketCache.expires_at < datetime.now(timezone.utc)
            )
            expired_items = db.exec(expired_search).all()

            for item in expired_items:
                db.delete(item)

            # Clean up old embeddings (keep those used in last 30 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            old_embeddings = select(VectorEmbedding).where(
                VectorEmbedding.last_used < cutoff_date
            )
            old_embedding_items = db.exec(old_embeddings).all()

            for embedding in old_embedding_items:
                # Remove from memory cache
                if embedding.embedding_id in self.embedding_cache:
                    del self.embedding_cache[embedding.embedding_id]
                db.delete(embedding)

            db.commit()

            log.info(
                f"Cleaned up {len(expired_items)} expired cache items and {len(old_embedding_items)} old embeddings"
            )

        except Exception as e:
            log.error(f"Failed to cleanup expired cache: {e}")
            db.rollback()

    async def get_cache_stats(self, db: Session) -> dict[str, Any]:
        """Get cache performance statistics"""
        try:
            # Search cache stats
            search_cache_count = db.exec(
                select(func.count(MarketCache.id)).where(
                    MarketCache.cache_type == "search"
                )
            ).first()

            search_cache_hits = (
                db.exec(
                    select(func.sum(MarketCache.hit_count)).where(
                        MarketCache.cache_type == "search"
                    )
                ).first()
                or 0
            )

            # Embedding cache stats
            embedding_count = db.exec(select(func.count(VectorEmbedding.id))).first()
            embedding_usage = (
                db.exec(select(func.sum(VectorEmbedding.usage_count))).first() or 0
            )

            # Memory cache stats
            memory_cache_size = len(self.embedding_cache)

            return {
                "search_cache_entries": search_cache_count,
                "search_cache_hits": search_cache_hits,
                "embedding_cache_entries": embedding_count,
                "embedding_total_usage": embedding_usage,
                "memory_cache_size": memory_cache_size,
                "cache_ttl_hours": self.cache_ttl_hours,
                "model_name": self.model_name,
            }

        except Exception as e:
            log.error(f"Failed to get cache stats: {e}")
            return {}


# Global instance
vector_service = VectorSearchService()

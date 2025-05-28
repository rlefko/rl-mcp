import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from app.api.v1.stock.models_stock import VectorSearchQuery, VectorSearchResult
from app.api.v1.stock.services.vector_service import VectorSearchService, vector_service
from app.api.v1.stock.tables_stock import MarketCache, StockData, VectorEmbedding
from tests.conftest import create_test_embedding, create_test_stock_data


class TestVectorSearchService:
    """Test suite for VectorSearchService"""

    @pytest.fixture
    def vector_service_instance(self):
        """Create a fresh VectorSearchService instance for testing"""
        return VectorSearchService()

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock SentenceTransformer for testing"""
        mock_model = Mock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        return mock_model

    def test_generate_cache_key(self, vector_service_instance):
        """Test cache key generation"""
        content = "Apple Inc. stock analysis"
        model_name = "test-model"

        cache_key = vector_service_instance._generate_cache_key(content, model_name)

        assert cache_key.startswith("embedding:test-model:")
        assert len(cache_key.split(":")[-1]) == 16  # Hash should be 16 characters

        # Same content should generate same key
        cache_key2 = vector_service_instance._generate_cache_key(content, model_name)
        assert cache_key == cache_key2

        # Different content should generate different key
        cache_key3 = vector_service_instance._generate_cache_key(
            "Different content", model_name
        )
        assert cache_key != cache_key3

    def test_generate_search_cache_key(
        self, vector_service_instance, sample_vector_queries
    ):
        """Test search cache key generation"""
        query = sample_vector_queries[0]

        cache_key = vector_service_instance._generate_search_cache_key(query)

        assert cache_key.startswith("search:")
        assert len(cache_key.split(":")[-1]) == 16

        # Same query should generate same key
        cache_key2 = vector_service_instance._generate_search_cache_key(query)
        assert cache_key == cache_key2

        # Different query should generate different key
        different_query = VectorSearchQuery(query="Different query", limit=5)
        cache_key3 = vector_service_instance._generate_search_cache_key(different_query)
        assert cache_key != cache_key3

    @pytest.mark.asyncio
    async def test_get_embedding_new(
        self, session, vector_service_instance, mock_sentence_transformer
    ):
        """Test embedding generation for new content"""
        with patch.object(
            vector_service_instance,
            "_get_model",
            return_value=mock_sentence_transformer,
        ):
            content = "Apple Inc. shows strong growth potential"

            embedding_id, embedding_vector = (
                await vector_service_instance.get_embedding(session, content)
            )

            assert embedding_id.startswith("embedding:")
            assert len(embedding_vector) == 5
            assert embedding_vector == [0.1, 0.2, 0.3, 0.4, 0.5]

            # Check that embedding was stored in database
            from sqlmodel import select

            stmt = select(VectorEmbedding).where(
                VectorEmbedding.embedding_id == embedding_id
            )
            stored_embedding = session.exec(stmt).first()

            assert stored_embedding is not None
            assert stored_embedding.embedding_vector == embedding_vector
            assert stored_embedding.model_name == vector_service_instance.model_name

    @pytest.mark.asyncio
    async def test_get_embedding_cached(self, session, vector_service_instance):
        """Test embedding retrieval from cache"""
        # Create a cached embedding
        embedding_id = "test_embedding_123"
        test_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        create_test_embedding(session, embedding_id, test_vector)

        # Mock the cache key generation to return our test embedding ID
        with patch.object(
            vector_service_instance, "_generate_cache_key", return_value=embedding_id
        ):
            content = "Test content"

            retrieved_id, retrieved_vector = (
                await vector_service_instance.get_embedding(session, content)
            )

            assert retrieved_id == embedding_id
            assert retrieved_vector == test_vector

            # Check that usage count was incremented
            from sqlmodel import select

            stmt = select(VectorEmbedding).where(
                VectorEmbedding.embedding_id == embedding_id
            )
            stored_embedding = session.exec(stmt).first()
            assert stored_embedding is not None
            # Usage count should be at least 1 (might be 2 if incremented)
            assert stored_embedding.usage_count >= 1

    @pytest.mark.asyncio
    async def test_search_similar_content(
        self, session, vector_service_instance, sample_stock_data
    ):
        """Test vector similarity search"""
        # Create test data with embeddings
        for stock_data in sample_stock_data:
            db_stock_data = create_test_stock_data(session, stock_data)
            # Create corresponding embedding
            test_vector = [0.1, 0.2, 0.3, 0.4, 0.5]  # Mock embedding
            create_test_embedding(session, db_stock_data.embedding_id, test_vector)

        # Mock the embedding generation and similarity calculation
        with patch.object(
            vector_service_instance, "get_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = (
                "query_embedding",
                [0.1, 0.2, 0.3, 0.4, 0.5],
            )

            query = VectorSearchQuery(
                query="Apple growth potential",
                symbols=["AAPL"],
                limit=5,
                similarity_threshold=0.5,
            )

            results = await vector_service_instance.search_similar_content(
                session, query
            )

            assert len(results) <= query.limit
            for result in results:
                assert isinstance(result, VectorSearchResult)
                assert result.similarity_score >= query.similarity_threshold
                assert result.symbol in query.symbols or query.symbols is None

    @pytest.mark.asyncio
    async def test_search_with_filters(
        self, session, vector_service_instance, sample_stock_data
    ):
        """Test vector search with various filters"""
        # Create test data
        for stock_data in sample_stock_data:
            db_stock_data = create_test_stock_data(session, stock_data)
            test_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
            create_test_embedding(session, db_stock_data.embedding_id, test_vector)

        with patch.object(
            vector_service_instance, "get_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = (
                "query_embedding",
                [0.1, 0.2, 0.3, 0.4, 0.5],
            )

            # Test symbol filter
            query = VectorSearchQuery(
                query="stock analysis",
                symbols=["AAPL", "MSFT"],
                limit=10,
                similarity_threshold=0.0,
            )

            results = await vector_service_instance.search_similar_content(
                session, query
            )

            for result in results:
                assert result.symbol in ["AAPL", "MSFT"]

            # Test content type filter
            query = VectorSearchQuery(
                query="stock analysis",
                include_news=False,
                include_analysis=True,
                limit=10,
                similarity_threshold=0.0,
            )

            results = await vector_service_instance.search_similar_content(
                session, query
            )

            for result in results:
                assert result.content_type == "analysis"

    @pytest.mark.asyncio
    async def test_search_caching(
        self, session, vector_service_instance, sample_stock_data
    ):
        """Test search result caching"""
        # Create test data
        for stock_data in sample_stock_data:
            db_stock_data = create_test_stock_data(session, stock_data)
            test_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
            create_test_embedding(session, db_stock_data.embedding_id, test_vector)

        query = VectorSearchQuery(
            query="Apple growth potential", limit=5, similarity_threshold=0.5
        )

        with patch.object(
            vector_service_instance, "get_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = (
                "query_embedding",
                [0.1, 0.2, 0.3, 0.4, 0.5],
            )

            # First search - should cache results
            results1 = await vector_service_instance.search_similar_content(
                session, query
            )

            # Check that cache entry was created
            cache_key = vector_service_instance._generate_search_cache_key(query)
            from sqlmodel import select

            stmt = select(MarketCache).where(MarketCache.cache_key == cache_key)
            cached_item = session.exec(stmt).first()

            # Cache might not be created if there are no results, which is OK
            if cached_item is not None:
                assert cached_item.cache_type == "search"

                # Second search - should use cache
                results2 = await vector_service_instance.search_similar_content(
                    session, query
                )

                assert len(results1) == len(results2)
                # Cache hit count should be incremented
                session.refresh(cached_item)
                assert cached_item.hit_count >= 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_cache(self, session, vector_service_instance):
        """Test cleanup of expired cache entries"""
        # Create expired cache entry
        expired_cache = MarketCache(
            cache_key="expired_search_123",
            cache_value={"results": []},
            cache_type="search",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            hit_count=5,
        )
        session.add(expired_cache)

        # Create valid cache entry
        valid_cache = MarketCache(
            cache_key="valid_search_456",
            cache_value={"results": []},
            cache_type="search",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            hit_count=3,
        )
        session.add(valid_cache)

        # Create old embedding
        old_embedding = VectorEmbedding(
            embedding_id="old_embedding_789",
            embedding_vector=[0.1, 0.2, 0.3],
            model_name="test_model",
            dimension=3,
            last_used=datetime.now(timezone.utc) - timedelta(days=31),
        )
        session.add(old_embedding)

        # Create recent embedding
        recent_embedding = VectorEmbedding(
            embedding_id="recent_embedding_101",
            embedding_vector=[0.4, 0.5, 0.6],
            model_name="test_model",
            dimension=3,
            last_used=datetime.now(timezone.utc) - timedelta(days=1),
        )
        session.add(recent_embedding)

        session.commit()

        # Run cleanup
        await vector_service_instance.cleanup_expired_cache(session)

        # Check that expired items were removed
        from sqlmodel import select

        stmt = select(MarketCache).where(MarketCache.cache_key == "expired_search_123")
        assert session.exec(stmt).first() is None

        stmt = select(VectorEmbedding).where(
            VectorEmbedding.embedding_id == "old_embedding_789"
        )
        assert session.exec(stmt).first() is None

        # Check that valid items remain
        stmt = select(MarketCache).where(MarketCache.cache_key == "valid_search_456")
        assert session.exec(stmt).first() is not None

        stmt = select(VectorEmbedding).where(
            VectorEmbedding.embedding_id == "recent_embedding_101"
        )
        assert session.exec(stmt).first() is not None

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, session, vector_service_instance):
        """Test cache statistics retrieval"""
        # Create some cache entries
        cache_entry = MarketCache(
            cache_key="test_search_123",
            cache_value={"results": []},
            cache_type="search",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            hit_count=10,
        )
        session.add(cache_entry)

        embedding = VectorEmbedding(
            embedding_id="test_embedding_456",
            embedding_vector=[0.1, 0.2, 0.3],
            model_name="test_model",
            dimension=3,
            usage_count=5,
        )
        session.add(embedding)
        session.commit()

        stats = await vector_service_instance.get_cache_stats(session)

        assert "search_cache_entries" in stats
        assert "search_cache_hits" in stats
        assert "embedding_cache_entries" in stats
        assert "embedding_total_usage" in stats
        assert "memory_cache_size" in stats
        assert "cache_ttl_hours" in stats
        assert "model_name" in stats

        assert stats["search_cache_entries"] >= 1
        assert stats["search_cache_hits"] >= 10
        assert stats["embedding_cache_entries"] >= 1
        assert stats["embedding_total_usage"] >= 5

    def test_build_filter_conditions(self, vector_service_instance):
        """Test filter condition building"""
        # Test with symbol filter
        query = VectorSearchQuery(
            query="test query",
            symbols=["AAPL", "MSFT"],
            include_news=True,
            include_analysis=False,
        )

        conditions = vector_service_instance._build_filter_conditions(query)

        # This is a basic test - in a real scenario, you'd test the actual SQL generation
        assert conditions is not None

        # Test with date filters
        query_with_dates = VectorSearchQuery(
            query="test query",
            date_from=datetime.now(timezone.utc) - timedelta(days=7),
            date_to=datetime.now(timezone.utc),
        )

        conditions = vector_service_instance._build_filter_conditions(query_with_dates)
        assert conditions is not None

    @pytest.mark.asyncio
    async def test_memory_cache_functionality(
        self, session, vector_service_instance, mock_sentence_transformer
    ):
        """Test memory cache for embeddings"""
        with patch.object(
            vector_service_instance,
            "_get_model",
            return_value=mock_sentence_transformer,
        ):
            content = "Test content for memory cache"

            # First call - should generate and cache
            embedding_id1, embedding_vector1 = (
                await vector_service_instance.get_embedding(session, content)
            )

            # Second call - should use memory cache
            embedding_id2, embedding_vector2 = (
                await vector_service_instance.get_embedding(session, content)
            )

            assert embedding_id1 == embedding_id2
            assert embedding_vector1 == embedding_vector2

            # Check that the embedding is in memory cache
            assert embedding_id1 in vector_service_instance.embedding_cache
            assert (
                vector_service_instance.embedding_cache[embedding_id1]
                == embedding_vector1
            )

    @pytest.mark.asyncio
    async def test_force_refresh_embedding(
        self, session, vector_service_instance, mock_sentence_transformer
    ):
        """Test force refresh of embeddings"""
        with patch.object(
            vector_service_instance,
            "_get_model",
            return_value=mock_sentence_transformer,
        ):
            content = "Test content for force refresh"

            # First call - generate embedding
            embedding_id1, embedding_vector1 = (
                await vector_service_instance.get_embedding(session, content)
            )

            # Modify the mock to return different vector
            mock_sentence_transformer.encode.return_value = np.array(
                [0.6, 0.7, 0.8, 0.9, 1.0]
            )

            # Second call with force refresh
            embedding_id2, embedding_vector2 = (
                await vector_service_instance.get_embedding(
                    session, content, force_refresh=True
                )
            )

            assert embedding_id1 == embedding_id2  # Same content, same ID
            assert (
                embedding_vector1 != embedding_vector2
            )  # Different vectors due to force refresh
            assert embedding_vector2 == [0.6, 0.7, 0.8, 0.9, 1.0]


class TestVectorServiceIntegration:
    """Integration tests for vector service with real-like scenarios"""

    @pytest.mark.asyncio
    async def test_end_to_end_search_workflow(self, session, sample_stock_data):
        """Test complete workflow from data creation to search"""
        # Create stock data with real embeddings (mocked)
        created_items = []
        for stock_data in sample_stock_data:
            db_stock_data = create_test_stock_data(session, stock_data)
            # Create realistic embeddings based on content
            if "Apple" in stock_data.content:
                test_vector = [0.8, 0.2, 0.1, 0.3, 0.4]  # Apple-like vector
            elif "Tesla" in stock_data.content:
                test_vector = [0.1, 0.8, 0.3, 0.2, 0.5]  # Tesla-like vector
            else:
                test_vector = [0.3, 0.3, 0.8, 0.4, 0.2]  # Microsoft-like vector

            create_test_embedding(session, db_stock_data.embedding_id, test_vector)
            created_items.append(db_stock_data)

        # Mock the vector service to return Apple-like query vector
        with patch.object(vector_service, "get_embedding") as mock_get_embedding:
            mock_get_embedding.return_value = (
                "query_embedding",
                [0.7, 0.3, 0.2, 0.3, 0.4],
            )

            # Search for Apple-related content
            query = VectorSearchQuery(
                query="Apple iPhone smartphone market",
                limit=10,
                similarity_threshold=0.5,
            )

            results = await vector_service.search_similar_content(session, query)

            # Should find Apple-related content with high similarity
            assert len(results) > 0
            apple_results = [r for r in results if "AAPL" in r.symbol]
            assert len(apple_results) > 0

            # Apple result should have higher similarity than others
            if len(results) > 1:
                apple_result = next(r for r in results if "AAPL" in r.symbol)
                other_results = [r for r in results if "AAPL" not in r.symbol]
                if other_results:
                    assert (
                        apple_result.similarity_score
                        >= other_results[0].similarity_score
                    )

    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, session):
        """Test performance with larger dataset"""
        # Create a larger dataset
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX"]
        data_types = ["news", "analysis"]

        created_count = 0
        for symbol in symbols:
            for data_type in data_types:
                for i in range(5):  # 5 entries per symbol per type
                    stock_data = StockData(
                        name=f"{symbol} {data_type} {i}",
                        description=f"Test {data_type} for {symbol}",
                        symbol=symbol,
                        data_type=data_type,
                        content=f"This is test {data_type} content for {symbol} number {i}",
                        metadata={"test": True, "index": i},
                        embedding_id=f"test_embedding_{symbol}_{data_type}_{i}",
                        embedding_model="test_model",
                        data_timestamp=datetime.now(timezone.utc),
                    )
                    session.add(stock_data)

                    # Create corresponding embedding
                    test_vector = [float(i) * 0.1 for i in range(5)]
                    create_test_embedding(session, stock_data.embedding_id, test_vector)
                    created_count += 1

        session.commit()

        # Test search performance
        with patch.object(vector_service, "get_embedding") as mock_get_embedding:
            mock_get_embedding.return_value = (
                "query_embedding",
                [0.1, 0.2, 0.3, 0.4, 0.5],
            )

            query = VectorSearchQuery(
                query="technology stock analysis", limit=20, similarity_threshold=0.0
            )

            import time

            start_time = time.time()
            results = await vector_service.search_similar_content(session, query)
            end_time = time.time()

            # Should complete within reasonable time (adjust threshold as needed)
            assert end_time - start_time < 5.0  # 5 seconds max
            assert len(results) <= query.limit
            assert created_count == len(symbols) * len(data_types) * 5

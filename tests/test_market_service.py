from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import feedparser
import pytest

from app.api.v1.stock.models_stock import (
    MarketSummary,
    StockAnalysis,
    StockNews,
    StockPrice,
)
from app.api.v1.stock.services.market_service import MarketDataService, market_service


class TestMarketDataService:
    """Test suite for MarketDataService"""

    @pytest.fixture
    def market_service_instance(self):
        """Create a fresh MarketDataService instance for testing"""
        return MarketDataService()

    @pytest.mark.asyncio
    async def test_analyze_sentiment_positive(self, market_service_instance):
        """Test sentiment analysis for positive text"""
        positive_text = (
            "Great earnings, strong growth, excellent performance, bullish outlook"
        )

        sentiment = await market_service_instance._analyze_sentiment(positive_text)

        assert sentiment > 0
        assert -1.0 <= sentiment <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_sentiment_negative(self, market_service_instance):
        """Test sentiment analysis for negative text"""
        negative_text = (
            "Bad earnings, terrible performance, bearish outlook, stock crash"
        )

        sentiment = await market_service_instance._analyze_sentiment(negative_text)

        assert sentiment < 0
        assert -1.0 <= sentiment <= 1.0

    def test_extract_symbols(self, market_service_instance):
        """Test stock symbol extraction from text"""
        text = "AAPL and MSFT are performing well, but GOOGL is down. The market is volatile."

        symbols = market_service_instance._extract_symbols(text)

        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols
        # Common words should be filtered out
        assert "THE" not in symbols
        assert "AND" not in symbols
        assert "IS" not in symbols

    @pytest.mark.asyncio
    async def test_get_stock_price_success(self, market_service_instance):
        """Test successful stock price retrieval with yahooquery"""
        mock_price_data = {
            "AAPL": {
                "regularMarketPrice": 150.25,
                "regularMarketPreviousClose": 148.50,
                "regularMarketVolume": 50000000,
                "marketCap": 2500000000000,
                "trailingPE": 25.5,
            }
        }

        with patch("app.api.v1.stock.services.market_service.Ticker") as mock_ticker:
            mock_ticker.return_value.price = mock_price_data

            result = await market_service_instance.get_stock_price("AAPL")

            assert result is not None
            assert result.symbol == "AAPL"
            assert result.price == 150.25
            assert result.change == 1.75  # 150.25 - 148.50
            assert result.change_percent == pytest.approx(1.18, rel=1e-2)
            assert result.volume == 50000000

    @pytest.mark.asyncio
    async def test_get_stock_price_not_found(self, market_service_instance):
        """Test stock price retrieval for invalid symbol"""
        with patch("app.api.v1.stock.services.market_service.Ticker") as mock_ticker:
            mock_ticker.return_value.price = {}

            result = await market_service_instance.get_stock_price("INVALID")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_stock_news_success(self, market_service_instance):
        """Test successful news retrieval"""
        mock_feed_data = Mock()
        mock_feed_data.entries = [
            Mock(
                title="Apple Reports Strong Earnings",
                summary="Apple Inc. announced record quarterly earnings with AAPL stock rising.",
                link="https://example.com/news1",
                published_parsed=(2024, 1, 15, 10, 30, 0, 0, 15, 0),
                get=Mock(
                    side_effect=lambda key, default=None: {
                        "title": "Apple Reports Strong Earnings",
                        "summary": "Apple Inc. announced record quarterly earnings with AAPL stock rising.",
                        "link": "https://example.com/news1",
                    }.get(key, default)
                ),
            ),
            Mock(
                title="Tesla Innovation Update",
                summary="Tesla unveils new technology for TSLA vehicles.",
                link="https://example.com/news2",
                published_parsed=(2024, 1, 15, 9, 0, 0, 0, 15, 0),
                get=Mock(
                    side_effect=lambda key, default=None: {
                        "title": "Tesla Innovation Update",
                        "summary": "Tesla unveils new technology for TSLA vehicles.",
                        "link": "https://example.com/news2",
                    }.get(key, default)
                ),
            ),
        ]
        mock_feed_data.feed = Mock()
        mock_feed_data.feed.get.return_value = "TechNews"

        with patch("feedparser.parse", return_value=mock_feed_data), patch.object(
            market_service_instance, "_get_cached_data", return_value=None
        ), patch.object(market_service_instance, "_cache_data"):
            result = await market_service_instance.get_stock_news(limit=5)

            assert len(result) > 0
            assert all(isinstance(article, StockNews) for article in result)
            assert any("AAPL" in article.symbols for article in result)

    @pytest.mark.asyncio
    async def test_get_stock_news_with_symbol_filter(self, market_service_instance):
        """Test news retrieval with symbol filter"""
        mock_feed_data = Mock()
        mock_feed_data.entries = [
            Mock(
                title="Apple Reports Strong Earnings",
                summary="Apple Inc. announced record quarterly earnings with AAPL stock rising.",
                link="https://example.com/news1",
                published_parsed=(2024, 1, 15, 10, 30, 0, 0, 15, 0),
                get=Mock(
                    side_effect=lambda key, default=None: {
                        "title": "Apple Reports Strong Earnings",
                        "summary": "Apple Inc. announced record quarterly earnings with AAPL stock rising.",
                        "link": "https://example.com/news1",
                    }.get(key, default)
                ),
            ),
        ]
        mock_feed_data.feed = Mock()
        mock_feed_data.feed.get.return_value = "TechNews"

        with patch("feedparser.parse", return_value=mock_feed_data), patch.object(
            market_service_instance, "_get_cached_data", return_value=None
        ), patch.object(market_service_instance, "_cache_data"):
            result = await market_service_instance.get_stock_news("AAPL", limit=5)

            assert len(result) > 0
            assert all("AAPL" in article.symbols for article in result)

    @pytest.mark.asyncio
    async def test_analyze_stock_comprehensive(self, market_service_instance, session):
        """Test comprehensive stock analysis"""
        mock_price_data = StockPrice(
            symbol="AAPL",
            price=150.25,
            change=2.50,
            change_percent=1.69,
            volume=50000000,
            market_cap=2500000000000,
            pe_ratio=25.5,
            timestamp=datetime.now(timezone.utc),
        )

        mock_news = [
            StockNews(
                title="Apple Strong Performance",
                summary="Apple shows excellent growth",
                url="https://example.com",
                source="TechNews",
                published_at=datetime.now(timezone.utc),
                symbols=["AAPL"],
                sentiment_score=0.8,
                relevance_score=0.9,
            )
        ]

        with patch.object(
            market_service_instance, "get_stock_price", return_value=mock_price_data
        ), patch.object(
            market_service_instance, "get_stock_news", return_value=mock_news
        ), patch.object(
            market_service_instance, "_store_analysis"
        ) as mock_store:
            result = await market_service_instance.analyze_stock("AAPL", session)

            assert isinstance(result, StockAnalysis)
            assert result.symbol == "AAPL"
            assert result.recommendation in ["BUY", "HOLD", "SELL"]
            assert 0.0 <= result.confidence_score <= 1.0
            assert result.risk_level in ["LOW", "MEDIUM", "HIGH"]
            mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_market_summary(self, market_service_instance, session):
        """Test market summary generation"""
        mock_prices = {
            "AAPL": StockPrice(
                symbol="AAPL",
                price=150.25,
                change=5.50,
                change_percent=3.8,
                volume=50000000,
                timestamp=datetime.now(timezone.utc),
            ),
            "GOOGL": StockPrice(
                symbol="GOOGL",
                price=2800.75,
                change=-25.25,
                change_percent=-0.89,
                volume=15000000,
                timestamp=datetime.now(timezone.utc),
            ),
            "MSFT": StockPrice(
                symbol="MSFT",
                price=350.50,
                change=8.25,
                change_percent=2.41,
                volume=30000000,
                timestamp=datetime.now(timezone.utc),
            ),
        }

        def mock_get_price(symbol):
            return mock_prices.get(symbol)

        mock_news = [
            StockNews(
                title="Market Update",
                summary="Market shows mixed signals",
                url="https://example.com",
                source="MarketNews",
                published_at=datetime.now(timezone.utc),
                symbols=["AAPL", "GOOGL"],
                sentiment_score=0.2,
                relevance_score=0.7,
            )
        ]

        with patch.object(
            market_service_instance, "get_stock_price", side_effect=mock_get_price
        ), patch.object(
            market_service_instance, "get_stock_news", return_value=mock_news
        ), patch.object(
            market_service_instance, "_get_cached_data", return_value=None
        ), patch.object(
            market_service_instance, "_cache_data"
        ):
            result = await market_service_instance.get_market_summary(session)

            assert isinstance(result, MarketSummary)
            assert result.total_symbols > 0
            assert len(result.top_gainers) <= 3
            assert len(result.top_losers) <= 3
            assert -1.0 <= result.market_sentiment <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_relevance(self, market_service_instance):
        """Test relevance calculation for news articles"""
        # Test exact symbol match
        relevance = await market_service_instance._calculate_relevance(
            "AAPL stock rises", "Apple stock performance", "AAPL"
        )
        assert relevance == 1.0

        # Test company name match
        relevance = await market_service_instance._calculate_relevance(
            "Apple reports earnings", "Apple Inc. quarterly results", "AAPL"
        )
        assert relevance == 0.8

        # Test no match
        relevance = await market_service_instance._calculate_relevance(
            "Tesla news", "Tesla updates", "AAPL"
        )
        assert relevance == 0.3

    @pytest.mark.asyncio
    async def test_generate_recommendation(self, market_service_instance):
        """Test recommendation generation logic"""
        # Test BUY recommendation
        price_data = StockPrice(
            symbol="AAPL",
            price=150.0,
            change=5.0,
            change_percent=3.5,
            pe_ratio=18.0,
            volume=1000000,
            timestamp=datetime.now(timezone.utc),
        )
        recommendation = await market_service_instance._generate_recommendation(
            price_data, 0.5
        )
        assert recommendation == "BUY"

        # Test SELL recommendation
        price_data = StockPrice(
            symbol="AAPL",
            price=150.0,
            change=-8.0,
            change_percent=-5.0,
            pe_ratio=35.0,
            volume=1000000,
            timestamp=datetime.now(timezone.utc),
        )
        recommendation = await market_service_instance._generate_recommendation(
            price_data, -0.5
        )
        assert recommendation == "SELL"

    @pytest.mark.asyncio
    async def test_assess_risk(self, market_service_instance):
        """Test risk assessment logic"""
        # Test HIGH risk
        price_data = StockPrice(
            symbol="AAPL",
            price=150.0,
            change=20.0,
            change_percent=15.0,
            pe_ratio=50.0,
            volume=1000000,
            timestamp=datetime.now(timezone.utc),
        )
        risk = await market_service_instance._assess_risk(price_data, -0.5)
        assert risk == "HIGH"

        # Test LOW risk
        price_data = StockPrice(
            symbol="AAPL",
            price=150.0,
            change=1.0,
            change_percent=0.7,
            pe_ratio=20.0,
            volume=1000000,
            timestamp=datetime.now(timezone.utc),
        )
        risk = await market_service_instance._assess_risk(price_data, 0.2)
        assert risk == "LOW"

    @pytest.mark.asyncio
    async def test_caching_functionality(self, market_service_instance):
        """Test that caching works properly"""
        cache_key = "test_price_AAPL"

        # Mock the cache methods
        with patch.object(
            market_service_instance, "_get_cached_data", return_value=None
        ) as mock_get_cache, patch.object(
            market_service_instance, "_cache_data"
        ) as mock_cache_data, patch(
            "app.api.v1.stock.services.market_service.Ticker"
        ) as mock_ticker:

            mock_price_data = {
                "AAPL": {
                    "regularMarketPrice": 150.25,
                    "regularMarketPreviousClose": 148.50,
                    "regularMarketVolume": 50000000,
                }
            }
            mock_ticker.return_value.price = mock_price_data

            result = await market_service_instance.get_stock_price(
                "AAPL", use_cache=True
            )

            # Verify cache was checked and data was cached
            mock_get_cache.assert_called_once()
            mock_cache_data.assert_called_once()
            assert result is not None

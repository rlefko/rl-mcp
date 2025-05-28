import asyncio
import os
from datetime import datetime, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.api.v1.stock.models_stock import StockDataCreate, VectorSearchQuery
from app.api.v1.stock.tables_stock import MarketCache, StockData, VectorEmbedding
from app.databases.database import get_session
from app.main import app


# Set test environment
@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables"""
    os.environ["ENV"] = "test"
    yield
    # Clean up after test
    if "ENV" in os.environ:
        del os.environ["ENV"]


# Test database setup
@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with database session override"""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing"""
    return [
        StockDataCreate(
            name="Apple Stock Analysis",
            description="Comprehensive analysis of Apple Inc.",
            symbol="AAPL",
            data_type="analysis",
            content="Apple Inc. shows strong growth potential with innovative products and solid financials. The company continues to dominate the smartphone market.",
            extra_metadata={"analyst": "test", "confidence": 0.85},
        ),
        StockDataCreate(
            name="Tesla News Update",
            description="Latest news about Tesla",
            symbol="TSLA",
            data_type="news",
            content="Tesla announces new battery technology that could revolutionize electric vehicles. The stock price surged on the news.",
            extra_metadata={"source": "TechNews", "sentiment": 0.7},
        ),
        StockDataCreate(
            name="Microsoft Earnings",
            description="Microsoft quarterly earnings report",
            symbol="MSFT",
            data_type="analysis",
            content="Microsoft reported strong quarterly earnings driven by cloud services growth. Azure revenue increased by 30% year-over-year.",
            extra_metadata={"quarter": "Q4", "revenue_growth": 0.3},
        ),
    ]


@pytest.fixture
def sample_vector_queries():
    """Sample vector search queries for testing"""
    return [
        VectorSearchQuery(
            query="Apple iPhone sales growth",
            symbols=["AAPL"],
            limit=5,
            similarity_threshold=0.5,
            include_news=True,
            include_analysis=True,
        ),
        VectorSearchQuery(
            query="electric vehicle battery technology",
            limit=10,
            similarity_threshold=0.6,
            include_news=True,
            include_analysis=False,
        ),
        VectorSearchQuery(
            query="cloud computing revenue growth",
            symbols=["MSFT", "AMZN", "GOOGL"],
            limit=3,
            similarity_threshold=0.7,
        ),
    ]


@pytest.fixture
def mock_stock_price_data():
    """Mock stock price data for testing"""
    return {
        "AAPL": {
            "symbol": "AAPL",
            "price": 150.25,
            "change": 2.50,
            "change_percent": 1.69,
            "volume": 50000000,
            "market_cap": 2500000000000,
            "pe_ratio": 25.5,
            "timestamp": datetime.now(timezone.utc),
        },
        "TSLA": {
            "symbol": "TSLA",
            "price": 800.75,
            "change": -15.25,
            "change_percent": -1.87,
            "volume": 25000000,
            "market_cap": 800000000000,
            "pe_ratio": 45.2,
            "timestamp": datetime.now(timezone.utc),
        },
    }


@pytest.fixture
def mock_news_data():
    """Mock news data for testing"""
    return [
        {
            "title": "Apple Reports Record iPhone Sales",
            "summary": "Apple Inc. announced record iPhone sales for the quarter, driven by strong demand for the latest models.",
            "url": "https://example.com/apple-news",
            "source": "TechNews",
            "published_at": datetime.now(timezone.utc),
            "symbols": ["AAPL"],
            "sentiment_score": 0.8,
            "relevance_score": 0.9,
        },
        {
            "title": "Tesla Unveils New Battery Technology",
            "summary": "Tesla has unveiled revolutionary battery technology that promises longer range and faster charging.",
            "url": "https://example.com/tesla-news",
            "source": "AutoNews",
            "published_at": datetime.now(timezone.utc),
            "symbols": ["TSLA"],
            "sentiment_score": 0.7,
            "relevance_score": 0.85,
        },
    ]


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock authentication for testing
@pytest.fixture(autouse=True)
def mock_auth():
    """Mock authentication for all tests"""
    from app.api.auth import authenticate
    from app.main import app

    def get_mock_auth():
        return True

    # Clear any existing overrides first
    app.dependency_overrides.clear()
    app.dependency_overrides[authenticate] = get_mock_auth
    yield
    app.dependency_overrides.clear()


# Helper functions for tests
def create_test_stock_data(session: Session, stock_data: StockDataCreate) -> StockData:
    """Helper function to create test stock data in database"""
    db_stock_data = StockData(
        name=stock_data.name,
        description=stock_data.description,
        symbol=stock_data.symbol,
        data_type=stock_data.data_type,
        content=stock_data.content,
        extra_metadata=stock_data.extra_metadata,  # Use extra_metadata instead of metadata
        embedding_id=f"test_embedding_{stock_data.symbol}",
        embedding_model="test_model",
        data_timestamp=datetime.now(timezone.utc),
    )
    session.add(db_stock_data)
    session.commit()
    session.refresh(db_stock_data)
    return db_stock_data


def create_test_embedding(
    session: Session, embedding_id: str, vector: list
) -> VectorEmbedding:
    """Helper function to create test vector embedding"""
    embedding = VectorEmbedding(
        embedding_id=embedding_id,
        embedding_vector=vector,
        model_name="test_model",
        dimension=len(vector),
    )
    session.add(embedding)
    session.commit()
    session.refresh(embedding)
    return embedding

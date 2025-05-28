from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.api.v1.base.tables import BaseMCPTable


class StockData(BaseMCPTable, table=True):
    """Stock data table with vector embedding support"""

    __tablename__ = "stock_data"

    # Core stock data fields
    symbol: str = Field(index=True)
    data_type: str = Field(index=True)
    content: str
    extra_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Vector embedding fields
    embedding_id: str | None = Field(default=None, index=True)
    embedding_model: str | None = Field(default=None)

    # Performance and caching fields
    similarity_score: float | None = Field(default=None)
    cache_key: str | None = Field(default=None, index=True)

    # Stock-specific fields
    price: float | None = Field(default=None)
    volume: int | None = Field(default=None)
    sentiment_score: float | None = Field(default=None)
    relevance_score: float | None = Field(default=None)

    # Timestamp fields for data freshness
    data_timestamp: datetime | None = Field(default=None)
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VectorEmbedding(SQLModel, table=True):
    """Separate table for storing vector embeddings"""

    __tablename__ = "vector_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    embedding_id: str = Field(unique=True, index=True)
    embedding_vector: list[float] = Field(sa_column=Column(JSON))
    model_name: str
    dimension: int

    # Metadata for embedding management
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    usage_count: int = Field(default=0)


class MarketCache(SQLModel, table=True):
    """Cache table for market data and computed results"""

    __tablename__ = "market_cache"

    id: int | None = Field(default=None, primary_key=True)
    cache_key: str = Field(unique=True, index=True)
    cache_value: dict = Field(sa_column=Column(JSON))
    cache_type: str = Field(index=True)

    # Cache management fields
    expires_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hit_count: int = Field(default=0)
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

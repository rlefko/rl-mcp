from datetime import datetime

from pydantic import BaseModel, Field

from app.api.v1.base.models import BaseMCP, BaseMCPCreate, BaseMCPUpdate


class StockPrice(BaseModel):
    """Stock price data model"""

    symbol: str = Field(..., description="Stock ticker symbol")
    price: float = Field(..., description="Current stock price")
    change: float = Field(..., description="Price change")
    change_percent: float = Field(..., description="Percentage change")
    volume: int = Field(..., description="Trading volume")
    market_cap: float | None = Field(None, description="Market capitalization")
    pe_ratio: float | None = Field(None, description="Price-to-earnings ratio")
    timestamp: datetime = Field(..., description="Data timestamp")


class StockNews(BaseModel):
    """Stock news article model"""

    title: str = Field(..., description="News article title")
    summary: str = Field(..., description="Article summary")
    url: str = Field(..., description="Article URL")
    source: str = Field(..., description="News source")
    published_at: datetime = Field(..., description="Publication timestamp")
    symbols: list[str] = Field(
        default_factory=list, description="Related stock symbols"
    )
    sentiment_score: float | None = Field(
        None, description="Sentiment analysis score (-1 to 1)"
    )
    relevance_score: float | None = Field(None, description="Relevance score (0 to 1)")


class StockAnalysis(BaseModel):
    """Stock analysis and insights model"""

    symbol: str = Field(..., description="Stock ticker symbol")
    analysis_type: str = Field(
        ..., description="Type of analysis (technical, fundamental, news)"
    )
    insights: str = Field(..., description="Analysis insights")
    confidence_score: float = Field(..., description="Confidence in analysis (0 to 1)")
    recommendation: str = Field(..., description="Buy/Hold/Sell recommendation")
    target_price: float | None = Field(None, description="Target price prediction")
    risk_level: str = Field(..., description="Risk assessment (Low/Medium/High)")


class VectorSearchQuery(BaseModel):
    """Vector search query model"""

    query: str = Field(..., description="Search query text")
    symbols: list[str] | None = Field(
        None, description="Filter by specific stock symbols"
    )
    limit: int = Field(
        default=10, ge=1, le=100, description="Number of results to return"
    )
    similarity_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score"
    )
    include_news: bool = Field(
        default=True, description="Include news articles in search"
    )
    include_analysis: bool = Field(
        default=True, description="Include analysis in search"
    )
    date_from: datetime | None = Field(
        None, description="Filter results from this date"
    )
    date_to: datetime | None = Field(None, description="Filter results to this date")


class VectorSearchResult(BaseModel):
    """Vector search result model"""

    content: str = Field(..., description="Matched content")
    content_type: str = Field(
        ..., description="Type of content (news, analysis, price)"
    )
    symbol: str | None = Field(None, description="Related stock symbol")
    similarity_score: float = Field(..., description="Similarity score (0 to 1)")
    extra_metadata: dict = Field(
        default_factory=dict, description="Additional metadata"
    )
    timestamp: datetime = Field(..., description="Content timestamp")


class StockDataCreate(BaseMCPCreate):
    """Create stock data entry"""

    symbol: str = Field(..., description="Stock ticker symbol")
    data_type: str = Field(..., description="Type of data (price, news, analysis)")
    content: str = Field(..., description="Raw content data")
    extra_metadata: dict = Field(
        default_factory=dict, description="Additional metadata"
    )
    embedding: list[float] | None = Field(None, description="Vector embedding")


class StockDataUpdate(BaseMCPUpdate):
    """Update stock data entry"""

    symbol: str | None = Field(None, description="Stock ticker symbol")
    data_type: str | None = Field(None, description="Type of data")
    content: str | None = Field(None, description="Raw content data")
    extra_metadata: dict | None = Field(None, description="Additional metadata")
    embedding: list[float] | None = Field(None, description="Vector embedding")


class StockDataRead(BaseMCP):
    """Read stock data entry"""

    symbol: str = Field(..., description="Stock ticker symbol")
    data_type: str = Field(..., description="Type of data")
    content: str = Field(..., description="Raw content data")
    extra_metadata: dict = Field(
        default_factory=dict, description="Additional metadata"
    )
    embedding_id: str | None = Field(None, description="Vector embedding identifier")
    similarity_score: float | None = Field(
        None, description="Similarity score for search results"
    )


class MarketSummary(BaseModel):
    """Market summary model"""

    date: datetime = Field(..., description="Summary date")
    total_symbols: int = Field(..., description="Total number of symbols tracked")
    top_gainers: list[StockPrice] = Field(..., description="Top gaining stocks")
    top_losers: list[StockPrice] = Field(..., description="Top losing stocks")
    market_sentiment: float = Field(
        ..., description="Overall market sentiment (-1 to 1)"
    )
    news_count: int = Field(..., description="Number of news articles processed")
    trending_topics: list[str] = Field(..., description="Trending topics in the market")


class CacheStats(BaseModel):
    """Cache statistics model"""

    cache_hits: int = Field(..., description="Number of cache hits")
    cache_misses: int = Field(..., description="Number of cache misses")
    cache_size: int = Field(..., description="Current cache size")
    hit_rate: float = Field(..., description="Cache hit rate percentage")
    last_updated: datetime = Field(..., description="Last cache update timestamp")

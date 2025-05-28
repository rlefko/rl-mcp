import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser
from bs4 import BeautifulSoup
from sqlmodel import Session, and_, select
from yahooquery import Ticker

from app.api.v1.stock.models_stock import (
    MarketSummary,
    StockAnalysis,
    StockNews,
    StockPrice,
)

from ..tables_stock import MarketCache, StockData
from .vector_service import vector_service

log = logging.getLogger(__name__)


class MarketDataService:
    """Comprehensive market data service with news aggregation and analysis"""

    def __init__(self):
        self.news_sources = [
            "https://feeds.finance.yahoo.com/rss/2.0/headline",
            "https://feeds.marketwatch.com/marketwatch/topstories/",
            "https://feeds.reuters.com/reuters/businessNews",
        ]
        self.cache_ttl_minutes = int(os.getenv("MARKET_CACHE_TTL_MINUTES", "15"))

    async def get_stock_price(
        self, symbol: str, use_cache: bool = True
    ) -> StockPrice | None:
        """Get current stock price with caching"""
        cache_key = f"price:{symbol}"

        if use_cache:
            cached_price = await self._get_cached_data(cache_key, "price")
            if cached_price:
                return StockPrice(**cached_price)

        try:
            ticker = Ticker(symbol)

            # Get current price data
            price_data = ticker.price
            if (
                symbol.upper() not in price_data
                or "regularMarketPrice" not in price_data[symbol.upper()]
            ):
                log.warning(f"No price data found for symbol: {symbol}")
                return None

            data = price_data[symbol.upper()]

            current_price = float(data.get("regularMarketPrice", 0))
            previous_close = float(
                data.get("regularMarketPreviousClose", current_price)
            )
            change = current_price - previous_close
            change_percent = (
                (change / previous_close) * 100 if previous_close != 0 else 0
            )

            stock_price = StockPrice(
                symbol=symbol.upper(),
                price=current_price,
                change=change,
                change_percent=change_percent,
                volume=int(data.get("regularMarketVolume", 0)),
                market_cap=data.get("marketCap"),
                pe_ratio=data.get("trailingPE"),
                timestamp=datetime.now(timezone.utc),
            )

            # Cache the result
            if use_cache:
                await self._cache_data(cache_key, "price", stock_price.model_dump())

            log.info(f"Retrieved price data for {symbol}: ${current_price:.2f}")
            return stock_price

        except Exception as e:
            log.error(f"Failed to get stock price for {symbol}: {e}")
            return None

    async def get_stock_news(
        self, symbol: str | None = None, limit: int = 20, use_cache: bool = True
    ) -> list[StockNews]:
        """Get stock news with sentiment analysis"""
        cache_key = f"news:{symbol or 'general'}:{limit}"

        if use_cache:
            cached_news = await self._get_cached_data(cache_key, "news")
            if cached_news:
                return [StockNews(**article) for article in cached_news]

        news_articles = []

        for source_url in self.news_sources:
            try:
                feed = feedparser.parse(source_url)

                for entry in feed.entries[:limit]:
                    # Extract and clean content
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))

                    # Clean HTML tags
                    summary = BeautifulSoup(summary, "html.parser").get_text()

                    # Extract symbols from content
                    symbols = self._extract_symbols(f"{title} {summary}")

                    # Filter by symbol if specified
                    if symbol and symbol.upper() not in symbols:
                        continue

                    # Parse publication date
                    published_at = datetime.now(timezone.utc)
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published_at = datetime(
                            *entry.published_parsed[:6], tzinfo=timezone.utc
                        )

                    # Calculate sentiment and relevance
                    sentiment_score = await self._analyze_sentiment(
                        f"{title} {summary}"
                    )
                    relevance_score = await self._calculate_relevance(
                        title, summary, symbol
                    )

                    news_article = StockNews(
                        title=title,
                        summary=summary[:500],  # Limit summary length
                        url=entry.get("link", ""),
                        source=feed.feed.get("title", "Unknown"),
                        published_at=published_at,
                        symbols=symbols,
                        sentiment_score=sentiment_score,
                        relevance_score=relevance_score,
                    )

                    news_articles.append(news_article)

            except Exception as e:
                log.warning(f"Failed to fetch news from {source_url}: {e}")
                continue

        # Sort by relevance and recency
        news_articles.sort(
            key=lambda x: (x.relevance_score or 0, x.published_at), reverse=True
        )
        news_articles = news_articles[:limit]

        # Cache the results
        if use_cache:
            await self._cache_data(
                cache_key, "news", [article.model_dump() for article in news_articles]
            )

        log.info(f"Retrieved {len(news_articles)} news articles")
        return news_articles

    async def analyze_stock(self, symbol: str, db: Session) -> StockAnalysis:
        """Perform comprehensive stock analysis"""
        try:
            # Get current price data
            price_data = await self.get_stock_price(symbol)
            if not price_data:
                raise ValueError(f"Could not retrieve price data for {symbol}")

            # Get recent news
            news_articles = await self.get_stock_news(symbol, limit=10)

            # Analyze news sentiment
            avg_sentiment = 0.0
            if news_articles:
                sentiments = [
                    article.sentiment_score
                    for article in news_articles
                    if article.sentiment_score
                ]
                avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

            # Generate analysis insights
            insights = await self._generate_analysis_insights(
                price_data, news_articles, avg_sentiment
            )

            # Determine recommendation
            recommendation = await self._generate_recommendation(
                price_data, avg_sentiment
            )

            # Calculate confidence and risk
            confidence_score = await self._calculate_confidence(
                price_data, news_articles
            )
            risk_level = await self._assess_risk(price_data, avg_sentiment)

            analysis = StockAnalysis(
                symbol=symbol.upper(),
                analysis_type="comprehensive",
                insights=insights,
                confidence_score=confidence_score,
                recommendation=recommendation,
                target_price=price_data.price
                * (1 + (avg_sentiment * 0.1)),  # Simple target calculation
                risk_level=risk_level,
            )

            # Store analysis in database with embedding
            await self._store_analysis(db, analysis)

            log.info(f"Generated analysis for {symbol}: {recommendation}")
            return analysis

        except Exception as e:
            log.error(f"Failed to analyze stock {symbol}: {e}")
            raise

    async def get_market_summary(self, db: Session) -> MarketSummary:
        """Generate comprehensive market summary"""
        cache_key = "market_summary"

        # Check cache first
        cached_summary = await self._get_cached_data(cache_key, "summary")
        if cached_summary:
            return MarketSummary(**cached_summary)

        try:
            # Get data for major indices/stocks
            major_symbols = [
                "AAPL",
                "GOOGL",
                "MSFT",
                "AMZN",
                "TSLA",
                "NVDA",
                "META",
                "NFLX",
            ]

            prices = []
            for symbol in major_symbols:
                price_data = await self.get_stock_price(symbol)
                if price_data:
                    prices.append(price_data)

            # Sort by performance
            prices.sort(key=lambda x: x.change_percent, reverse=True)

            # Get recent news
            news_articles = await self.get_stock_news(limit=50)

            # Calculate market sentiment
            sentiments = [
                article.sentiment_score
                for article in news_articles
                if article.sentiment_score
            ]
            market_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

            # Extract trending topics
            trending_topics = await self._extract_trending_topics(news_articles)

            summary = MarketSummary(
                date=datetime.now(timezone.utc),
                total_symbols=len(prices),
                top_gainers=prices[:3],
                top_losers=prices[-3:],
                market_sentiment=market_sentiment,
                news_count=len(news_articles),
                trending_topics=trending_topics,
            )

            # Cache the summary
            await self._cache_data(cache_key, "summary", summary.model_dump())

            return summary

        except Exception as e:
            log.error(f"Failed to generate market summary: {e}")
            raise

    def _extract_symbols(self, text: str) -> list[str]:
        """Extract stock symbols from text"""
        # Pattern to match stock symbols (1-5 uppercase letters)
        pattern = r"\b[A-Z]{1,5}\b"
        potential_symbols = re.findall(pattern, text)

        # Filter out common words that aren't stock symbols
        common_words = {
            "THE",
            "AND",
            "FOR",
            "ARE",
            "BUT",
            "NOT",
            "YOU",
            "ALL",
            "CAN",
            "HER",
            "WAS",
            "ONE",
            "OUR",
            "HAD",
            "BY",
            "UP",
            "DO",
            "NO",
            "IF",
            "TO",
            "MY",
            "IS",
            "AT",
            "AS",
            "WE",
            "ON",
            "BE",
            "OR",
            "AN",
            "WILL",
            "SO",
            "IT",
            "OF",
            "IN",
            "HE",
            "HAS",
            "GET",
            "NEW",
            "NOW",
            "OLD",
            "SEE",
            "HIM",
            "TWO",
            "HOW",
            "ITS",
            "WHO",
            "OIL",
            "USE",
            "MAN",
            "DAY",
            "TOO",
            "ANY",
            "MAY",
            "SAY",
            "SHE",
            "WAY",
            "OUT",
            "TOP",
            "SET",
            "PUT",
            "END",
            "WHY",
            "TRY",
            "GOD",
            "SIX",
            "DOG",
            "EAT",
            "AGO",
            "SIT",
            "FUN",
            "BAD",
            "YES",
            "YET",
            "ARM",
            "FAR",
            "OFF",
            "ILL",
            "OWN",
            "UNDER",
            "LAST",
        }

        symbols = [symbol for symbol in potential_symbols if symbol not in common_words]
        return list(set(symbols))  # Remove duplicates

    async def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text (simplified implementation)"""
        # This is a simplified sentiment analysis
        # In production, you'd use a proper sentiment analysis model
        positive_words = [
            "good",
            "great",
            "excellent",
            "positive",
            "up",
            "gain",
            "profit",
            "bull",
            "rise",
            "strong",
            "growth",
            "increase",
            "buy",
            "bullish",
        ]
        negative_words = [
            "bad",
            "terrible",
            "negative",
            "down",
            "loss",
            "bear",
            "fall",
            "weak",
            "decline",
            "decrease",
            "sell",
            "bearish",
            "crash",
            "drop",
        ]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        total_words = len(text.split())
        if total_words == 0:
            return 0.0

        sentiment = (positive_count - negative_count) / max(total_words, 1)
        return max(-1.0, min(1.0, sentiment * 10))  # Scale and clamp to [-1, 1]

    async def _calculate_relevance(
        self, title: str, summary: str, symbol: str | None
    ) -> float:
        """Calculate relevance score for news article"""
        if not symbol:
            return 0.5  # Default relevance for general news

        text = f"{title} {summary}".lower()
        symbol_lower = symbol.lower()

        # Check for exact symbol match
        if symbol_lower in text:
            return 1.0

        # Check for company name (simplified)
        company_names = {
            "aapl": "apple",
            "googl": "google",
            "msft": "microsoft",
            "amzn": "amazon",
            "tsla": "tesla",
            "nvda": "nvidia",
            "meta": "meta",
            "nflx": "netflix",
        }

        company_name = company_names.get(symbol_lower)
        if company_name and company_name in text:
            return 0.8

        return 0.3  # Low relevance if no direct match

    async def _generate_analysis_insights(
        self,
        price_data: StockPrice,
        news_articles: list[StockNews],
        avg_sentiment: float,
    ) -> str:
        """Generate analysis insights based on price and news data"""
        insights = []

        # Price analysis
        if price_data.change_percent > 5:
            insights.append(
                f"Strong upward momentum with {price_data.change_percent:.1f}% gain"
            )
        elif price_data.change_percent < -5:
            insights.append(
                f"Significant decline of {abs(price_data.change_percent):.1f}%"
            )
        else:
            insights.append(
                f"Moderate price movement of {price_data.change_percent:.1f}%"
            )

        # Volume analysis
        if price_data.volume > 1000000:
            insights.append("High trading volume indicates strong investor interest")

        # Sentiment analysis
        if avg_sentiment > 0.3:
            insights.append("Positive news sentiment suggests bullish outlook")
        elif avg_sentiment < -0.3:
            insights.append("Negative news sentiment indicates bearish sentiment")
        else:
            insights.append("Mixed news sentiment suggests uncertainty")

        # PE ratio analysis
        if price_data.pe_ratio:
            if price_data.pe_ratio > 25:
                insights.append(
                    "High P/E ratio suggests growth expectations or overvaluation"
                )
            elif price_data.pe_ratio < 15:
                insights.append(
                    "Low P/E ratio may indicate undervaluation or slow growth"
                )

        return ". ".join(insights)

    async def _generate_recommendation(
        self, price_data: StockPrice, avg_sentiment: float
    ) -> str:
        """Generate buy/hold/sell recommendation"""
        score = 0

        # Price momentum
        if price_data.change_percent > 2:
            score += 1
        elif price_data.change_percent < -2:
            score -= 1

        # Sentiment
        if avg_sentiment > 0.2:
            score += 1
        elif avg_sentiment < -0.2:
            score -= 1

        # PE ratio consideration
        if price_data.pe_ratio and price_data.pe_ratio < 20:
            score += 0.5
        elif price_data.pe_ratio and price_data.pe_ratio > 30:
            score -= 0.5

        if score >= 1.5:
            return "BUY"
        elif score <= -1.5:
            return "SELL"
        else:
            return "HOLD"

    async def _calculate_confidence(
        self, price_data: StockPrice, news_articles: list[StockNews]
    ) -> float:
        """Calculate confidence score for analysis"""
        confidence = 0.5  # Base confidence

        # More news articles increase confidence
        if len(news_articles) > 5:
            confidence += 0.2

        # Recent data increases confidence
        data_age = datetime.now(timezone.utc) - price_data.timestamp
        if data_age.total_seconds() < 3600:  # Less than 1 hour old
            confidence += 0.2

        # Volume indicates market interest
        if price_data.volume > 500000:
            confidence += 0.1

        return min(1.0, confidence)

    async def _assess_risk(self, price_data: StockPrice, avg_sentiment: float) -> str:
        """Assess risk level"""
        risk_score = 0

        # High volatility increases risk
        if abs(price_data.change_percent) > 10:
            risk_score += 2
        elif abs(price_data.change_percent) > 5:
            risk_score += 1

        # Negative sentiment increases risk
        if avg_sentiment < -0.3:
            risk_score += 1

        # High PE ratio increases risk
        if price_data.pe_ratio and price_data.pe_ratio > 40:
            risk_score += 1

        if risk_score >= 3:
            return "HIGH"
        elif risk_score >= 1:
            return "MEDIUM"
        else:
            return "LOW"

    async def _extract_trending_topics(
        self, news_articles: list[StockNews]
    ) -> list[str]:
        """Extract trending topics from news articles"""
        # Simple keyword extraction
        all_text = " ".join(
            [article.title + " " + article.summary for article in news_articles]
        )
        words = all_text.lower().split()

        # Filter out common words and short words
        stop_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
            "a",
            "an",
        }

        filtered_words = [
            word for word in words if len(word) > 3 and word not in stop_words
        ]

        # Count word frequency
        word_count = {}
        for word in filtered_words:
            word_count[word] = word_count.get(word, 0) + 1

        # Get top trending words
        trending = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10]
        return [word for word, count in trending if count > 2]

    async def _store_analysis(self, db: Session, analysis: StockAnalysis):
        """Store analysis in database with vector embedding"""
        try:
            content = f"{analysis.insights} Recommendation: {analysis.recommendation} Risk: {analysis.risk_level}"

            # Generate embedding
            embedding_id, embedding_vector = await vector_service.get_embedding(
                db, content
            )

            # Create stock data entry
            stock_data = StockData(
                name=f"Analysis for {analysis.symbol}",
                description=f"Comprehensive analysis of {analysis.symbol}",
                symbol=analysis.symbol,
                data_type="analysis",
                content=content,
                extra_metadata={
                    "analysis_type": analysis.analysis_type,
                    "confidence_score": analysis.confidence_score,
                    "recommendation": analysis.recommendation,
                    "target_price": analysis.target_price,
                    "risk_level": analysis.risk_level,
                },
                embedding_id=embedding_id,
                embedding_model=vector_service.model_name,
                data_timestamp=datetime.now(timezone.utc),
            )

            db.add(stock_data)
            db.commit()

            log.info(f"Stored analysis for {analysis.symbol} in database")

        except Exception as e:
            log.error(f"Failed to store analysis: {e}")
            db.rollback()

    async def _get_cached_data(self, cache_key: str, cache_type: str) -> Any | None:
        """Get data from cache"""
        try:
            # This would typically use a database session, but for now we'll use a simple approach
            # In a real implementation, you'd inject the database session
            from app.databases.database import get_session

            with next(get_session()) as db:
                stmt = select(MarketCache).where(
                    and_(
                        MarketCache.cache_key == cache_key,
                        MarketCache.cache_type == cache_type,
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

                    log.debug(f"Cache hit for {cache_key}")
                    return cached_item.cache_value

        except Exception as e:
            log.warning(f"Failed to retrieve cached data: {e}")

        return None

    async def _cache_data(self, cache_key: str, cache_type: str, data: Any):
        """Cache data"""
        try:
            from app.databases.database import get_session

            with next(get_session()) as db:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    minutes=self.cache_ttl_minutes
                )

                cache_item = MarketCache(
                    cache_key=cache_key,
                    cache_value=data,
                    cache_type=cache_type,
                    expires_at=expires_at,
                    hit_count=0,
                )

                # Use merge to handle potential duplicates
                db.merge(cache_item)
                db.commit()

                log.debug(f"Cached data for {cache_key}")

        except Exception as e:
            log.warning(f"Failed to cache data: {e}")


# Global instance
market_service = MarketDataService()

# 📰 News Intelligence & Market Analysis

> 🧠 **Harness the power of real-time financial news with AI-driven sentiment analysis**

Transform raw financial news into actionable intelligence with our comprehensive news and analysis capabilities. Our system aggregates content from multiple sources, applies advanced sentiment analysis, and delivers insights that help you stay ahead of market movements. 📈✨

## 🌟 What Makes Our News Intelligence Special?

### 📊 **AI-Powered Analysis**
- **🎯 Sentiment Scoring**: Advanced NLP models analyze sentiment (-1 to 1 scale)
- **📈 Relevance Ranking**: AI determines how relevant news is to specific stocks
- **🔍 Content Categorization**: Automatic classification of news types and topics
- **⚡ Real-time Processing**: News is analyzed and indexed as it arrives

### 🌐 **Multi-Source Aggregation**
- **📰 Diverse Sources**: Content from major financial news outlets
- **🔄 Continuous Updates**: Real-time news ingestion and processing
- **🎯 Symbol Mapping**: Intelligent association of news with relevant stocks
- **📅 Historical Archive**: Access to historical news and analysis data

## 🚀 Getting Started with News Intelligence

### 📡 **Basic News Endpoint**
```bash
GET /v1/stock/news
```

### 🎯 **Simple News Query**
```python
import requests

# Get latest news for Apple
response = requests.get(
    "http://localhost:8000/v1/stock/news?symbol=AAPL&limit=10",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

news_articles = response.json()
for article in news_articles:
    sentiment_emoji = "🟢" if article['sentiment_score'] > 0 else "🔴" if article['sentiment_score'] < 0 else "⚪"
    print(f"{sentiment_emoji} {article['title']}")
    print(f"📊 Sentiment: {article['sentiment_score']:.2f}")
    print(f"🎯 Relevance: {article['relevance_score']:.2f}")
    print(f"📅 Published: {article['published_at']}")
    print("---")
```

## 🎛️ News Query Parameters

### 🔧 **Available Filters**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `symbol` | string | Filter by stock symbol | "AAPL" |
| `limit` | integer | Max articles (1-100) | 20 |

### 📊 **Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Article headline |
| `summary` | string | Article summary/excerpt |
| `url` | string | Link to full article |
| `source` | string | News source (Reuters, Bloomberg, etc.) |
| `published_at` | datetime | Publication timestamp |
| `symbols` | array[string] | Related stock symbols |
| `sentiment_score` | float | Sentiment analysis (-1 to 1) |
| `relevance_score` | float | Relevance to symbol (0 to 1) |

## 🧠 AI-Powered Stock Analysis

### 📈 **Comprehensive Analysis Endpoint**
```bash
GET /v1/stock/analysis/{symbol}
```

### 🎯 **Analysis Example**
```python
# Get comprehensive analysis for Tesla
analysis = requests.get(
    "http://localhost:8000/v1/stock/analysis/TSLA",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
).json()

print(f"🏢 Symbol: {analysis['symbol']}")
print(f"📊 Analysis Type: {analysis['analysis_type']}")
print(f"🎯 Recommendation: {analysis['recommendation']}")
print(f"📈 Target Price: ${analysis['target_price']}")
print(f"🛡️ Risk Level: {analysis['risk_level']}")
print(f"🔍 Confidence: {analysis['confidence_score']:.1%}")
print(f"\n💡 Insights:\n{analysis['insights']}")
```

### 📊 **Analysis Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Stock ticker symbol |
| `analysis_type` | string | Type of analysis performed |
| `insights` | string | Detailed analysis insights |
| `confidence_score` | float | AI confidence (0 to 1) |
| `recommendation` | string | Buy/Hold/Sell recommendation |
| `target_price` | float | Predicted target price |
| `risk_level` | string | Risk assessment (Low/Medium/High) |

## 🎨 Advanced News Intelligence Use Cases

### 📊 **Sentiment Trend Analysis**

Track sentiment changes over time to identify market shifts.

```python
class SentimentTrendAnalyzer:
    def __init__(self, api_client):
        self.api = api_client
    
    async def analyze_sentiment_trend(self, symbol, days=30):
        """Analyze sentiment trends over time"""
        from datetime import datetime, timedelta
        
        # Get recent news
        news = await self.api.get_news(symbol=symbol, limit=100)
        
        # Group by date and calculate daily sentiment
        daily_sentiment = {}
        for article in news:
            date = article['published_at'][:10]  # YYYY-MM-DD
            if date not in daily_sentiment:
                daily_sentiment[date] = []
            daily_sentiment[date].append(article['sentiment_score'])
        
        # Calculate daily averages
        trend_data = []
        for date, scores in daily_sentiment.items():
            avg_sentiment = sum(scores) / len(scores)
            trend_data.append({
                "date": date,
                "avg_sentiment": avg_sentiment,
                "article_count": len(scores),
                "sentiment_category": self._categorize_sentiment(avg_sentiment)
            })
        
        return sorted(trend_data, key=lambda x: x['date'])
    
    def _categorize_sentiment(self, score):
        """Categorize sentiment score"""
        if score > 0.2:
            return "Positive"
        elif score < -0.2:
            return "Negative"
        else:
            return "Neutral"
```

### 🔍 **News Impact Analysis**

Correlate news sentiment with stock price movements.

```python
class NewsImpactAnalyzer:
    def __init__(self, api_client):
        self.api = api_client
    
    async def analyze_news_impact(self, symbol):
        """Analyze correlation between news and price movements"""
        # Get recent news and price data
        news = await self.api.get_news(symbol=symbol, limit=50)
        price_data = await self.api.get_price(symbol)
        
        impact_analysis = {
            "symbol": symbol,
            "current_price": price_data['price'],
            "price_change": price_data['change_percent'],
            "news_sentiment": self._calculate_weighted_sentiment(news),
            "high_impact_news": [],
            "sentiment_price_correlation": None
        }
        
        # Identify high-impact news
        for article in news:
            if (abs(article['sentiment_score']) > 0.5 and 
                article['relevance_score'] > 0.8):
                impact_analysis["high_impact_news"].append({
                    "title": article['title'],
                    "sentiment": article['sentiment_score'],
                    "relevance": article['relevance_score'],
                    "published": article['published_at']
                })
        
        return impact_analysis
    
    def _calculate_weighted_sentiment(self, news):
        """Calculate sentiment weighted by relevance"""
        if not news:
            return 0
        
        weighted_sum = sum(
            article['sentiment_score'] * article['relevance_score'] 
            for article in news
        )
        weight_sum = sum(article['relevance_score'] for article in news)
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0
```

### 🚨 **Breaking News Alerts**

Monitor for breaking news and significant market events.

```python
class BreakingNewsMonitor:
    def __init__(self, api_client):
        self.api = api_client
        self.alert_thresholds = {
            "high_sentiment": 0.8,
            "high_relevance": 0.9,
            "recent_hours": 2
        }
    
    async def monitor_breaking_news(self, watchlist):
        """Monitor for breaking news across watchlist"""
        alerts = []
        
        for symbol in watchlist:
            # Get very recent news
            recent_news = await self.api.get_news(symbol=symbol, limit=20)
            
            for article in recent_news:
                # Check if this is breaking/significant news
                if self._is_breaking_news(article):
                    alert = {
                        "symbol": symbol,
                        "type": "breaking_news",
                        "title": article['title'],
                        "sentiment": article['sentiment_score'],
                        "relevance": article['relevance_score'],
                        "urgency": self._calculate_urgency(article),
                        "published": article['published_at'],
                        "url": article['url']
                    }
                    alerts.append(alert)
        
        # Sort by urgency
        return sorted(alerts, key=lambda x: x['urgency'], reverse=True)
    
    def _is_breaking_news(self, article):
        """Determine if article qualifies as breaking news"""
        from datetime import datetime, timedelta
        
        # Check recency
        published = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
        cutoff = datetime.now(published.tzinfo) - timedelta(hours=self.alert_thresholds["recent_hours"])
        
        is_recent = published > cutoff
        is_high_impact = (
            abs(article['sentiment_score']) > self.alert_thresholds["high_sentiment"] or
            article['relevance_score'] > self.alert_thresholds["high_relevance"]
        )
        
        return is_recent and is_high_impact
    
    def _calculate_urgency(self, article):
        """Calculate urgency score for news"""
        sentiment_weight = abs(article['sentiment_score']) * 0.4
        relevance_weight = article['relevance_score'] * 0.6
        return sentiment_weight + relevance_weight
```

## 🔄 Data Ingestion & Processing

### 📥 **Background News Ingestion**

Our system continuously ingests news from multiple sources:

```bash
# Start background news ingestion for all symbols
POST /v1/stock/ingest/news

# Start ingestion for specific symbol
POST /v1/stock/ingest/news?symbol=AAPL
```

### ⚡ **Synchronous Ingestion**

For immediate results, use synchronous ingestion:

```bash
# Synchronous ingestion with immediate results
POST /v1/stock/ingest/news/sync?symbol=TSLA
```

### 🎯 **Custom Ingestion Example**

```python
class NewsIngestionManager:
    def __init__(self, api_client):
        self.api = api_client
    
    async def ingest_portfolio_news(self, portfolio_symbols):
        """Ingest news for entire portfolio"""
        ingestion_results = {}
        
        for symbol in portfolio_symbols:
            try:
                result = await self.api.ingest_news_sync(symbol=symbol)
                ingestion_results[symbol] = {
                    "status": "success",
                    "articles_processed": result.get('articles_processed', 0),
                    "message": result.get('message', '')
                }
            except Exception as e:
                ingestion_results[symbol] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return ingestion_results
    
    async def schedule_regular_ingestion(self, symbols, interval_hours=1):
        """Schedule regular news ingestion"""
        import asyncio
        
        while True:
            print(f"🔄 Starting news ingestion for {len(symbols)} symbols...")
            
            for symbol in symbols:
                try:
                    await self.api.ingest_news_background(symbol=symbol)
                    print(f"✅ Ingestion started for {symbol}")
                except Exception as e:
                    print(f"❌ Failed to start ingestion for {symbol}: {e}")
            
            # Wait for next cycle
            await asyncio.sleep(interval_hours * 3600)
```

## 📊 Sentiment Analysis Deep Dive

### 🧠 **Understanding Sentiment Scores**

Our sentiment analysis uses advanced NLP models to score content:

| Score Range | Interpretation | Emoji | Description |
|-------------|----------------|-------|-------------|
| 0.7 to 1.0 | Very Positive | 🟢🟢 | Strong positive sentiment |
| 0.3 to 0.7 | Positive | 🟢 | Moderately positive |
| -0.3 to 0.3 | Neutral | ⚪ | Balanced or neutral tone |
| -0.7 to -0.3 | Negative | 🔴 | Moderately negative |
| -1.0 to -0.7 | Very Negative | 🔴🔴 | Strong negative sentiment |

### 🎯 **Relevance Scoring**

Relevance scores indicate how closely news relates to specific stocks:

| Score Range | Relevance Level | Description |
|-------------|----------------|-------------|
| 0.9 to 1.0 | Highly Relevant | Directly about the company |
| 0.7 to 0.9 | Very Relevant | Significantly mentions the company |
| 0.5 to 0.7 | Moderately Relevant | Some mention or indirect impact |
| 0.3 to 0.5 | Somewhat Relevant | Tangentially related |
| 0.0 to 0.3 | Low Relevance | Minimal connection |

## 🎉 **Integration Examples**

### 📱 **Mobile App Integration**

```python
class MobileNewsService:
    def __init__(self, api_client):
        self.api = api_client
    
    async def get_personalized_feed(self, user_portfolio, user_interests):
        """Generate personalized news feed"""
        feed_items = []
        
        # Portfolio-related news
        for symbol in user_portfolio:
            news = await self.api.get_news(symbol=symbol, limit=5)
            for article in news:
                feed_items.append({
                    "type": "portfolio_news",
                    "symbol": symbol,
                    "title": article['title'],
                    "summary": article['summary'][:150] + "...",
                    "sentiment": article['sentiment_score'],
                    "priority": "high" if abs(article['sentiment_score']) > 0.5 else "normal"
                })
        
        # Interest-based news
        for interest in user_interests:
            # Use vector search for interest-based content
            search_results = await self.api.search({
                "query": interest,
                "include_news": True,
                "similarity_threshold": 0.7,
                "limit": 3
            })
            
            for result in search_results:
                feed_items.append({
                    "type": "interest_news",
                    "topic": interest,
                    "content": result['content'][:150] + "...",
                    "relevance": result['similarity_score'],
                    "priority": "normal"
                })
        
        # Sort by priority and recency
        return sorted(feed_items, key=lambda x: (
            x['priority'] == 'high',
            x.get('sentiment', 0),
            x.get('relevance', 0)
        ), reverse=True)
```

### 🏢 **Enterprise Dashboard**

```python
class EnterpriseDashboard:
    def __init__(self, api_client):
        self.api = api_client
    
    async def generate_market_intelligence_report(self, sectors):
        """Generate comprehensive market intelligence"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "sectors": {},
            "market_sentiment": {},
            "key_developments": []
        }
        
        for sector, symbols in sectors.items():
            sector_news = []
            sector_sentiment = []
            
            for symbol in symbols:
                news = await self.api.get_news(symbol=symbol, limit=10)
                analysis = await self.api.get_analysis(symbol)
                
                sector_news.extend(news)
                sector_sentiment.append(analysis.get('confidence_score', 0))
            
            # Calculate sector metrics
            avg_sentiment = sum(
                article['sentiment_score'] for article in sector_news
            ) / len(sector_news) if sector_news else 0
            
            report["sectors"][sector] = {
                "symbol_count": len(symbols),
                "news_volume": len(sector_news),
                "avg_sentiment": avg_sentiment,
                "confidence": sum(sector_sentiment) / len(sector_sentiment)
            }
        
        return report
```

## 🚀 **Next Steps**

Ready to master news intelligence? Explore these related guides:

- 🔍 **[Vector Search Guide](vector-search.md)** - Combine news with semantic search
- 💹 **[Market Data](market-data.md)** - Correlate news with price movements
- 💡 **[Use Cases](use-cases.md)** - Real-world applications
- 🔗 **[API Reference](api-reference.md)** - Complete technical documentation

---

<div align="center">

**📰 Ready to Transform News into Intelligence?**

*Our news and analysis capabilities turn the flood of financial information into actionable insights. Start building smarter financial applications today!* 🚀✨

</div> 

# 🔍 Vector Search & Semantic Intelligence

> 🧠 **Unlock the power of AI-driven semantic search across financial data**

Transform how you discover financial insights with our advanced vector search capabilities. Our system uses state-of-the-art sentence transformers to understand the meaning behind your queries, delivering relevant results even when exact keywords don't match. 🚀

## 🌟 What is Vector Search?

Vector search goes beyond traditional keyword matching by understanding the **semantic meaning** of your queries. Instead of looking for exact text matches, our system:

- 🧠 **Understands Context**: Grasps the meaning behind your questions
- 🎯 **Finds Relevant Content**: Discovers related information even with different wording
- 📊 **Ranks by Relevance**: Uses AI to score and rank results by similarity
- ⚡ **Delivers Fast Results**: Optimized for real-time financial applications

### 🔬 **How It Works**

1. **📝 Content Embedding**: All financial content is converted to high-dimensional vectors
2. **🔍 Query Processing**: Your search query is transformed into the same vector space
3. **📊 Similarity Calculation**: Cosine similarity determines content relevance
4. **🎯 Intelligent Ranking**: Results are ranked by similarity and filtered by your criteria

## 🚀 Getting Started with Vector Search

### 📡 **Basic Search Endpoint**
```bash
POST /v1/stock/search
```

### 🎯 **Simple Search Example**
```python
import requests

# Basic semantic search
search_request = {
    "query": "Apple iPhone sales declining",
    "limit": 10,
    "similarity_threshold": 0.7
}

response = requests.post(
    "http://localhost:8000/v1/stock/search",
    json=search_request,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

results = response.json()
for result in results:
    print(f"📊 Score: {result['similarity_score']:.3f}")
    print(f"📰 Type: {result['content_type']}")
    print(f"🏢 Symbol: {result['symbol']}")
    print(f"📝 Content: {result['content'][:150]}...")
    print("---")
```

## 🎛️ Advanced Search Parameters

### 🔧 **Query Configuration**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `query` | string | Your search question/topic | "Tesla battery technology" |
| `symbols` | list[string] | Filter by specific stocks | ["TSLA", "AAPL"] |
| `limit` | integer | Max results (1-100) | 20 |
| `similarity_threshold` | float | Min similarity (0.0-1.0) | 0.8 |
| `include_news` | boolean | Include news articles | true |
| `include_analysis` | boolean | Include analysis reports | true |
| `date_from` | datetime | Filter from date | "2024-01-01T00:00:00Z" |
| `date_to` | datetime | Filter to date | "2024-12-31T23:59:59Z" |

### 🎯 **Advanced Search Examples**

#### 🔍 **Targeted Symbol Search**
```python
# Search for Tesla-specific battery technology news
search_request = {
    "query": "battery technology breakthrough innovation",
    "symbols": ["TSLA"],
    "include_news": True,
    "include_analysis": True,
    "similarity_threshold": 0.85,
    "limit": 15
}
```

#### 📅 **Time-Filtered Search**
```python
# Search for recent AI-related news in tech stocks
search_request = {
    "query": "artificial intelligence machine learning AI",
    "symbols": ["AAPL", "GOOGL", "MSFT", "NVDA"],
    "date_from": "2024-01-01T00:00:00Z",
    "include_news": True,
    "similarity_threshold": 0.75
}
```

#### 📊 **Analysis-Only Search**
```python
# Find analyst reports about renewable energy
search_request = {
    "query": "renewable energy solar wind power sustainability",
    "include_news": False,
    "include_analysis": True,
    "similarity_threshold": 0.8,
    "limit": 10
}
```

## 🎨 **Search Query Strategies**

### 💡 **Effective Query Patterns**

#### 🎯 **Topic-Based Queries**
```python
# Good: Descriptive and specific
"electric vehicle market share competition"
"semiconductor chip shortage supply chain"
"cloud computing revenue growth"

# Avoid: Too generic
"stocks"
"market"
"news"
```

#### 🔍 **Question-Based Queries**
```python
# Natural language questions work great!
"What are analysts saying about Apple's AI strategy?"
"How is the chip shortage affecting automotive stocks?"
"Which companies are leading in renewable energy?"
```

#### 🏢 **Company-Specific Insights**
```python
# Combine company focus with topic
"Tesla autonomous driving progress"
"Microsoft cloud computing growth"
"Amazon logistics automation"
```

### 📊 **Similarity Threshold Guide**

| Threshold | Use Case | Description |
|-----------|----------|-------------|
| 0.9-1.0 | 🎯 Exact matches | Very specific, high-precision results |
| 0.8-0.9 | 📊 Relevant content | Good balance of precision and recall |
| 0.7-0.8 | 🔍 Broader search | More results, some may be tangentially related |
| 0.6-0.7 | 🌐 Exploratory | Cast a wide net, good for discovery |
| <0.6 | ⚠️ Too broad | May include irrelevant results |

## 🚀 **Real-World Use Cases**

### 🤖 **AI Trading Assistant**
```python
# Monitor sentiment around specific events
def monitor_earnings_sentiment(symbol):
    search_request = {
        "query": f"earnings report financial results revenue profit",
        "symbols": [symbol],
        "include_news": True,
        "include_analysis": True,
        "similarity_threshold": 0.8,
        "date_from": (datetime.now() - timedelta(days=7)).isoformat()
    }
    
    results = search_stocks(search_request)
    
    # Analyze sentiment trends
    positive_sentiment = sum(1 for r in results if r.get('sentiment_score', 0) > 0.1)
    negative_sentiment = sum(1 for r in results if r.get('sentiment_score', 0) < -0.1)
    
    return {
        "symbol": symbol,
        "positive_mentions": positive_sentiment,
        "negative_mentions": negative_sentiment,
        "total_mentions": len(results)
    }
```

### 📊 **Market Research Platform**
```python
# Research emerging trends across sectors
def research_trend(trend_topic, sectors=None):
    search_request = {
        "query": trend_topic,
        "symbols": sectors,
        "include_news": True,
        "include_analysis": True,
        "similarity_threshold": 0.75,
        "limit": 50
    }
    
    results = search_stocks(search_request)
    
    # Group by symbol and analyze
    symbol_insights = {}
    for result in results:
        symbol = result['symbol']
        if symbol not in symbol_insights:
            symbol_insights[symbol] = []
        symbol_insights[symbol].append(result)
    
    return symbol_insights
```

### 🎯 **Risk Monitoring System**
```python
# Monitor for risk-related content
def monitor_risk_signals():
    risk_queries = [
        "regulatory investigation lawsuit legal",
        "cybersecurity breach data hack",
        "supply chain disruption shortage",
        "executive departure leadership change"
    ]
    
    all_risks = []
    for query in risk_queries:
        search_request = {
            "query": query,
            "include_news": True,
            "similarity_threshold": 0.8,
            "date_from": (datetime.now() - timedelta(days=1)).isoformat(),
            "limit": 20
        }
        
        results = search_stocks(search_request)
        all_risks.extend(results)
    
    return sorted(all_risks, key=lambda x: x['similarity_score'], reverse=True)
```

## ⚡ **Performance Optimization**

### 🚀 **Caching Strategy**
Our vector search includes intelligent caching:

- **🧠 Embedding Cache**: Pre-computed embeddings for faster searches
- **🔍 Query Cache**: Cached results for repeated searches
- **⏰ Smart Expiration**: Time-based cache invalidation for fresh data

### 📊 **Monitoring Performance**
```python
# Check cache performance
cache_stats = requests.get(
    "http://localhost:8000/v1/stock/cache/stats",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
).json()

print(f"🎯 Cache Hit Rate: {cache_stats['hit_rate']:.1f}%")
print(f"📊 Embedding Cache Size: {cache_stats['embedding_cache_entries']}")
print(f"🔍 Search Cache Hits: {cache_stats['search_cache_hits']}")
```

### 🎛️ **Best Practices**

1. **🎯 Use Specific Queries**: More specific queries yield better results
2. **📊 Adjust Thresholds**: Fine-tune similarity thresholds for your use case
3. **🔄 Leverage Caching**: Repeated queries benefit from intelligent caching
4. **📅 Filter by Date**: Use date filters to focus on recent or historical data
5. **🏢 Symbol Filtering**: Narrow searches with specific symbols when possible

## 🔬 **Technical Details**

### 🧠 **Embedding Model**
- **Model**: `all-MiniLM-L6-v2` (configurable)
- **Dimensions**: 384-dimensional vectors
- **Language**: Optimized for English financial content
- **Performance**: ~14k tokens/second on modern hardware

### 📊 **Similarity Calculation**
- **Method**: Cosine similarity
- **Range**: 0.0 (completely different) to 1.0 (identical)
- **Optimization**: Vectorized operations using NumPy
- **Indexing**: Optimized database queries with proper indexing

### 🗄️ **Storage & Retrieval**
- **Database**: PostgreSQL with vector extensions
- **Indexing**: Optimized indexes for fast similarity searches
- **Caching**: Multi-layer caching for performance
- **Scalability**: Designed for high-volume concurrent searches

## 🎉 **Next Steps**

Ready to master vector search? Explore these related guides:

- 📰 **[News & Analysis](news-analysis.md)** - Understand the content you're searching
- 💹 **[Market Data](market-data.md)** - Combine search with real-time data
- ⚡ **[Performance Guide](performance.md)** - Optimize for your use case
- 🔗 **[API Reference](api-reference.md)** - Complete endpoint documentation

---

<div align="center">

**🔍 Ready to unlock the power of semantic financial search?**

*Transform how you discover market insights with AI-powered vector search. Start exploring the hidden connections in financial data today!* 🚀✨

</div> 

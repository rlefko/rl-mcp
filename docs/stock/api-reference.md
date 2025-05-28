# 🔗 Stock API Reference

> 📚 **Complete reference for all stock market API endpoints**

This comprehensive reference covers every endpoint, parameter, and response format in our stock market API. Perfect for developers who need detailed technical specifications. 🚀

## 🔐 Authentication

All endpoints require Bearer token authentication:

```bash
Authorization: Bearer YOUR_API_TOKEN
```

**Base URL**: `http://localhost:8000/v1/stock`

---

## 📊 Stock Data Management

### 📋 **Get Stock Data**
```http
GET /v1/stock
```

Retrieve stock data with filtering and pagination.

#### 🔧 **Query Parameters**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `symbol` | string | No | - | Filter by stock symbol (e.g., "AAPL") |
| `data_type` | string | No | - | Filter by type: "news", "analysis", "price" |
| `limit` | integer | No | 50 | Results per page (1-100) |
| `offset` | integer | No | 0 | Number of results to skip |

#### 📤 **Response**
```json
[
  {
    "id": 123,
    "symbol": "AAPL",
    "data_type": "news",
    "content": "Apple announces new iPhone features...",
    "extra_metadata": {
      "source": "Reuters",
      "sentiment_score": 0.8
    },
    "embedding_id": "emb_abc123",
    "similarity_score": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

#### 🎯 **Example**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/v1/stock?symbol=AAPL&data_type=news&limit=10"
```

---

### ➕ **Create Stock Data**
```http
POST /v1/stock
```

Create new stock data entry with automatic vector embedding.

#### 📥 **Request Body**
```json
{
  "symbol": "TSLA",
  "data_type": "analysis",
  "content": "Tesla's Q4 earnings show strong growth in EV deliveries...",
  "extra_metadata": {
    "analyst": "Goldman Sachs",
    "rating": "Buy",
    "target_price": 250.0
  }
}
```

#### 📤 **Response**
```json
{
  "id": 124,
  "symbol": "TSLA",
  "data_type": "analysis",
  "content": "Tesla's Q4 earnings show strong growth in EV deliveries...",
  "extra_metadata": {
    "analyst": "Goldman Sachs",
    "rating": "Buy",
    "target_price": 250.0
  },
  "embedding_id": "emb_def456",
  "similarity_score": null,
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

---

### 🔍 **Get Stock Data by ID**
```http
GET /v1/stock/{stock_data_id}
```

Retrieve specific stock data entry by ID.

#### 📤 **Response**
Same format as individual item in GET /v1/stock response.

---

### ✏️ **Update Stock Data**
```http
PATCH /v1/stock/{stock_data_id}
```

Update existing stock data entry.

#### 📥 **Request Body**
```json
{
  "content": "Updated analysis content...",
  "extra_metadata": {
    "updated_rating": "Strong Buy"
  }
}
```

---

### 🗑️ **Delete Stock Data**
```http
DELETE /v1/stock/{stock_data_id}
```

Delete stock data entry.

#### 📤 **Response**
`204 No Content`

---

## 🔍 Vector Search

### 🧠 **Semantic Search**
```http
POST /v1/stock/search
```

Perform AI-powered semantic search across stock data.

#### 📥 **Request Body**
```json
{
  "query": "Tesla battery technology innovations",
  "symbols": ["TSLA", "PANW"],
  "limit": 20,
  "similarity_threshold": 0.8,
  "include_news": true,
  "include_analysis": true,
  "date_from": "2024-01-01T00:00:00Z",
  "date_to": "2024-12-31T23:59:59Z"
}
```

#### 🔧 **Parameters**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query text |
| `symbols` | array[string] | No | null | Filter by stock symbols |
| `limit` | integer | No | 10 | Max results (1-100) |
| `similarity_threshold` | float | No | 0.7 | Min similarity (0.0-1.0) |
| `include_news` | boolean | No | true | Include news articles |
| `include_analysis` | boolean | No | true | Include analysis reports |
| `date_from` | datetime | No | null | Filter from date |
| `date_to` | datetime | No | null | Filter to date |

#### 📤 **Response**
```json
[
  {
    "content": "Tesla announces breakthrough in battery technology...",
    "content_type": "news",
    "symbol": "TSLA",
    "similarity_score": 0.92,
    "extra_metadata": {
      "source": "TechCrunch",
      "sentiment_score": 0.8
    },
    "timestamp": "2024-01-15T09:30:00Z"
  }
]
```

---

## 💹 Market Data

### 📈 **Get Stock Price**
```http
GET /v1/stock/price/{symbol}
```

Get current stock price and metrics.

#### 📤 **Response**
```json
{
  "symbol": "AAPL",
  "price": 185.25,
  "change": 2.15,
  "change_percent": 1.17,
  "volume": 45678900,
  "market_cap": 2890000000000,
  "pe_ratio": 28.5,
  "timestamp": "2024-01-15T16:00:00Z"
}
```

---

### 📰 **Get Stock News**
```http
GET /v1/stock/news
```

Get latest stock news with sentiment analysis.

#### 🔧 **Query Parameters**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `symbol` | string | No | - | Filter by stock symbol |
| `limit` | integer | No | 20 | Number of articles (1-100) |

#### 📤 **Response**
```json
[
  {
    "title": "Apple Reports Record Q4 Earnings",
    "summary": "Apple exceeded expectations with strong iPhone sales...",
    "url": "https://example.com/apple-earnings",
    "source": "Reuters",
    "published_at": "2024-01-15T14:30:00Z",
    "symbols": ["AAPL"],
    "sentiment_score": 0.75,
    "relevance_score": 0.95
  }
]
```

---

### 🧠 **Stock Analysis**
```http
GET /v1/stock/analysis/{symbol}
```

Get comprehensive AI-powered stock analysis.

#### 📤 **Response**
```json
{
  "symbol": "AAPL",
  "analysis_type": "comprehensive",
  "insights": "Apple shows strong fundamentals with growing services revenue...",
  "confidence_score": 0.87,
  "recommendation": "Buy",
  "target_price": 200.0,
  "risk_level": "Medium"
}
```

---

### 🌍 **Market Summary**
```http
GET /v1/stock/market/summary
```

Get comprehensive market overview.

#### 📤 **Response**
```json
{
  "date": "2024-01-15T16:00:00Z",
  "total_symbols": 500,
  "top_gainers": [
    {
      "symbol": "NVDA",
      "price": 875.50,
      "change": 45.25,
      "change_percent": 5.45,
      "volume": 12345678,
      "market_cap": 2150000000000,
      "pe_ratio": 65.2,
      "timestamp": "2024-01-15T16:00:00Z"
    }
  ],
  "top_losers": [
    {
      "symbol": "META",
      "price": 485.20,
      "change": -15.80,
      "change_percent": -3.15,
      "volume": 8765432,
      "market_cap": 1230000000000,
      "pe_ratio": 22.8,
      "timestamp": "2024-01-15T16:00:00Z"
    }
  ],
  "market_sentiment": 0.15,
  "news_count": 1250,
  "trending_topics": ["AI", "earnings", "electric vehicles"]
}
```

---

### 🔥 **Trending Symbols**
```http
GET /v1/stock/market/trending
```

Get trending stocks based on data volume.

#### 🔧 **Query Parameters**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 10 | Number of symbols (1-50) |

#### 📤 **Response**
```json
[
  {
    "symbol": "TSLA",
    "mention_count": 145,
    "sentiment_avg": 0.65,
    "price_change_percent": 3.2
  }
]
```

---

## 🔄 Data Ingestion

### 📥 **Ingest News (Background)**
```http
POST /v1/stock/ingest/news
```

Start background news ingestion.

#### 🔧 **Query Parameters**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `symbol` | string | No | - | Filter news by symbol |

#### 📤 **Response**
```json
{
  "message": "News ingestion started in background",
  "symbol": "AAPL",
  "status": "processing"
}
```

---

### 📥 **Ingest News (Synchronous)**
```http
POST /v1/stock/ingest/news/sync
```

Synchronous news ingestion with immediate results.

#### 📤 **Response**
```json
{
  "message": "News ingestion completed",
  "symbol": "AAPL",
  "articles_processed": 25,
  "status": "completed"
}
```

---

## ⚡ Performance & Monitoring

### 📊 **Cache Statistics**
```http
GET /v1/stock/cache/stats
```

Get cache performance metrics.

#### 📤 **Response**
```json
{
  "cache_hits": 1250,
  "cache_misses": 180,
  "cache_size": 5000,
  "hit_rate": 87.4,
  "last_updated": "2024-01-15T16:00:00Z"
}
```

---

### 🧹 **Cache Cleanup**
```http
POST /v1/stock/cache/cleanup
```

Trigger cache cleanup in background.

#### 📤 **Response**
```json
{
  "message": "Cache cleanup started",
  "status": "processing"
}
```

---

### 🏥 **Health Check**
```http
GET /v1/stock/health
```

Check stock service health and connectivity.

#### 📤 **Response**
```json
{
  "status": "healthy",
  "database_connected": true,
  "vector_service_ready": true,
  "market_service_ready": true,
  "cache_operational": true,
  "last_data_update": "2024-01-15T15:45:00Z",
  "uptime_seconds": 86400
}
```

---

## 🚨 Error Responses

### 📋 **Standard Error Format**
```json
{
  "detail": "Error description",
  "status_code": 400,
  "timestamp": "2024-01-15T16:00:00Z"
}
```

### 🔢 **HTTP Status Codes**
| Code | Description | Common Causes |
|------|-------------|---------------|
| `200` | Success | Request completed successfully |
| `201` | Created | Resource created successfully |
| `204` | No Content | Resource deleted successfully |
| `400` | Bad Request | Invalid parameters or request body |
| `401` | Unauthorized | Missing or invalid authentication token |
| `404` | Not Found | Resource not found |
| `422` | Validation Error | Request validation failed |
| `500` | Internal Error | Server error or service unavailable |

### 🛠️ **Common Error Examples**

#### 🔐 **Authentication Error**
```json
{
  "detail": "Invalid authentication credentials",
  "status_code": 401
}
```

#### ❌ **Validation Error**
```json
{
  "detail": [
    {
      "loc": ["body", "similarity_threshold"],
      "msg": "ensure this value is less than or equal to 1.0",
      "type": "value_error.number.not_le"
    }
  ],
  "status_code": 422
}
```

#### 🔍 **Not Found Error**
```json
{
  "detail": "Price data not found for symbol: INVALID",
  "status_code": 404
}
```

---

## 🎯 Rate Limiting

### 📊 **Current Limits**
- **General Endpoints**: 100 requests/minute
- **Search Endpoints**: 50 requests/minute  
- **Data Ingestion**: 10 requests/minute

### 📈 **Rate Limit Headers**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642262400
```

---

## 🧪 Testing & Examples

### 🔧 **cURL Examples**

#### 🔍 **Basic Search**
```bash
curl -X POST "http://localhost:8000/v1/stock/search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Apple iPhone sales",
    "limit": 5,
    "similarity_threshold": 0.8
  }'
```

#### 💹 **Get Market Summary**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/v1/stock/market/summary"
```

#### 📰 **Get News for Symbol**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/v1/stock/news?symbol=TSLA&limit=10"
```

### 🐍 **Python SDK Example**
```python
import requests

class StockAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def search(self, query, **kwargs):
        data = {"query": query, **kwargs}
        response = requests.post(
            f"{self.base_url}/search",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def get_price(self, symbol):
        response = requests.get(
            f"{self.base_url}/price/{symbol}",
            headers=self.headers
        )
        return response.json()

# Usage
api = StockAPI("http://localhost:8000/v1/stock", "YOUR_TOKEN")
results = api.search("Tesla battery technology", symbols=["TSLA"])
price = api.get_price("AAPL")
```

---

<div align="center">

**🔗 Complete API Reference at Your Fingertips**

*Everything you need to integrate our powerful stock market intelligence into your applications. Start building with confidence!* 🚀✨

</div> 

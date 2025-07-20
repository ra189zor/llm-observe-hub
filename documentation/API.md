
# API Documentation

LLM-Lens provides a comprehensive REST API for monitoring, analytics, and configuration. This document details all available endpoints.

## Base URL

- **Local Development:** `http://localhost:5000`

## Authentication

Currently, LLM-Lens does not require authentication. All endpoints are publicly accessible.

⚠️ **Security Note:** In production, consider implementing authentication for sensitive endpoints.

## Core Proxy Endpoint

### Chat Completions Proxy

**Endpoint:** `POST /proxy/v1/chat/completions`

**Description:** Main proxy endpoint that forwards requests to your local LLM while capturing comprehensive metrics.

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "model": "string",
  "messages": [
    {
      "role": "user|assistant|system",
      "content": "string"
    }
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 100,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

**Response:** Returns the original LLM response while logging metrics in the background.

**Example:**
```bash
curl -X POST http://localhost:5000/proxy/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

## Analytics Endpoints

### Performance Analytics

**Endpoint:** `GET /api/analytics/performance`

**Description:** Comprehensive performance analytics and insights.

**Response:**
```json
{
  "summary": {
    "total_requests": 150,
    "success_rate": 95.5,
    "streaming_requests": 45,
    "avg_performance_score": 0.85
  },
  "latency_stats": {
    "mean": 1250.5,
    "median": 1100.0,
    "p95": 2800.0,
    "p99": 4200.0
  },
  "throughput_stats": {
    "mean_tokens_per_sec": 25.4,
    "max_tokens_per_sec": 45.2,
    "min_tokens_per_sec": 8.1
  },
  "model_performance": {
    "llama2": {
      "request_count": 80,
      "avg_latency": 1150.0,
      "avg_performance_score": 0.88,
      "error_rate": 2.5
    }
  }
}
```

### Model Performance Comparison

**Endpoint:** `GET /api/model-performance`

**Parameters:**
- `hours` (optional): Time range in hours (default: 24)

**Response:**
```json
{
  "models": [
    {
      "model_name": "llama2",
      "avg_latency": 1150.0,
      "avg_throughput": 25.4,
      "avg_performance": 0.88,
      "request_count": 80,
      "total_tokens": 12500
    }
  ],
  "time_period_hours": 24,
  "recommendation": "llama2"
}
```

### Cost Analysis

**Endpoint:** `GET /api/cost-analysis`

**Parameters:**
- `hours` (optional): Time range in hours (default: 24)

**Response:**
```json
{
  "total_cost": 2.45,
  "cost_breakdown": {
    "llama2": {
      "requests": 80,
      "total_tokens": 12500,
      "estimated_cost": 2.45,
      "avg_latency": 1150.0
    }
  },
  "time_period_hours": 24
}
```

## Request Log Endpoints

### Get Log Details

**Endpoint:** `GET /api/logs/{log_id}`

**Parameters:**
- `log_id`: Integer ID of the log entry

**Response:**
```json
{
  "id": 123,
  "model_name": "llama2",
  "start_time": "2025-01-17T10:30:00Z",
  "end_time": "2025-01-17T10:30:02Z",
  "latency_ms": 2000,
  "prompt_tokens": 50,
  "completion_tokens": 75,
  "total_tokens": 125,
  "tokens_per_second": 37.5,
  "time_to_first_token_ms": 500,
  "performance_score": 0.85,
  "is_streaming": false,
  "temperature": 0.7,
  "max_tokens": 100,
  "request_metadata": {
    "temperature": 0.7,
    "max_tokens": 100
  },
  "input_text": "Hello, how are you?",
  "output_text": "I'm doing well, thank you for asking!",
  "error_message": null
}
```

## Alert Management

### Get Alert Rules

**Endpoint:** `GET /api/alerts/rules`

**Response:**
```json
[
  {
    "id": 1,
    "name": "High Latency Alert",
    "metric": "latency",
    "threshold": 5000.0,
    "operator": "gt",
    "is_active": true,
    "created_at": "2025-01-17T10:00:00Z"
  }
]
```

### Create Alert Rule

**Endpoint:** `POST /api/alerts/rules`

**Request Body:**
```json
{
  "name": "High Latency Alert",
  "metric": "latency",
  "threshold": 5000.0,
  "operator": "gt",
  "is_active": true
}
```

**Available Metrics:**
- `latency` - Response time in milliseconds
- `tokens_per_second` - Throughput metric
- `error_rate` - Percentage of failed requests

**Available Operators:**
- `gt` - Greater than
- `lt` - Less than
- `eq` - Equal to

**Response:**
```json
{
  "id": 2,
  "message": "Alert rule created successfully"
}
```

### Get Alert Events

**Endpoint:** `GET /api/alerts/events`

**Response:**
```json
[
  {
    "id": 1,
    "rule_name": "High Latency Alert",
    "metric_value": 6500.0,
    "threshold": 5000.0,
    "message": "High Latency Alert: latency (6500.0) gt 5000.0",
    "triggered_at": "2025-01-17T10:45:00Z",
    "resolved_at": null
  }
]
```

## Cost Management

### Get Cost Settings

**Endpoint:** `GET /api/cost-settings`

**Response:**
```json
[
  {
    "id": 1,
    "model_name": "llama2",
    "cost_per_1k_input_tokens": 0.001,
    "cost_per_1k_output_tokens": 0.002,
    "electricity_cost_per_hour": 0.50,
    "created_at": "2025-01-17T10:00:00Z",
    "updated_at": "2025-01-17T10:00:00Z"
  }
]
```

### Create/Update Cost Settings

**Endpoint:** `POST /api/cost-settings`

**Content-Type:** `application/x-www-form-urlencoded`

**Parameters:**
- `model_name`: String
- `cost_per_1k_input_tokens`: Float (default: 0.0)
- `cost_per_1k_output_tokens`: Float (default: 0.0)
- `electricity_cost_per_hour`: Float (default: 0.0)

**Example:**
```bash
curl -X POST http://localhost:5000/api/cost-settings \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "model_name=llama2&cost_per_1k_input_tokens=0.001&cost_per_1k_output_tokens=0.002&electricity_cost_per_hour=0.50"
```

## Budget Management

### Get Budgets

**Endpoint:** `GET /api/budgets`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Monthly AI Budget",
    "budget_type": "monthly",
    "amount": 100.0,
    "current_usage": 25.50,
    "is_active": true,
    "created_at": "2025-01-17T10:00:00Z",
    "reset_at": null
  }
]
```

### Create Budget

**Endpoint:** `POST /api/budgets`

**Content-Type:** `application/x-www-form-urlencoded`

**Parameters:**
- `name`: String
- `budget_type`: String (daily|weekly|monthly)
- `amount`: Float

**Example:**
```bash
curl -X POST http://localhost:5000/api/budgets \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Monthly AI Budget&budget_type=monthly&amount=100.00"
```

## Model Comparison

### Get Model Comparisons

**Endpoint:** `GET /api/model-comparisons`

**Response:**
```json
[
  {
    "id": 1,
    "comparison_name": "LLaMA vs GPT4All",
    "model_a": "llama2",
    "model_b": "gpt4all",
    "test_prompt": "Explain quantum computing",
    "result_a_latency": 1200.0,
    "result_b_latency": 1800.0,
    "result_a_tokens": 150,
    "result_b_tokens": 200,
    "result_a_cost": 0.05,
    "result_b_cost": 0.08,
    "winner": "model_a",
    "created_at": "2025-01-17T10:00:00Z"
  }
]
```

### Create Model Comparison

**Endpoint:** `POST /api/model-comparisons`

**Content-Type:** `application/x-www-form-urlencoded`

**Parameters:**
- `comparison_name`: String
- `model_a`: String
- `model_b`: String
- `test_prompt`: String

## Optimization Suggestions

### Get Optimization Suggestions

**Endpoint:** `GET /api/optimization-suggestions`

**Response:**
```json
[
  {
    "id": 1,
    "suggestion_type": "performance",
    "model_name": "llama2",
    "title": "High Latency Detected",
    "description": "Average latency is 2500ms with 45 requests exceeding 150% of average. Consider optimizing model parameters or upgrading hardware.",
    "priority": "high",
    "potential_improvement": "25-40% latency reduction",
    "is_implemented": false,
    "created_at": "2025-01-17T10:00:00Z",
    "implemented_at": null
  }
]
```

### Generate Optimization Suggestions

**Endpoint:** `POST /api/optimization-suggestions/generate`

**Description:** Analyzes recent performance data and generates AI-powered optimization suggestions.

**Response:**
```json
{
  "message": "Generated 3 optimization suggestions",
  "suggestions": [
    {
      "suggestion_type": "performance",
      "model_name": "general",
      "title": "High Latency Detected",
      "description": "Average latency is 2500ms...",
      "priority": "high",
      "potential_improvement": "25-40% latency reduction"
    }
  ]
}
```

### Mark Suggestion as Implemented

**Endpoint:** `POST /api/optimization-suggestions/{suggestion_id}/implement`

**Parameters:**
- `suggestion_id`: Integer ID of the suggestion

**Response:**
```json
{
  "message": "Suggestion marked as implemented"
}
```

## Data Export

### Export as CSV

**Endpoint:** `GET /api/export/csv`

**Parameters:**
- `hours` (optional): Time range in hours (default: 24)
- `model` (optional): Filter by specific model

**Response:** CSV file download

**Example:**
```bash
curl "http://localhost:5000/api/export/csv?hours=24&model=llama2" \
  --output llm_logs.csv
```

### Export as JSON

**Endpoint:** `GET /api/export/json`

**Parameters:**
- `hours` (optional): Time range in hours (default: 24)
- `model` (optional): Filter by specific model

**Response:** JSON file download

**Example:**
```bash
curl "http://localhost:5000/api/export/json?hours=24" \
  --output llm_logs.json
```

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid JSON in request body"
}
```

### 404 Not Found
```json
{
  "detail": "Log entry not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Analytics calculation failed: [error message]"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Connection error to local LLM: [error message]"
}
```

## Rate Limits

Currently, there are no rate limits implemented. However, for production use, consider implementing rate limiting based on your requirements.

## Webhooks (Future Feature)

Webhook support for real-time notifications is planned for future releases.

## SDK Examples

### Python SDK Example

```python
import requests
import json

class LLMLensClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def get_performance_analytics(self):
        response = requests.get(f"{self.base_url}/api/analytics/performance")
        return response.json()
    
    def create_alert_rule(self, name, metric, threshold, operator):
        data = {
            "name": name,
            "metric": metric,
            "threshold": threshold,
            "operator": operator
        }
        response = requests.post(f"{self.base_url}/api/alerts/rules", json=data)
        return response.json()
    
    def export_logs(self, hours=24, format="csv"):
        response = requests.get(f"{self.base_url}/api/export/{format}?hours={hours}")
        return response.content

# Usage
client = LLMLensClient()
analytics = client.get_performance_analytics()
print(f"Total requests: {analytics['summary']['total_requests']}")
```

### JavaScript SDK Example

```javascript
class LLMLensClient {
    constructor(baseUrl = "http://localhost:5000") {
        this.baseUrl = baseUrl;
    }
    
    async getPerformanceAnalytics() {
        const response = await fetch(`${this.baseUrl}/api/analytics/performance`);
        return await response.json();
    }
    
    async createAlertRule(name, metric, threshold, operator) {
        const response = await fetch(`${this.baseUrl}/api/alerts/rules`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, metric, threshold, operator })
        });
        return await response.json();
    }
    
    async exportLogs(hours = 24, format = "json") {
        const response = await fetch(`${this.baseUrl}/api/export/${format}?hours=${hours}`);
        return await response.blob();
    }
}

// Usage
const client = new LLMLensClient();
client.getPerformanceAnalytics().then(analytics => {
    console.log(`Total requests: ${analytics.summary.total_requests}`);
});
```

## Testing the API

### Using curl

Test all endpoints with curl commands:

```bash
# Test performance analytics
curl http://localhost:5000/api/analytics/performance

# Test model performance
curl "http://localhost:5000/api/model-performance?hours=24"

# Create alert rule
curl -X POST http://localhost:5000/api/alerts/rules \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Alert","metric":"latency","threshold":3000,"operator":"gt"}'

# Export data
curl "http://localhost:5000/api/export/json?hours=1" --output test_export.json
```

### Using Postman

Import this collection into Postman for easy testing:

```json
{
  "info": {
    "name": "LLM-Lens API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Performance Analytics",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/analytics/performance",
          "host": ["{{base_url}}"],
          "path": ["api", "analytics", "performance"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:5000"
    }
  ]
}
```

This comprehensive API documentation should help users integrate with and extend LLM-Lens functionality programmatically.

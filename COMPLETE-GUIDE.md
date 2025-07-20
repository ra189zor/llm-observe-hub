# LLM-Lens COMPLETE GUIDE

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Local Installation](#local-installation)
  - [Docker Installation](#docker-installation)
  - [Environment Configuration](#environment-configuration)
- [Deployment](#deployment)
  - [Local Deployment](#local-deployment)
  - [Docker Deployment](#docker-deployment)
  - [Production Considerations](#production-considerations)
- [API Reference](#api-reference)
  - [Proxy Endpoint](#proxy-endpoint)
  - [Analytics Endpoints](#analytics-endpoints)
  - [Alert Management](#alert-management)
  - [Cost & Budget Management](#cost--budget-management)
  - [Model Comparison](#model-comparison)
  - [Optimization Suggestions](#optimization-suggestions)
  - [Data Export](#data-export)
  - [SDK Examples](#sdk-examples)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [Testing & Validation](#testing--validation)
- [Acknowledgments](#acknowledgments)

---

## Introduction

LLM-Lens is a developer-focused observability platform for local LLMs, providing real-time analytics, cost tracking, and performance optimization through a modern dashboard and comprehensive API.

---

## Installation

### Quick Start

```bash
git clone https://github.com/your-username/llm-lens.git
cd llm-lens
pip install -r requirements.txt
python main.py
```

### Local Installation

#### Prerequisites
- Python 3.11+
- pip
- Git

#### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/llm-lens.git
   cd llm-lens
   ```
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart python-dotenv
   ```
3. Create a `.env` file (optional):
   ```env
   DEFAULT_LLM_URL=http://localhost:1234/v1/chat/completions
   DATABASE_URL=sqlite:///./llm_lens.db
   ```
4. Run the application:
   ```bash
   python main.py
   ```

### Docker Installation

1. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY . .
   RUN pip install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart
   EXPOSE 5000
   CMD ["python", "main.py"]
   ```
2. Build and run:
   ```bash
   docker build -t llm-lens .
   docker run -p 5000:5000 llm-lens
   ```

### Environment Configuration

- Use a `.env` file for all configuration:
  ```env
  DEFAULT_LLM_URL=http://localhost:1234/v1/chat/completions
  OLLAMA_URL=http://localhost:11434/api/chat
  DATABASE_URL=sqlite:///./llm_lens.db
  ```

---

## Deployment

### Local Deployment

- Run with auto-reload for development:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 5000 --reload
  ```

### Docker Deployment

- See Docker instructions above.

### Production Considerations

- Set environment variables for LLM endpoints and database.
- Use Gunicorn for production:
  ```bash
  pip install gunicorn
  gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
  ```

---

## API Reference

### Proxy Endpoint

- `POST /proxy/v1/chat/completions`
  - Forwards requests to your local LLM and logs metrics.

### Analytics Endpoints

- `GET /api/analytics/performance`
- `GET /api/model-performance`
- `GET /api/cost-analysis`
- `GET /api/logs/{log_id}`

### Alert Management

- `GET /api/alerts/rules`
- `POST /api/alerts/rules`
- `GET /api/alerts/events`

### Cost & Budget Management

- `GET /api/cost-settings`
- `POST /api/cost-settings`
- `GET /api/budgets`
- `POST /api/budgets`

### Model Comparison

- `GET /api/model-comparisons`
- `POST /api/model-comparisons`

### Optimization Suggestions

- `GET /api/optimization-suggestions`
- `POST /api/optimization-suggestions/generate`
- `POST /api/optimization-suggestions/{suggestion_id}/implement`

### Data Export

- `GET /api/export/csv`
- `GET /api/export/json`

### SDK Examples

#### Python
```python
import requests
client = requests.get("http://localhost:5000/api/analytics/performance")
print(client.json())
```

#### JavaScript
```javascript
fetch("http://localhost:5000/api/analytics/performance")
  .then(res => res.json())
  .then(data => console.log(data));
```

---

### Common Issues

- **Python Version Error**: Upgrade to Python 3.11+
- **Pip Installation Fails**: Install pip via your OS package manager
- **Permission Denied**: Use `pip install --user ...`
- **Port Already in Use**: Change the port in `main.py`
- **Module Import Errors**: Ensure all dependencies are installed
- **Database Permission Issues**: Check directory permissions

### Debugging

- Enable debug logging:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```

---

## Testing & Validation

- Test server:
  ```bash
  curl http://localhost:5000/
  ```
- Test proxy endpoint:
  ```bash
  curl -X POST http://localhost:5000/proxy/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "test", "messages": [{"role": "user", "content": "Hello"}]}'
  ```
- Access dashboard:
  - Open `http://localhost:5000/dashboard` in your browser

---

## Acknowledgments

- FastAPI, SQLAlchemy, Jinja2, httpx, Bootstrap, Chart.js, Font Awesome

---

**For full details, see the source code and documentation.**

---

## 📚 More Documentation

For the most detailed and up-to-date documentation, visit the `documentation` folder in this project. There you will find:
- Full API reference
- Advanced deployment guides
- Installation instructions for all platforms
- Contribution guidelines
- Troubleshooting and FAQ

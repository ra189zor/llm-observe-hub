from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from datetime import datetime, timedelta, timezone
import httpx
import json
import asyncio
import csv
import io
import statistics
from typing import Dict, Any, List, AsyncGenerator
import os


from dotenv import load_dotenv
load_dotenv()
from database import LLMRequestLog, AlertRule, AlertEvent, CostSettings, Budget, ModelComparison, OptimizationSuggestion, get_db, init_database


# Use FastAPI lifespan event for startup logic
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    db = next(get_db())
    try:
        existing_rules = db.query(AlertRule).count()
        if existing_rules == 0:
            default_rules = [
                AlertRule(name="High Latency Alert", metric="latency", threshold=5000.0, operator="gt"),
                AlertRule(name="Low Tokens/Sec Alert", metric="tokens_per_second", threshold=10.0, operator="lt"),
                AlertRule(name="High Error Rate Alert", metric="error_rate", threshold=10.0, operator="gt")
            ]
            for rule in default_rules:
                db.add(rule)
            db.commit()
    finally:
        db.close()
    yield

app = FastAPI(title="LLM-Lens", description="Observability tool for local LLMs", lifespan=lifespan)


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

## ...existing code...

# Default local LLM API URLs - can be configured via environment variables
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
LMSTUDIO_URL = os.getenv("LMSTUDIO_URL", "http://localhost:1234/v1/chat/completions")
DEFAULT_LLM_URL = os.getenv("DEFAULT_LLM_URL", LMSTUDIO_URL)

async def calculate_performance_score(latency_ms: int, tokens_per_second: float, error_occurred: bool) -> float:
    """Calculate a performance score based on latency, throughput, and error status."""
    if error_occurred:
        return 0.0
    
    # Normalize latency (lower is better, target: under 2000ms)
    latency_score = max(0, 100 - (latency_ms / 20))
    
    # Normalize tokens per second (higher is better, target: over 20 tokens/sec)
    throughput_score = min(100, (tokens_per_second or 0) * 5)
    
    # Weighted average
    return round((latency_score * 0.6 + throughput_score * 0.4), 2)

async def check_alert_rules(db: Session, log_entry: LLMRequestLog):
    """Check if any alert rules are triggered and create alert events."""
    active_rules = db.query(AlertRule).filter(AlertRule.is_active == True).all()
    
    for rule in active_rules:
        metric_value = None
        # Use .threshold as float, not as SQLAlchemy column
        threshold = float(getattr(rule, 'threshold', 0))
        operator = getattr(rule, 'operator', '')
        metric = getattr(rule, 'metric', '')
        if metric == "latency":
            metric_value = float(getattr(log_entry, "latency_ms", 0) or 0)
        elif metric == "tokens_per_second":
            metric_value = float(getattr(log_entry, "tokens_per_second", 0) or 0)
        elif metric == "error_rate":
            recent_logs = db.query(LLMRequestLog).order_by(desc(LLMRequestLog.start_time)).limit(10).all()
            if recent_logs:
                error_count = sum(1 for log in recent_logs if getattr(log, "error_message", None))
                metric_value = (error_count / len(recent_logs)) * 100
            else:
                metric_value = 0.0
        if metric_value is not None:
            triggered = False
            if operator == "gt" and metric_value > threshold:
                triggered = True
            elif operator == "lt" and metric_value < threshold:
                triggered = True
            elif operator == "eq" and metric_value == threshold:
                triggered = True
            if triggered:
                alert_event = AlertEvent(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    metric_value=metric_value,
                    threshold=threshold,
                    message=f"{rule.name}: {metric} ({metric_value}) {operator} {threshold}"
                )
                db.add(alert_event)

async def stream_llm_response(
    client: httpx.AsyncClient,
    url: str,
    request_data: Dict[str, Any],
    db: Session,
    log_start_info: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """Handle streaming LLM responses with real-time metrics collection."""
    first_token_time = None
    response_chunks: List[str] = []
    tokens_count = 0
    
    try:
        async with client.stream("POST", url, json=request_data) as response:
            response.raise_for_status()
            
            async for chunk in response.aiter_text():
                if chunk.strip():
                    if first_token_time is None:
                        first_token_time = datetime.now(timezone.utc)
                    
                    response_chunks.append(chunk)
                    tokens_count += len(chunk.split())  # Rough token estimate
                    yield chunk
    
    except Exception as e:
        error_chunk = f"data: {json.dumps({'error': str(e)})}\n\n"
        yield error_chunk
        
        # Log error to database
        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - log_start_info['start_time']).total_seconds() * 1000)
        
        log_entry = LLMRequestLog(
            model_name=log_start_info['model_name'],
            start_time=log_start_info['start_time'],
            end_time=end_time,
            latency_ms=latency_ms,
            input_text=log_start_info['input_text'],
            output_text="",
            error_message=str(e),
            is_streaming=True,
            request_metadata=log_start_info.get('metadata', {})
        )
        log_entry.performance_score = await calculate_performance_score(latency_ms, 0, True)
        
        db.add(log_entry)
        db.commit()
        
        await check_alert_rules(db, log_entry)
        db.commit()
        return
    
    # Log successful streaming response
    end_time = datetime.now(timezone.utc)
    latency_ms = int((end_time - log_start_info['start_time']).total_seconds() * 1000)
    time_to_first_token = int((first_token_time - log_start_info['start_time']).total_seconds() * 1000) if first_token_time else None
    
    # Calculate tokens per second
    duration_seconds = (end_time - log_start_info['start_time']).total_seconds()
    tokens_per_second = tokens_count / duration_seconds if duration_seconds > 0 else 0
    
    output_text = "".join(response_chunks)
    
    log_entry = LLMRequestLog(
        model_name=log_start_info['model_name'],
        start_time=log_start_info['start_time'],
        end_time=end_time,
        latency_ms=latency_ms,
        input_text=log_start_info['input_text'],
        output_text=output_text,
        is_streaming=True,
        time_to_first_token_ms=time_to_first_token,
        tokens_per_second=tokens_per_second,
        temperature=log_start_info.get('metadata', {}).get('temperature'),
        max_tokens=log_start_info.get('metadata', {}).get('max_tokens'),
        request_metadata=log_start_info.get('metadata', {}),
        completion_tokens=tokens_count,
        total_tokens=tokens_count + log_start_info.get('prompt_tokens', 0),
        performance_score=await calculate_performance_score(latency_ms, tokens_per_second, False)
    )
    
    db.add(log_entry)
    db.commit()
    
    await check_alert_rules(db, log_entry)
    db.commit()

@app.post("/proxy/v1/chat/completions")
async def proxy_chat_completions(request: Request, db: Session = Depends(get_db)):
    """
    Enhanced proxy endpoint with streaming support and advanced metrics collection.
    """
    start_time = datetime.now(timezone.utc)
    
    try:
        request_body = await request.json()
        model_name = request_body.get("model", "unknown")
        is_streaming = request_body.get("stream", False)
        
        # Extract input text and metadata
        messages = request_body.get("messages", [])
        input_text = " ".join([msg.get("content", "") for msg in messages if msg.get("role") == "user"])
        
        metadata = {
            "temperature": request_body.get("temperature"),
            "max_tokens": request_body.get("max_tokens"),
            "top_p": request_body.get("top_p"),
            "frequency_penalty": request_body.get("frequency_penalty"),
            "presence_penalty": request_body.get("presence_penalty")
        }
        
        # Estimate prompt tokens (rough calculation)
        prompt_tokens = sum(len(msg.get("content", "").split()) for msg in messages)
        
        llm_url = DEFAULT_LLM_URL
        
        # Prepare log start info for streaming
        log_start_info = {
            "start_time": start_time,
            "model_name": model_name,
            "input_text": input_text,
            "metadata": metadata,
            "prompt_tokens": prompt_tokens
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            if is_streaming:
                # Handle streaming responses
                if "localhost:11434" in llm_url or "ollama" in llm_url.lower():
                    ollama_request = {
                        "model": model_name,
                        "messages": messages,
                        "stream": True
                    }
                    return StreamingResponse(
                        stream_llm_response(client, llm_url, ollama_request, db, log_start_info),
                        media_type="text/plain"
                    )
                else:
                    return StreamingResponse(
                        stream_llm_response(client, llm_url, request_body, db, log_start_info),
                        media_type="text/plain"
                    )
            else:
                # Handle non-streaming responses with enhanced metrics
                try:
                    if "localhost:11434" in llm_url or "ollama" in llm_url.lower():
                        ollama_request = {
                            "model": model_name,
                            "messages": messages,
                            "stream": False
                        }
                        response = await client.post(llm_url, json=ollama_request)
                    else:
                        response = await client.post(llm_url, json=request_body)
                    
                    response.raise_for_status()
                    response_data = response.json()
                    
                    # Enhanced metrics collection
                    end_time = datetime.now(timezone.utc)
                    latency_ms = int((end_time - start_time).total_seconds() * 1000)
                    
                    # Extract response data and calculate tokens per second
                    output_text = ""
                    completion_tokens = None
                    total_tokens = None
                    
                    if "choices" in response_data and response_data["choices"]:
                        choice = response_data["choices"][0]
                        if "message" in choice and "content" in choice["message"]:
                            output_text = choice["message"]["content"]
                    
                    if "usage" in response_data:
                        usage = response_data["usage"]
                        prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
                        completion_tokens = usage.get("completion_tokens")
                        total_tokens = usage.get("total_tokens")
                    
                    # Calculate tokens per second for non-streaming
                    duration_seconds = (end_time - start_time).total_seconds()
                    tokens_per_second = (completion_tokens or 0) / duration_seconds if duration_seconds > 0 else 0
                    
                    # Create enhanced log entry
                    log_entry = LLMRequestLog(
                        model_name=model_name,
                        start_time=start_time,
                        end_time=end_time,
                        latency_ms=latency_ms,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        input_text=input_text,
                        output_text=output_text,
                        is_streaming=False,
                        tokens_per_second=tokens_per_second,
                        temperature=metadata.get('temperature'),
                        max_tokens=metadata.get('max_tokens'),
                        request_metadata=metadata,
                        performance_score=await calculate_performance_score(latency_ms, tokens_per_second, False)
                    )
                    
                    db.add(log_entry)
                    db.commit()
                    
                    # Check alert rules
                    await check_alert_rules(db, log_entry)
                    db.commit()
                    
                    return response_data
                    
                except Exception as e:
                    # Enhanced error handling with metrics
                    end_time = datetime.now(timezone.utc)
                    latency_ms = int((end_time - start_time).total_seconds() * 1000)
                    error_msg = str(e)
                    
                    log_entry = LLMRequestLog(
                        model_name=model_name,
                        start_time=start_time,
                        end_time=end_time,
                        latency_ms=latency_ms,
                        input_text=input_text,
                        output_text="",
                        error_message=error_msg,
                        is_streaming=False,
                        request_metadata=metadata,
                        performance_score=await calculate_performance_score(latency_ms, 0, True)
                    )
                    
                    db.add(log_entry)
                    db.commit()
                    
                    await check_alert_rules(db, log_entry)
                    db.commit()
                    
                    if isinstance(e, httpx.RequestError):
                        raise HTTPException(status_code=503, detail=f"Connection error to local LLM: {error_msg}")
                    elif isinstance(e, httpx.HTTPStatusError):
                        raise HTTPException(status_code=e.response.status_code, detail=f"LLM API error: {error_msg}")
                    else:
                        raise HTTPException(status_code=500, detail=f"Unexpected error: {error_msg}")
                        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        # Handle any other unexpected errors
        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        error_msg = f"Unexpected error: {str(e)}"
        
        try:
            log_entry = LLMRequestLog(
                model_name="unknown",
                start_time=start_time,
                end_time=end_time,
                latency_ms=latency_ms,
                input_text="",
                output_text="",
                error_message=error_msg,
                performance_score=0.0
            )
            db.add(log_entry)
            db.commit()
        except Exception:
            pass
            
        raise HTTPException(status_code=500, detail=error_msg)

# Advanced Analytics API Endpoints
@app.get("/api/analytics/performance")
async def get_performance_analytics(db: Session = Depends(get_db)):
    """Get advanced performance analytics and insights."""
    try:
        # Calculate various performance metrics
        recent_logs = db.query(LLMRequestLog).filter(
            LLMRequestLog.start_time >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).all()
        
        if not recent_logs:
            return {"message": "No data available for the last 24 hours"}
        
        # Performance statistics
        latencies = [log.latency_ms for log in recent_logs if log.latency_ms is not None]
        tokens_per_sec = [log.tokens_per_second for log in recent_logs if log.tokens_per_second is not None]
        performance_scores = [log.performance_score for log in recent_logs if log.performance_score is not None]
        
        analytics = {
            "summary": {
                "total_requests": len(recent_logs),
                "success_rate": (len([log for log in recent_logs if not log.error_message]) / len(recent_logs)) * 100,
                "streaming_requests": len([log for log in recent_logs if log.is_streaming]),
                "avg_performance_score": statistics.mean(performance_scores) if performance_scores else 0
            },
            "latency_stats": {
                "mean": statistics.mean(latencies) if latencies else 0,
                "median": statistics.median(latencies) if latencies else 0,
                "p95": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
                "p99": sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
            },
            "throughput_stats": {
                "mean_tokens_per_sec": statistics.mean(tokens_per_sec) if tokens_per_sec else 0,
                "max_tokens_per_sec": max(tokens_per_sec) if tokens_per_sec else 0,
                "min_tokens_per_sec": min(tokens_per_sec) if tokens_per_sec else 0
            },
            "model_performance": {}
        }
        
        # Per-model analytics
        models = set(log.model_name for log in recent_logs)
        for model in models:
            model_logs = [log for log in recent_logs if log.model_name == model]
            model_latencies = [log.latency_ms for log in model_logs if log.latency_ms is not None]
            model_scores = [log.performance_score for log in model_logs if log.performance_score is not None]
            
            analytics["model_performance"][model] = {
                "request_count": len(model_logs),
                "avg_latency": statistics.mean(model_latencies) if model_latencies else 0,
                "avg_performance_score": statistics.mean(model_scores) if model_scores else 0,
                "error_rate": (len([log for log in model_logs if log.error_message]) / len(model_logs)) * 100
            }
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics calculation failed: {str(e)}")

# Alert Management API Endpoints
@app.get("/api/alerts/rules")
async def get_alert_rules(db: Session = Depends(get_db)):
    """Get all alert rules."""
    rules = db.query(AlertRule).all()
    return [
        {
            "id": rule.id,
            "name": rule.name,
            "metric": rule.metric,
            "threshold": rule.threshold,
            "operator": rule.operator,
            "is_active": rule.is_active,
            "created_at": rule.created_at.isoformat()
        }
        for rule in rules
    ]

@app.post("/api/alerts/rules")
async def create_alert_rule(rule_data: dict, db: Session = Depends(get_db)):
    """Create a new alert rule."""
    try:
        rule = AlertRule(
            name=rule_data["name"],
            metric=rule_data["metric"],
            threshold=float(rule_data["threshold"]),
            operator=rule_data["operator"],
            is_active=rule_data.get("is_active", True)
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        return {
            "id": rule.id,
            "message": "Alert rule created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create alert rule: {str(e)}")

@app.get("/api/alerts/events")
async def get_alert_events(db: Session = Depends(get_db)):
    """Get recent alert events."""
    events = db.query(AlertEvent).order_by(desc(AlertEvent.triggered_at)).limit(50).all()
    return [
        {
            "id": event.id,
            "rule_name": event.rule_name,
            "metric_value": event.metric_value,
            "threshold": event.threshold,
            "message": event.message,
            "triggered_at": event.triggered_at.isoformat(),
            "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None
        }
        for event in events
    ]

# Cost Tracking Endpoints
@app.get("/api/cost-settings")
async def get_cost_settings(db: Session = Depends(get_db)):
    """Get all cost settings for different models."""
    cost_settings = db.query(CostSettings).all()
    return cost_settings

@app.post("/api/cost-settings")
async def create_cost_setting(
    model_name: str,
    cost_per_1k_input_tokens: float = 0.0,
    cost_per_1k_output_tokens: float = 0.0,
    electricity_cost_per_hour: float = 0.0,
    db: Session = Depends(get_db)
):
    """Create or update cost settings for a model."""
    existing = db.query(CostSettings).filter(CostSettings.model_name == model_name).first()
    
    if existing:
        existing.cost_per_1k_input_tokens = cost_per_1k_input_tokens
        existing.cost_per_1k_output_tokens = cost_per_1k_output_tokens
        existing.electricity_cost_per_hour = electricity_cost_per_hour
        existing.updated_at = datetime.utcnow()
        db.commit()
        return existing
    else:
        new_setting = CostSettings(
            model_name=model_name,
            cost_per_1k_input_tokens=cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=cost_per_1k_output_tokens,
            electricity_cost_per_hour=electricity_cost_per_hour
        )
        db.add(new_setting)
        db.commit()
        return new_setting

@app.get("/api/budgets")
async def get_budgets(db: Session = Depends(get_db)):
    """Get all budget configurations."""
    budgets = db.query(Budget).all()
    return budgets

@app.post("/api/budgets")
async def create_budget(
    name: str,
    budget_type: str,
    amount: float,
    db: Session = Depends(get_db)
):
    """Create a new budget."""
    new_budget = Budget(
        name=name,
        budget_type=budget_type,
        amount=amount
    )
    db.add(new_budget)
    db.commit()
    return new_budget

@app.get("/api/cost-analysis")
async def get_cost_analysis(hours: int = 24, db: Session = Depends(get_db)):
    """Get cost analysis for the specified time period."""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all logs in the time period
    logs = db.query(LLMRequestLog).filter(LLMRequestLog.start_time >= cutoff_time).all()
    
    cost_breakdown = {}
    total_cost = 0.0
    
    for log in logs:
        model_name = log.model_name
        if model_name not in cost_breakdown:
            cost_breakdown[model_name] = {
                "requests": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0,
                "avg_latency": 0.0
            }
        
        # Calculate cost for this request
        cost_settings = db.query(CostSettings).filter(CostSettings.model_name == model_name).first()
        request_cost = 0.0
        
        if cost_settings and log.prompt_tokens and log.completion_tokens:
            input_cost = (log.prompt_tokens / 1000) * cost_settings.cost_per_1k_input_tokens
            output_cost = (log.completion_tokens / 1000) * cost_settings.cost_per_1k_output_tokens
            
            if cost_settings.electricity_cost_per_hour > 0:
                duration_hours = log.latency_ms / (1000 * 60 * 60)
                electricity_cost = duration_hours * cost_settings.electricity_cost_per_hour
                request_cost = input_cost + output_cost + electricity_cost
            else:
                request_cost = input_cost + output_cost
        
        cost_breakdown[model_name]["requests"] += 1
        cost_breakdown[model_name]["total_tokens"] += log.total_tokens or 0
        cost_breakdown[model_name]["estimated_cost"] += request_cost
        cost_breakdown[model_name]["avg_latency"] += log.latency_ms
        total_cost += request_cost
    
    # Calculate averages
    for model_data in cost_breakdown.values():
        if model_data["requests"] > 0:
            model_data["avg_latency"] = model_data["avg_latency"] / model_data["requests"]
    
    return {
        "total_cost": round(total_cost, 4),
        "cost_breakdown": cost_breakdown,
        "time_period_hours": hours
    }

# Model Comparison Endpoints
@app.get("/api/model-comparisons")
async def get_model_comparisons(db: Session = Depends(get_db)):
    """Get all model comparison results."""
    comparisons = db.query(ModelComparison).order_by(desc(ModelComparison.created_at)).all()
    return comparisons

@app.post("/api/model-comparisons")
async def create_model_comparison(
    comparison_name: str,
    model_a: str,
    model_b: str,
    test_prompt: str,
    db: Session = Depends(get_db)
):
    """Create a new model comparison test."""
    new_comparison = ModelComparison(
        comparison_name=comparison_name,
        model_a=model_a,
        model_b=model_b,
        test_prompt=test_prompt
    )
    db.add(new_comparison)
    db.commit()
    return new_comparison

@app.get("/api/model-performance")
async def get_model_performance(hours: int = 24, db: Session = Depends(get_db)):
    """Get performance comparison between all models."""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get performance metrics grouped by model
    performance_data = db.query(
        LLMRequestLog.model_name,
        func.avg(LLMRequestLog.latency_ms).label('avg_latency'),
        func.avg(LLMRequestLog.tokens_per_second).label('avg_throughput'),
        func.avg(LLMRequestLog.performance_score).label('avg_performance'),
        func.count(LLMRequestLog.id).label('request_count'),
        func.sum(LLMRequestLog.total_tokens).label('total_tokens')
    ).filter(
        LLMRequestLog.start_time >= cutoff_time
    ).group_by(LLMRequestLog.model_name).all()
    
    models = []
    for row in performance_data:
        model_info = {
            "model_name": row.model_name,
            "avg_latency": round(row.avg_latency or 0, 2),
            "avg_throughput": round(row.avg_throughput or 0, 2),
            "avg_performance": round(row.avg_performance or 0, 3),
            "request_count": row.request_count,
            "total_tokens": row.total_tokens or 0
        }
        models.append(model_info)
    
    # Sort by performance score
    models.sort(key=lambda x: x['avg_performance'], reverse=True)
    
    return {
        "models": models,
        "time_period_hours": hours,
        "recommendation": models[0]["model_name"] if models else None
    }

# Performance Optimization Endpoints
@app.get("/api/optimization-suggestions")
async def get_optimization_suggestions(db: Session = Depends(get_db)):
    """Get AI-powered optimization suggestions."""
    suggestions = db.query(OptimizationSuggestion).filter(
        OptimizationSuggestion.is_implemented == False
    ).order_by(desc(OptimizationSuggestion.created_at)).all()
    return suggestions

@app.post("/api/optimization-suggestions/generate")
async def generate_optimization_suggestions(db: Session = Depends(get_db)):
    """Generate AI-powered optimization suggestions based on current performance data."""
    
    # Get recent performance data
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    recent_logs = db.query(LLMRequestLog).filter(LLMRequestLog.start_time >= cutoff_time).all()
    
    if not recent_logs:
        return {"message": "No recent data available for analysis"}
    
    # Analyze performance patterns and generate suggestions
    suggestions = []
    
    # Performance analysis
    avg_latency = statistics.mean([log.latency_ms for log in recent_logs])
    high_latency_logs = [log for log in recent_logs if log.latency_ms > avg_latency * 1.5]
    
    if len(high_latency_logs) > len(recent_logs) * 0.3:  # More than 30% high latency
        suggestions.append({
            "suggestion_type": "performance",
            "model_name": "general",
            "title": "High Latency Detected",
            "description": f"Average latency is {avg_latency:.0f}ms with {len(high_latency_logs)} requests exceeding 150% of average. Consider optimizing model parameters or upgrading hardware.",
            "priority": "high",
            "potential_improvement": "25-40% latency reduction"
        })
    
    # Parameter optimization suggestions
    model_performance = {}
    for log in recent_logs:
        if log.model_name not in model_performance:
            model_performance[log.model_name] = {
                "latencies": [],
                "temperatures": [],
                "max_tokens": [],
                "performance_scores": []
            }
        
        model_performance[log.model_name]["latencies"].append(log.latency_ms)
        if log.temperature:
            model_performance[log.model_name]["temperatures"].append(log.temperature)
        if log.max_tokens:
            model_performance[log.model_name]["max_tokens"].append(log.max_tokens)
        if log.performance_score:
            model_performance[log.model_name]["performance_scores"].append(log.performance_score)
    
    for model_name, data in model_performance.items():
        avg_temp = statistics.mean(data["temperatures"]) if data["temperatures"] else None
        avg_perf = statistics.mean(data["performance_scores"]) if data["performance_scores"] else None
        
        if avg_temp and avg_temp > 0.8:
            suggestions.append({
                "suggestion_type": "parameter",
                "model_name": model_name,
                "title": "High Temperature Setting",
                "description": f"Model {model_name} is using average temperature of {avg_temp:.2f}. Consider lowering to 0.3-0.7 for more consistent responses.",
                "priority": "medium",
                "potential_improvement": "10-20% consistency improvement"
            })
        
        if avg_perf and avg_perf < 0.7:
            suggestions.append({
                "suggestion_type": "performance",
                "model_name": model_name,
                "title": "Low Performance Score",
                "description": f"Model {model_name} has average performance score of {avg_perf:.3f}. Consider parameter tuning or model replacement.",
                "priority": "high",
                "potential_improvement": "30-50% performance boost"
            })
    
    # Hardware optimization suggestions
    total_requests = len(recent_logs)
    streaming_requests = len([log for log in recent_logs if log.is_streaming])
    
    if streaming_requests > 0:
        avg_ttft = statistics.mean([log.time_to_first_token_ms for log in recent_logs if log.time_to_first_token_ms])
        if avg_ttft > 1000:  # > 1 second TTFT
            suggestions.append({
                "suggestion_type": "hardware",
                "model_name": "general",
                "title": "Slow Time to First Token",
                "description": f"Average TTFT is {avg_ttft:.0f}ms. Consider upgrading to faster SSD or increasing RAM allocation.",
                "priority": "medium",
                "potential_improvement": "50-70% TTFT improvement"
            })
    
    # Token optimization
    high_token_requests = [log for log in recent_logs if log.total_tokens and log.total_tokens > 500]
    if len(high_token_requests) > total_requests * 0.4:
        suggestions.append({
            "suggestion_type": "parameter",
            "model_name": "general",
            "title": "High Token Usage",
            "description": f"{len(high_token_requests)} requests use >500 tokens. Consider implementing response truncation or prompt optimization.",
            "priority": "medium",
            "potential_improvement": "20-30% cost reduction"
        })
    
    # Save suggestions to database
    for suggestion_data in suggestions:
        existing = db.query(OptimizationSuggestion).filter(
            OptimizationSuggestion.title == suggestion_data["title"],
            OptimizationSuggestion.model_name == suggestion_data["model_name"]
        ).first()
        
        if not existing:
            suggestion = OptimizationSuggestion(**suggestion_data)
            db.add(suggestion)
    
    db.commit()
    
    return {
        "message": f"Generated {len(suggestions)} optimization suggestions",
        "suggestions": suggestions
    }

@app.post("/api/optimization-suggestions/{suggestion_id}/implement")
async def implement_suggestion(suggestion_id: int, db: Session = Depends(get_db)):
    """Mark an optimization suggestion as implemented."""
    suggestion = db.query(OptimizationSuggestion).filter(OptimizationSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    suggestion.is_implemented = True
    suggestion.implemented_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Suggestion marked as implemented"}

# Export functionality
@app.get("/api/export/csv")
async def export_logs_csv(
    hours: int = 24,
    model: str = None,
    db: Session = Depends(get_db)
):
    """Export request logs as CSV."""
    try:
        # Build query
        query = db.query(LLMRequestLog).filter(
            LLMRequestLog.start_time >= datetime.utcnow() - timedelta(hours=hours)
        )
        
        if model:
            query = query.filter(LLMRequestLog.model_name == model)
        
        logs = query.order_by(desc(LLMRequestLog.start_time)).all()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'timestamp', 'model_name', 'latency_ms', 'tokens_per_second',
            'prompt_tokens', 'completion_tokens', 'total_tokens',
            'is_streaming', 'performance_score', 'temperature',
            'max_tokens', 'error_message', 'input_text_preview', 'output_text_preview'
        ])
        
        # Data rows
        for log in logs:
            writer.writerow([
                log.start_time.isoformat(),
                log.model_name,
                log.latency_ms,
                log.tokens_per_second,
                log.prompt_tokens,
                log.completion_tokens,
                log.total_tokens,
                log.is_streaming,
                log.performance_score,
                log.temperature,
                log.max_tokens,
                log.error_message,
                log.input_text[:100] + "..." if len(log.input_text) > 100 else log.input_text,
                log.output_text[:100] + "..." if len(log.output_text) > 100 else log.output_text
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=llm_lens_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/export/json")
async def export_logs_json(
    hours: int = 24,
    model: str = None,
    db: Session = Depends(get_db)
):
    """Export request logs as JSON."""
    try:
        query = db.query(LLMRequestLog).filter(
            LLMRequestLog.start_time >= datetime.utcnow() - timedelta(hours=hours)
        )
        
        if model:
            query = query.filter(LLMRequestLog.model_name == model)
        
        logs = query.order_by(desc(LLMRequestLog.start_time)).all()
        
        export_data = []
        for log in logs:
            export_data.append({
                "id": log.id,
                "timestamp": log.start_time.isoformat(),
                "model_name": log.model_name,
                "latency_ms": log.latency_ms,
                "tokens_per_second": log.tokens_per_second,
                "prompt_tokens": log.prompt_tokens,
                "completion_tokens": log.completion_tokens,
                "total_tokens": log.total_tokens,
                "is_streaming": log.is_streaming,
                "time_to_first_token_ms": log.time_to_first_token_ms,
                "performance_score": log.performance_score,
                "temperature": log.temperature,
                "max_tokens": log.max_tokens,
                "request_metadata": log.request_metadata,
                "error_message": log.error_message,
                "input_text": log.input_text,
                "output_text": log.output_text
            })
        
        return JSONResponse(
            content=export_data,
            headers={"Content-Disposition": f"attachment; filename=llm_lens_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# Enhanced dashboard endpoint with new analytics
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page with feature overview."""
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def enhanced_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Enhanced dashboard with advanced analytics, alerts, and performance insights.
    """
    # Fetch recent logs with enhanced fields
    recent_logs = db.query(LLMRequestLog).order_by(desc(LLMRequestLog.start_time)).limit(100).all()
    
    # Enhanced aggregations for charts
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    
    # Advanced latency analysis with percentiles
    latency_data = []
    performance_data = []
    streaming_data = []
    
    for i in range(24):
        hour_start = datetime.utcnow() - timedelta(hours=i+1)
        hour_end = datetime.utcnow() - timedelta(hours=i)
        
        hour_logs = db.query(LLMRequestLog).filter(
            LLMRequestLog.start_time >= hour_start,
            LLMRequestLog.start_time < hour_end
        ).all()
        
        if hour_logs:
            latencies = [log.latency_ms for log in hour_logs if log.latency_ms]
            performance_scores = [log.performance_score for log in hour_logs if log.performance_score]
            streaming_count = len([log for log in hour_logs if log.is_streaming])
            
            avg_latency = statistics.mean(latencies) if latencies else 0
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
            avg_performance = statistics.mean(performance_scores) if performance_scores else 0
            
            latency_data.append({
                "hour": hour_start.strftime("%H:00"),
                "avg_latency": round(avg_latency, 2),
                "p95_latency": round(p95_latency, 2)
            })
            
            performance_data.append({
                "hour": hour_start.strftime("%H:00"),
                "avg_score": round(avg_performance, 2)
            })
            
            streaming_data.append({
                "hour": hour_start.strftime("%H:00"),
                "streaming_requests": streaming_count,
                "total_requests": len(hour_logs)
            })
        else:
            latency_data.append({"hour": hour_start.strftime("%H:00"), "avg_latency": 0, "p95_latency": 0})
            performance_data.append({"hour": hour_start.strftime("%H:00"), "avg_score": 0})
            streaming_data.append({"hour": hour_start.strftime("%H:00"), "streaming_requests": 0, "total_requests": 0})
    
    latency_data.reverse()
    performance_data.reverse()
    streaming_data.reverse()
    
    # Enhanced token usage by model with throughput
    token_data = db.query(
        LLMRequestLog.model_name,
        func.sum(LLMRequestLog.total_tokens).label("total_tokens"),
        func.avg(LLMRequestLog.tokens_per_second).label("avg_throughput"),
        func.count(LLMRequestLog.id).label("request_count")
    ).filter(
        LLMRequestLog.total_tokens.isnot(None),
        LLMRequestLog.start_time >= one_day_ago
    ).group_by(LLMRequestLog.model_name).all()
    
    token_usage = [{
        "model": row.model_name,
        "tokens": row.total_tokens or 0,
        "avg_throughput": round(row.avg_throughput or 0, 2),
        "request_count": row.request_count
    } for row in token_data]
    
    # Recent alert events
    recent_alerts = db.query(AlertEvent).order_by(desc(AlertEvent.triggered_at)).limit(10).all()
    alert_events = [{
        "id": alert.id,
        "rule_name": alert.rule_name,
        "message": alert.message,
        "triggered_at": alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S") if alert.triggered_at else "Unknown",
        "resolved": alert.resolved_at is not None
    } for alert in recent_alerts]
    
    # Format enhanced logs for display
    formatted_logs = []
    for log in recent_logs:
        formatted_logs.append({
            "id": log.id,
            "model_name": log.model_name,
            "start_time": log.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "latency_ms": log.latency_ms,
            "total_tokens": log.total_tokens or 0,
            "tokens_per_second": round(log.tokens_per_second or 0, 2),
            "performance_score": log.performance_score or 0,
            "is_streaming": log.is_streaming,
            "time_to_first_token_ms": log.time_to_first_token_ms,
            "status": "Error" if log.error_message else "Success",
            "input_text": log.input_text[:100] + "..." if len(log.input_text) > 100 else log.input_text,
            "output_text": log.output_text[:100] + "..." if len(log.output_text) > 100 else log.output_text,
            "full_input": log.input_text,
            "full_output": log.output_text,
            "error_message": log.error_message,
            "temperature": log.temperature,
            "max_tokens": log.max_tokens
        })
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent_logs": formatted_logs,
        "latency_data": latency_data,
        "performance_data": performance_data,
        "streaming_data": streaming_data,
        "token_usage": token_usage,
        "alert_events": alert_events
    })

@app.get("/api/logs/{log_id}")
async def get_enhanced_log_details(log_id: int, db: Session = Depends(get_db)):
    """
    API endpoint to get detailed log information with enhanced metrics.
    """
    log = db.query(LLMRequestLog).filter(LLMRequestLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    
    return {
        "id": log.id,
        "model_name": log.model_name,
        "start_time": log.start_time.isoformat(),
        "end_time": log.end_time.isoformat(),
        "latency_ms": log.latency_ms,
        "prompt_tokens": log.prompt_tokens,
        "completion_tokens": log.completion_tokens,
        "total_tokens": log.total_tokens,
        "tokens_per_second": log.tokens_per_second,
        "time_to_first_token_ms": log.time_to_first_token_ms,
        "performance_score": log.performance_score,
        "is_streaming": log.is_streaming,
        "temperature": log.temperature,
        "max_tokens": log.max_tokens,
        "request_metadata": log.request_metadata,
        "input_text": log.input_text,
        "output_text": log.output_text,
        "error_message": log.error_message
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

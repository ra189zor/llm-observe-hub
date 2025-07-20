
# Troubleshooting & FAQ

This guide helps you resolve common issues and answers frequently asked questions about LLM-Lens.

## 🔧 Quick Troubleshooting

### Server Won't Start

**Issue**: Server fails to start or crashes immediately

**Common Causes & Solutions**:

1. **Port Already in Use**
   ```
   Error: [Errno 98] Address already in use
   ```
   **Solution**: Change the port in `main.py`:
   ```python
   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=5001)  # Changed from 5000
   ```

2. **Missing Dependencies**
   ```
   ModuleNotFoundError: No module named 'fastapi'
   ```
   **Solution**: Install dependencies:
   ```bash
   pip install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart
   ```

3. **Database Permission Issues**
   ```
   sqlite3.OperationalError: unable to open database file
   ```
   **Solution**: Check file permissions:
   ```bash
   chmod 755 .
   touch llm_lens.db
   chmod 664 llm_lens.db
   ```

### Connection Issues

**Issue**: Cannot connect to local LLM

**Symptoms**:
- "Connection error to local LLM" messages
- Proxy requests timing out
- Dashboard shows no data

**Solutions**:

1. **Verify LLM is Running**
   ```bash
   # For LM Studio
   curl http://localhost:1234/v1/models
   
   # For Ollama
   curl http://localhost:11434/api/tags
   ```

2. **Check LLM URL Configuration**
   ```bash
   # Set correct environment variable
   export DEFAULT_LLM_URL="http://localhost:1234/v1/chat/completions"
   ```

3. **Test LLM Connection Manually**
   ```bash
   curl -X POST http://localhost:1234/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"your-model","messages":[{"role":"user","content":"Hello"}]}'
   ```

### Dashboard Issues

**Issue**: Dashboard loads but shows no data

**Possible Causes**:

1. **No Requests Made Through Proxy**
   - Make sure your applications are using the proxy endpoint
   - Test with: `http://localhost:5000/proxy/v1/chat/completions`

2. **Database Empty**
   - Check if database file exists: `ls -la llm_lens.db`
   - Verify database has data:
   ```python
   from database import get_db, LLMRequestLog
   db = next(get_db())
   print(db.query(LLMRequestLog).count())
   ```

3. **Time Range Issues**
   - Dashboard shows last 24 hours by default
   - Make recent test requests to see data

## 🐛 Common Error Messages

### 1. "Connection refused"

**Full Error**: `httpx.ConnectError: [Errno 111] Connection refused`

**Cause**: LLM service is not running or wrong URL

**Solution**:
- Start your LLM service (LM Studio, Ollama, etc.)
- Verify the correct port and URL
- Check firewall settings

### 2. "No module named 'fastapi'"

**Cause**: Dependencies not installed

**Solution**:
```bash
pip install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart
```

### 3. "Database is locked"

**Full Error**: `sqlite3.OperationalError: database is locked`

**Cause**: Multiple instances accessing database

**Solution**:
- Stop all running instances
- Remove lock file: `rm llm_lens.db-wal llm_lens.db-shm` (if they exist)
- Restart application

### 4. "Internal Server Error"

**Cause**: Various backend issues

**Solution**:
1. Check console logs for specific error
2. Enable debug mode in `main.py`:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```
3. Check database integrity
4. Verify all environment variables

### 5. "Streaming not working"

**Symptoms**: Streaming responses don't appear in real-time

**Solutions**:
1. Verify LLM supports streaming
2. Check that `stream: true` is in your request
3. Test streaming directly with LLM:
   ```bash
   curl -X POST http://localhost:1234/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"your-model","messages":[{"role":"user","content":"Hello"}],"stream":true}'
   ```

## ❓ Frequently Asked Questions

### General Usage

**Q: How do I configure LLM-Lens for my specific LLM setup?**

A: Set the environment variable for your LLM URL:
```bash
# For LM Studio
export DEFAULT_LLM_URL="http://localhost:1234/v1/chat/completions"

# For Ollama
export DEFAULT_LLM_URL="http://localhost:11434/api/chat"

# For custom setup
export DEFAULT_LLM_URL="http://your-llm-host:port/api/endpoint"
```

**Q: Can I use LLM-Lens with multiple LLMs?**

A: Currently, LLM-Lens proxies to one LLM at a time. You can change the target LLM by updating the `DEFAULT_LLM_URL` environment variable.

**Q: How do I backup my data?**

A: For SQLite database:
```bash
# Create backup
cp llm_lens.db llm_lens_backup_$(date +%Y%m%d).db

# Restore backup
cp llm_lens_backup_20240101.db llm_lens.db
```

**Q: How much disk space does LLM-Lens use?**

A: Storage depends on usage:
- Database: ~1KB per request
- Logs: ~100 bytes per request
- For 1000 requests/day: ~1MB/day

### Performance

**Q: LLM-Lens is slowing down my requests. What can I do?**

A: LLM-Lens adds minimal overhead (~5-10ms). If experiencing slowdowns:

1. Check database size: `ls -lh llm_lens.db`
2. Clean old logs if needed:
   ```python
   # Remove logs older than 30 days
   from database import get_db, LLMRequestLog
   from datetime import datetime, timedelta
   
   db = next(get_db())
   cutoff = datetime.utcnow() - timedelta(days=30)
   db.query(LLMRequestLog).filter(LLMRequestLog.start_time < cutoff).delete()
   db.commit()
   ```
3. Ensure sufficient system resources

**Q: Can I run LLM-Lens on a different server than my LLM?**

A: Yes! Set the `DEFAULT_LLM_URL` to point to your remote LLM:
```bash
export DEFAULT_LLM_URL="http://remote-server:1234/v1/chat/completions"
```

**Q: How accurate are the token counts?**

A: Token accuracy depends on your LLM's API:
- **LM Studio**: Very accurate (uses actual API counts)
- **Ollama**: Estimated (calculated from text length)
- **Custom APIs**: Depends on implementation

### Features

**Q: How do I set up cost tracking?**

A: Configure cost settings via API:
```bash
curl -X POST http://localhost:5000/api/cost-settings \
  -H "Content-Type: application/form-data" \
  -d "model_name=llama2&cost_per_1k_input_tokens=0.001&cost_per_1k_output_tokens=0.002"
```

**Q: How do alerts work?**

A: Alerts trigger when metrics exceed thresholds:
1. Create alert rules via API or dashboard
2. LLM-Lens monitors metrics in real-time
3. Alert events are logged when thresholds are crossed
4. View alerts in dashboard or via API

**Q: Can I export my data?**

A: Yes! Use the export endpoints:
```bash
# CSV export
curl "http://localhost:5000/api/export/csv?hours=24" --output data.csv

# JSON export
curl "http://localhost:5000/api/export/json?hours=24" --output data.json
```

**Q: What's the performance score calculation?**

A: Performance score (0-1) combines:
- **Latency score** (60%): Lower latency = higher score
- **Throughput score** (40%): Higher tokens/sec = higher score
- **Error penalty**: Errors result in 0 score

### Integrations

**Q: How do I integrate with my Python application?**

A: Update your OpenAI client configuration:
```python
import openai

# Instead of direct LLM
# client = openai.OpenAI(base_url="http://localhost:1234/v1")

# Use LLM-Lens proxy
client = openai.OpenAI(base_url="http://localhost:5000/proxy/v1")
```

**Q: How do I integrate with JavaScript/Node.js?**

A: Update your fetch URLs:
```javascript
// Instead of direct LLM API
// const response = await fetch('http://localhost:1234/v1/chat/completions', ...)

// Use LLM-Lens proxy
const response = await fetch('http://localhost:5000/proxy/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        model: 'your-model',
        messages: [{ role: 'user', content: 'Hello!' }]
    })
});
```

**Q: Does LLM-Lens work with LangChain?**

A: Yes! Configure LangChain to use the proxy:
```python
from langchain.llms import OpenAI

llm = OpenAI(
    openai_api_base="http://localhost:5000/proxy/v1",
    model_name="your-model"
)
```


### Deployment

For full deployment instructions and advanced options, see the `DEPLOYMENT.md` file in the documentation folder.

### Database

**Q: Can I use PostgreSQL instead of SQLite?**

A: Yes! Set the database URL:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/llm_lens"
```

**Q: How do I reset the database?**

A: Delete the database file and restart:
```bash
rm llm_lens.db
python main.py  # Will recreate database
```

**Q: How do I view raw database data?**

A: Use SQLite command line:
```bash
sqlite3 llm_lens.db
.tables
SELECT * FROM llm_request_logs LIMIT 10;
.quit
```

## 🔍 Debugging Steps

### Step 1: Check System Status

```bash
# Check if server is running
curl http://localhost:5000/

# Check database exists
ls -la llm_lens.db

# Check LLM is accessible
curl http://localhost:1234/v1/models  # LM Studio
curl http://localhost:11434/api/tags  # Ollama
```

### Step 2: Enable Debug Logging

Add to `main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Step 3: Test Proxy Endpoint

```bash
curl -X POST http://localhost:5000/proxy/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"test","messages":[{"role":"user","content":"Hello"}]}'
```

### Step 4: Check Database Contents

```python
from database import get_db, LLMRequestLog
db = next(get_db())
logs = db.query(LLMRequestLog).all()
print(f"Total logs: {len(logs)}")
for log in logs[-5:]:  # Last 5 logs
    print(f"{log.start_time}: {log.model_name} - {log.latency_ms}ms")
```

### Step 5: Verify Configuration

```python
import os
print("Environment Variables:")
print(f"DEFAULT_LLM_URL: {os.getenv('DEFAULT_LLM_URL', 'Not set')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
```

## 📞 Getting Help

### Self-Help Resources

1. **Check Console Logs**: Look for error messages in the terminal
2. **Review Documentation**: Check README.md and API.md
3. **Test Components**: Use curl commands to test each part
4. **Search Issues**: Look through GitHub issues for similar problems

### Creating Bug Reports

When reporting issues, include:

1. **System Information**
   - Operating system
   - Python version (`python --version`)
   - LLM software and version

2. **Error Details**
   - Full error message
   - Console output
   - Steps to reproduce

3. **Configuration**
   - Environment variables
   - LLM URL and model
   - Any custom settings

4. **Log Files**
   - Recent console output
   - Database query results
   - Browser console errors (for dashboard issues)

### Community Support

- **GitHub Issues**: [Create new issue](https://github.com/your-username/llm-lens/issues)
- **GitHub Discussions**: [Join discussions](https://github.com/your-username/llm-lens/discussions)
- **Documentation**: [Project Wiki](https://github.com/your-username/llm-lens/wiki)

## 🚀 Performance Tips

### Optimize Database Performance

1. **Regular Cleanup**
   ```python
   # Clean logs older than 30 days
   from database import get_db, LLMRequestLog
   from datetime import datetime, timedelta
   
   db = next(get_db())
   cutoff = datetime.utcnow() - timedelta(days=30)
   deleted = db.query(LLMRequestLog).filter(LLMRequestLog.start_time < cutoff).delete()
   db.commit()
   print(f"Deleted {deleted} old logs")
   ```

2. **Monitor Database Size**
   ```bash
   # Check database size
   ls -lh llm_lens.db
   
   # Count records
   sqlite3 llm_lens.db "SELECT COUNT(*) FROM llm_request_logs;"
   ```

### Optimize Application Performance

1. **Reduce Log Details**
   - Truncate long input/output texts
   - Disable verbose logging in production

2. **Use Efficient Queries**
   - Dashboard queries are optimized
   - Avoid custom queries on large datasets

3. **Monitor Resource Usage**
   ```bash
   # Check CPU and memory usage
   top -p $(pgrep -f "python main.py")
   ```

### Network Optimization

1. **Local Network Only**
   - Keep LLM and LLM-Lens on same network
   - Minimize network latency

2. **Connection Pooling**
   - Default httpx client is optimized
   - No additional configuration needed

---



# Installation Guide

This guide provides detailed steps for installing and setting up LLM-Lens in different environments.

## Local Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package installer)
- Git (for cloning the repository)

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/llm-lens.git
cd llm-lens
```

### Step 2: Install Dependencies

**Option A: Using pip (Simple)**
```bash
pip install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart
```

**Option B: Using requirements.txt (if available)**
```bash
pip install -r requirements.txt
```

**Option C: Using pyproject.toml**
```bash
pip install -e .
```

### Step 3: Initialize Database
The database is automatically initialized when you first run the application.

### Step 4: Run the Application
```bash
python main.py
```

The server will start on `http://localhost:5000`.

## Docker Installation (Advanced)

If you prefer using Docker:

### Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart

EXPOSE 5000

CMD ["python", "main.py"]
```

### Build and Run
```bash
docker build -t llm-lens .
docker run -p 5000:5000 llm-lens
```

## Environment Configuration

### Basic Configuration
Create a `.env` file (optional):
```bash
# LLM Configuration
DEFAULT_LLM_URL=http://localhost:1234/v1/chat/completions
OLLAMA_URL=http://localhost:11434/api/chat
LMSTUDIO_URL=http://localhost:1234/v1/chat/completions

# Database Configuration
DATABASE_URL=sqlite:///./llm_lens.db

# Server Configuration
HOST=0.0.0.0
PORT=5000
```

### Advanced Configuration

**For PostgreSQL Database:**
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/llm_lens
```

**For Remote LLM APIs:**
```bash
DEFAULT_LLM_URL=http://your-remote-server:port/v1/chat/completions
```

## Verification

### Test the Installation
1. **Check the server is running:**
   ```bash
   curl http://localhost:5000/
   ```

2. **Test the proxy endpoint:**
   ```bash
   curl -X POST http://localhost:5000/proxy/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "test", "messages": [{"role": "user", "content": "Hello"}]}'
   ```

3. **Access the dashboard:**
   Open `http://localhost:5000/dashboard` in your browser

### Verify Database
Check that the database was created:
```bash
ls -la llm_lens.db
```

You should see the SQLite database file.

## Troubleshooting Installation

### Common Issues

**1. Python Version Error**
```
Error: Python 3.11 or higher is required
```
**Solution:** Upgrade Python:
```bash
# On Ubuntu/Debian
sudo apt update && sudo apt install python3.11

# On macOS with Homebrew
brew install python@3.11

# On Windows, download from python.org
```

**2. Pip Installation Fails**
```
Error: pip: command not found
```
**Solution:** Install pip:
```bash
# On Ubuntu/Debian
sudo apt install python3-pip

# On macOS
python3 -m ensurepip --upgrade

# On Windows, reinstall Python with pip option checked
```

**3. Permission Denied**
```
PermissionError: [Errno 13] Permission denied
```
**Solution:** Use user installation:
```bash
pip install --user fastapi uvicorn sqlalchemy httpx jinja2 python-multipart
```

**4. Port Already in Use**
```
Error: [Errno 98] Address already in use
```
**Solution:** Change the port in `main.py`:
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)  # Changed from 5000 to 5001
```

**5. Module Import Errors**
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution:** Ensure all dependencies are installed:
```bash
pip list | grep fastapi
pip install --upgrade fastapi
```

**6. Database Permission Issues**
```
sqlite3.OperationalError: unable to open database file
```
**Solution:** Check directory permissions:
```bash
chmod 755 .
touch llm_lens.db
chmod 664 llm_lens.db
```

### Development Installation

For development with hot reload:

```bash
# Install with development dependencies
pip install fastapi uvicorn[standard] sqlalchemy httpx jinja2 python-multipart

# Run with auto-reload
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

### Production Installation

For production deployment:

```bash
# Install with production optimizations
pip install fastapi uvicorn[standard] sqlalchemy httpx jinja2 python-multipart gunicorn

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
```

## Next Steps

After successful installation:

1. **Configure your LLM** - Ensure your local LLM (LM Studio, Ollama, etc.) is running
2. **Update your applications** - Point them to the LLM-Lens proxy endpoint
3. **Explore the dashboard** - Start monitoring your LLM performance
4. **Set up alerts** - Configure performance monitoring
5. **Review the documentation** - Read the main README.md for usage details

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting section](#troubleshooting-installation)
2. Review the console output for error messages
3. Check that all prerequisites are met
4. Create a new issue with:
   - Your operating system
   - Python version (`python --version`)
   - Error message and full traceback
   - Steps to reproduce the issue

# Architecture Evaluation: Handling Heavy Async I/O

## 🎯 Objective
Handle heavy asynchronous I/O operations (like AI generation via external APIs) without blocking the main Flask application.

## 📊 Option Comparison

### Option A: FastAPI Microservice (Recommended for AI/Async)
**Best for:** Heavy I/O, external API calls, high concurrency, modern async Python.

| Pros | Cons |
|------|------|
| ✅ **True Async**: Native `async/await` support | ❌ **Complexity**: Adds another service to manage |
| ✅ **Performance**: High throughput with Uvicorn | ❌ **Overhead**: HTTP communication latency between apps |
| ✅ **Isolation**: AI crashes don't kill main app | ❌ **Deployment**: Needs separate process/container |
| ✅ **Scalability**: Can scale independently | |

### Option B: Flask + ThreadPoolExecutor
**Best for:** Simple background tasks, CPU-bound tasks, keeping architecture simple.

| Pros | Cons |
|------|------|
| ✅ **Simplicity**: No new service/deployment | ❌ **Pseudo-Async**: Uses threads, not true async event loop |
| ✅ **Integration**: Direct access to shared DB models | ❌ **Resource Heavy**: Threads consume more memory than async tasks |
| ✅ **Speed**: No HTTP overhead | ❌ **Blocking Risk**: GIL limitations for CPU tasks |

---

## 🚀 Migration Plan: Flask to FastAPI Microservice

### Phase 1: Create Microservice
1. Create `microservice/` directory
2. Initialize `fastapi` app
3. Implement async endpoints (e.g., `/generate-ai`)

### Phase 2: Update Main App
1. Update Flask app to call Microservice via HTTP
2. Use `httpx` or `requests` to communicate
3. Handle timeouts and errors gracefully

### Phase 3: Deployment
1. Update `docker-compose.yml` to include microservice
2. Configure Nginx to route traffic (optional) or keep internal

---

## 📝 Implementation Examples

### 1. FastAPI Microservice (`microservice/main.py`)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

class GenerationRequest(BaseModel):
    prompt: str
    model: str = "grok-1"

@app.post("/generate")
async def generate_timetable(request: GenerationRequest):
    """
    Async endpoint handling heavy I/O (External API call)
    """
    try:
        # Simulate external API call (non-blocking)
        async with httpx.AsyncClient() as client:
            # Replace with actual AI provider URL
            response = await client.post(
                "https://api.grok.ai/v1/chat/completions",
                json={
                    "model": request.model,
                    "messages": [{"role": "user", "content": request.prompt}]
                },
                headers={"Authorization": f"Bearer {os.getenv('GROK_API_KEY')}"},
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 2. Running the Microservice
```bash
# Install dependencies
pip install fastapi uvicorn httpx

# Run with Uvicorn (Development)
uvicorn microservice.main:app --reload --port 8000

# Run with Gunicorn + Uvicorn Workers (Production)
gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 microservice.main:app
```

### 3. Calling from Flask (`app_with_navigation.py`)

```python
import requests

@app.route('/generate-ai', methods=['POST'])
def generate_ai_proxy():
    prompt = request.json.get('prompt')
    
    # Call microservice (synchronous call from Flask perspective)
    try:
        resp = requests.post("http://localhost:8000/generate", json={"prompt": prompt})
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

---

## 🧵 Alternative: Flask ThreadPool (No Microservice)

If you prefer to keep everything in one app:

```python
from concurrent.futures import ThreadPoolExecutor
import requests

# Create thread pool
executor = ThreadPoolExecutor(max_workers=4)

def call_external_api(prompt):
    # Blocking I/O operation
    resp = requests.post("https://api.grok.ai/...", json={...})
    return resp.json()

@app.route('/generate-ai', methods=['POST'])
def generate_ai():
    prompt = request.json.get('prompt')
    
    # Offload to thread pool
    future = executor.submit(call_external_api, prompt)
    
    # Wait for result (still blocks request thread, but releases GIL)
    # For true non-blocking, you'd need Celery or similar
    result = future.result()
    
    return jsonify(result)
```

## 💡 Recommendation

**Go with FastAPI Microservice** if:
1. You expect high traffic
2. You have many async I/O operations
3. You want to use modern AI libraries that support async

**Stick with Flask + ThreadPool** if:
1. This is a rare operation
2. You want to minimize deployment complexity
3. You are comfortable with managing threads

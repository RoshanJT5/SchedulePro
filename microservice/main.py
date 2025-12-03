from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import httpx
import os
import asyncio
from typing import Optional

app = FastAPI(title="AI Timetable Microservice")

class GenerationRequest(BaseModel):
    prompt: str
    model: str = "grok-beta"
    temperature: float = 0.7

class GenerationResponse(BaseModel):
    result: str
    model_used: str
    usage: dict

@app.post("/generate", response_model=GenerationResponse)
async def generate(
    request: GenerationRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Async endpoint to handle heavy AI generation via Grok API.
    """
    # Use environment variable or header for API key
    api_key = x_api_key or os.getenv("GROK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    try:
        # Simulate heavy I/O or call actual API
        # In production, replace this with actual httpx call
        
        # Example of actual call structure:
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                json={
                    "model": request.model,
                    "messages": [
                        {"role": "system", "content": "You are a timetable assistant."},
                        {"role": "user", "content": request.prompt}
                    ],
                    "temperature": request.temperature
                },
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return {
                "result": data['choices'][0]['message']['content'],
                "model_used": data['model'],
                "usage": data.get('usage', {})
            }
        """
        
        # Simulation for now
        await asyncio.sleep(2)  # Simulate 2s latency
        return {
            "result": f"Simulated schedule based on: {request.prompt[:50]}...",
            "model_used": request.model,
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ai-microservice"}

# FastAPI Request Body Pitfall

## Symptom
POST/PUT endpoints return `null` instead of parsed JSON, or FastAPI returns 400/422 with no clear error.

## Root Cause
When you write `async def endpoint(request: dict):`, FastAPI treats `request` as a **query parameter** named "request", NOT as a JSON body. The endpoint will:
- Accept requests without error
- Receive `request = None` (no query param named "request")
- Return `null` when you try to use it

## Fix
```python
from fastapi import FastAPI, HTTPException, Request

# WRONG — request is treated as a query parameter, always None
@app.post("/api/endpoint")
async def bad(request: dict):
    return request  # returns null

# RIGHT — use FastAPI Request + await request.json()
@app.post("/api/endpoint")
async def good(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")
    return body  # returns the actual JSON
```

## Alternative: Pydantic model
```python
from pydantic import BaseModel

class Item(BaseModel):
    email: str
    password: str | None = None

@app.post("/api/endpoint")
async def good(item: Item):
    return {"email": item.email, "password": item.password}
```

## Occurrence
Hit this bug in `dashboard_server.py` `queue_add` endpoint.
The `request: dict` signature silently returned `null` for every POST.
Fixed by importing `Request` and using `await request.json()`.

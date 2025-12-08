# JSON Parsing Error Fix

## Problem
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
werkzeug.exceptions.BadRequest: 400 Bad Request: Failed to decode JSON object
```

This error occurs when `request.get_json()` is called on a request that doesn't contain valid JSON data (empty body, form data, or malformed JSON).

---

## Root Cause

The error happens in routes that expect JSON but receive:
- Empty request body
- Form-encoded data instead of JSON
- Malformed JSON
- Non-JSON content type

Common scenarios:
1. Frontend sends form data instead of JSON
2. Request body is empty
3. Content-Type header is not `application/json`

---

## Solution

### Option 1: Safe JSON Parsing (Recommended)

Replace:
```python
data = request.get_json() or {}
```

With:
```python
try:
    data = request.get_json(force=True, silent=True) or {}
except Exception:
    data = {}
```

Or better yet, use a helper function:

```python
def get_request_data():
    """Safely get JSON data from request, fallback to form data"""
    try:
        # Try JSON first
        data = request.get_json(force=True, silent=True)
        if data:
            return data
    except Exception:
        pass
    
    # Fallback to form data
    try:
        if request.form:
            return request.form.to_dict()
    except Exception:
        pass
    
    # Return empty dict if all fails
    return {}
```

### Option 2: Check Content Type First

```python
if request.is_json:
    data = request.get_json() or {}
elif request.form:
    data = request.form.to_dict()
else:
    data = {}
```

### Option 3: Use request.get_json() Parameters

```python
# force=True: Parse even if Content-Type is not application/json
# silent=True: Return None instead of raising error on parse failure
data = request.get_json(force=True, silent=True) or {}
```

---

## Recommended Implementation

Add this helper function to your `app_with_navigation.py`:

```python
def safe_get_request_data():
    """
    Safely extract data from request, supporting both JSON and form data.
    Returns empty dict if no data is available or parsing fails.
    """
    # Try JSON first (most API calls)
    try:
        data = request.get_json(force=True, silent=True)
        if data is not None:
            return data
    except Exception as e:
        print(f"[Request] JSON parsing failed: {e}")
    
    # Try form data (HTML forms)
    try:
        if request.form:
            return request.form.to_dict()
    except Exception as e:
        print(f"[Request] Form parsing failed: {e}")
    
    # Try query parameters (GET requests)
    try:
        if request.args:
            return request.args.to_dict()
    except Exception as e:
        print(f"[Request] Args parsing failed: {e}")
    
    # Return empty dict as fallback
    return {}
```

Then replace all instances of:
```python
data = request.get_json() or {}
data = request.json
```

With:
```python
data = safe_get_request_data()
```

---

## Quick Fix for Specific Route

If you know the specific route causing the issue (e.g., `/timetable/generate`), you can fix it individually:

**Before:**
```python
@app.route('/timetable/generate', methods=['POST'])
def generate_timetable():
    data = request.get_json() or {}  # ❌ Can fail
    # ... rest of code
```

**After:**
```python
@app.route('/timetable/generate', methods=['POST'])
def generate_timetable():
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        data = {}
    
    # Alternative: Check if JSON first
    if not data and request.form:
        data = request.form.to_dict()
    
    # ... rest of code
```

---

## Prevention

### Frontend Best Practices

Ensure your frontend sends proper JSON:

```javascript
// ✅ Correct
fetch('/timetable/generate', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ filters: {...} })
});

// ❌ Wrong - sends form data
fetch('/timetable/generate', {
    method: 'POST',
    body: new FormData(form)  // This is not JSON!
});
```

### Backend Best Practices

1. Always use safe JSON parsing
2. Validate Content-Type header
3. Provide clear error messages
4. Support multiple data formats when appropriate

---

## Testing

Test your routes with:

```bash
# Valid JSON
curl -X POST http://localhost:5000/timetable/generate \
  -H "Content-Type: application/json" \
  -d '{"filters": {}}'

# Empty body (should not crash)
curl -X POST http://localhost:5000/timetable/generate

# Form data (should handle gracefully)
curl -X POST http://localhost:5000/timetable/generate \
  -d "program=B.Tech&semester=1"
```

---

## Summary

**Problem**: `request.get_json()` crashes on non-JSON requests  
**Solution**: Use `request.get_json(force=True, silent=True) or {}` with try-except  
**Best Practice**: Create a `safe_get_request_data()` helper function

This makes your API more robust and handles edge cases gracefully.

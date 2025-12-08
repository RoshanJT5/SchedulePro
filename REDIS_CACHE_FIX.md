# Redis Cache Fix - Optional Caching

## Problem Fixed
The application was throwing Redis connection errors when Redis was not running:
```
Cache write error: Error 10061 connecting to localhost:6379. 
No connection could be made because the target machine actively refused it.
```

## Solution Applied
Modified `cache.py` to make Redis **optional** instead of required. The application now:

1. ✅ **Checks Redis availability on startup** with a 1-second timeout
2. ✅ **Gracefully degrades to no-cache mode** if Redis is unavailable
3. ✅ **Eliminates connection error spam** in the logs
4. ✅ **Runs perfectly without Redis** - caching is a performance optimization, not a requirement

## Changes Made

### File: `cache.py`

#### 1. Redis Availability Check (Lines 14-24)
```python
# Check Redis availability
try:
    _temp_client = redis.from_url(redis_url, socket_connect_timeout=1)
    _temp_client.ping()
    redis_client = _temp_client
    redis_available = True
    print("[Cache] Redis connected successfully")
except Exception as e:
    print(f"[Cache] Redis not available: {e}")
    print("[Cache] Running in no-cache mode")
    redis_available = False
```

#### 2. Updated Functions
- **`get_cache_version()`**: Returns default version if Redis unavailable
- **`invalidate_cache()`**: Silently skips if Redis unavailable
- **`cache_response()`**: Bypasses caching entirely if Redis unavailable

## Current Status

### ✅ Application Works WITHOUT Redis
The application now runs perfectly without Redis. You'll see this message on startup:
```
[Cache] Redis not available: Error 10061 connecting to localhost:6379...
[Cache] Running in no-cache mode
```

This is **normal and expected** if you don't have Redis installed.

## Optional: Enable Redis for Performance

Redis provides **response caching** which can significantly improve performance for:
- Timetable views (complex queries)
- Dashboard statistics
- Course/faculty listings

### Option 1: Install Redis on Windows

1. **Download Redis for Windows**:
   - Visit: https://github.com/microsoftarchive/redis/releases
   - Download: `Redis-x64-3.0.504.msi`

2. **Install Redis**:
   - Run the installer
   - Use default settings (Port 6379)
   - Check "Add to PATH"

3. **Start Redis**:
   ```powershell
   redis-server
   ```

4. **Restart your Flask application** - it will automatically detect Redis

### Option 2: Use Docker (Recommended)

```powershell
# Start Redis in Docker
docker run -d -p 6379:6379 --name redis redis:alpine

# Stop Redis
docker stop redis

# Remove Redis container
docker rm redis
```

### Option 3: Use WSL2 (Windows Subsystem for Linux)

```bash
# In WSL2 terminal
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

## Environment Variables

You can customize the Redis connection in your `.env` file:

```env
# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379/1
```

## Verification

When Redis is running, you'll see on startup:
```
[Cache] Redis connected successfully
```

When caching works, you'll see:
```
[Cache] Invalidated prefix: timetable_view
```

## Performance Impact

### Without Redis (Current)
- ✅ Application works perfectly
- ⚠️ No response caching
- ⚠️ Database queries run on every request

### With Redis (Optional)
- ✅ Cached responses (5 minutes default TTL)
- ✅ Reduced database load
- ✅ Faster page loads for repeated requests
- ✅ Version-based cache invalidation

## Summary

**You don't need to do anything!** The application now works without Redis. The error messages are gone, and everything functions normally.

If you want better performance in the future, you can optionally install Redis using one of the methods above.

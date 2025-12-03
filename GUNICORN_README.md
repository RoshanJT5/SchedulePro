# Running with Gunicorn (Production Server)

## Quick Start

Your Flask application is now configured to run with Gunicorn for production use. This allows multiple users to access your application simultaneously without freezing.

### Configuration Summary

✅ **gunicorn_config.py** - Configured with:
- Workers: `(CPU cores * 2) + 1` (automatically calculated)
- Threads per worker: 4
- Timeout: 120 seconds
- Worker class: `gthread` (best for database-heavy apps)

✅ **requirements.txt** - Includes `gunicorn==21.2.0`

✅ **Procfile** - Ready for deployment platforms (Heroku, Render, etc.)

✅ **MongoDB** - Your MongoDB configuration is intact and unchanged

## How to Run

### Option 1: Using the Start Script (Recommended)

**Windows:**
```cmd
start_gunicorn.bat
```

**Linux/Mac:**
```bash
chmod +x start_gunicorn.sh
./start_gunicorn.sh
```

### Option 2: Direct Command

```bash
gunicorn -c gunicorn_config.py app_with_navigation:app
```

### Option 3: Custom Configuration

You can override settings using environment variables:

```bash
# Windows
set GUNICORN_WORKERS=8
set GUNICORN_THREADS=2
gunicorn -c gunicorn_config.py app_with_navigation:app

# Linux/Mac
GUNICORN_WORKERS=8 GUNICORN_THREADS=2 gunicorn -c gunicorn_config.py app_with_navigation:app
```

## Performance

With Gunicorn, your application can now:
- ✅ Handle multiple concurrent users
- ✅ Process requests in parallel
- ✅ Automatically restart workers to prevent memory leaks
- ✅ Scale based on your CPU cores

### Example Performance

On a 4-core CPU:
- **Workers**: 9 (calculated as 4 * 2 + 1)
- **Total threads**: 36 (9 workers × 4 threads)
- **Concurrent requests**: Can handle 36+ simultaneous requests

## Monitoring

To see your Gunicorn workers running:

**Windows:**
```cmd
tasklist | findstr gunicorn
```

**Linux/Mac:**
```bash
ps aux | grep gunicorn
```

## Deployment

For deployment platforms (Heroku, Render, Railway, etc.), the `Procfile` is already configured:

```
web: gunicorn -c gunicorn_config.py app_with_navigation:app
```

Just push your code and the platform will automatically use Gunicorn!

## Troubleshooting

### Application won't start
- Check that `.env` file exists with your MongoDB credentials
- Verify MongoDB connection string is correct
- Check logs for specific errors

### Slow performance
- Increase workers: `export GUNICORN_WORKERS=12`
- Increase threads: `export GUNICORN_THREADS=8`
- Monitor memory usage

### Workers timing out
- Increase timeout: Edit `gunicorn_config.py` and change `timeout = 120` to a higher value

## Important Notes

- 🔒 **MongoDB Configuration**: Unchanged and working correctly
- 🚫 **No Docker**: This setup doesn't require Docker
- ✅ **Production Ready**: Safe to deploy to production
- 📊 **Auto-scaling**: Workers automatically scale with CPU cores

## Need Help?

Check the logs when running Gunicorn - they will show:
- Number of workers started
- Worker PIDs
- Any errors or warnings
- Request processing information

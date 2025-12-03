# Background Tasks with Celery & Redis

This project now uses Celery to handle heavy tasks (like Timetable Generation) in the background.

## Prerequisites

1. **Redis**: You must have Redis running.
   - **Docker**: `docker run -d -p 6379:6379 redis`
   - **Windows**: Install Memurai or run Redis via WSL.
   - **Linux/Mac**: `sudo apt install redis` / `brew install redis`

## Configuration

The following environment variables in `.env` control Celery:

```
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Running Locally

1. **Start Redis** (if not running)
2. **Start the Flask App** (Terminal 1):
   ```cmd
   python app_with_navigation.py
   ```
3. **Start the Celery Worker** (Terminal 2):
   - **Windows**:
     ```cmd
     start_celery.bat
     ```
   - **Linux/Mac**:
     ```bash
     ./start_celery.sh
     ```

## Running with Docker Compose

The `docker-compose.yml` has been updated to include Redis and a Celery Worker automatically.

```bash
docker-compose up --build
```

## How it Works

1. When you click "Generate Timetable", the server returns immediately with a `task_id`.
2. The Celery worker picks up the task and runs the algorithm.
3. The frontend polls `/tasks/<task_id>` to check progress.
4. Once complete, the result is returned.

@echo off
echo Starting AI Microservice...
cd microservice
uvicorn main:app --reload --port 8000

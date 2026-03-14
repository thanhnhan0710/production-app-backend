#!/bin/bash
set -e

echo "Running Database Migrations..."
alembic upgrade head

echo "Starting Server..."
# Chạy với 2 workers cho môi trường thử nghiệm thay vì reload
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
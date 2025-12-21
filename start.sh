#!/bin/bash

# Dừng script nếu có lệnh bị lỗi
set -e

# 1. Chạy migration để đồng bộ Database mới nhất
echo "Running Database Migrations..."
alembic upgrade head

# 2. Khởi động Server FastAPI
echo "Starting Server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
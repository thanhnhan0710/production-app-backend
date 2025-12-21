# 1. Chọn Base Image (Python 3.10 bản nhẹ)
FROM python:3.13-slim

# 2. Thiết lập biến môi trường
# PYTHONDONTWRITEBYTECODE: Ngăn Python tạo file .pyc
# PYTHONUNBUFFERED: Log in ra terminal ngay lập tức (dễ debug)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Tạo thư mục làm việc trong container
WORKDIR /app

# 4. Cài đặt các dependencies hệ thống (nếu cần thiết cho MySQL client)
RUN apt-get update && apt-get install -y default-libmysqlclient-dev build-essential pkg-config

# 5. Copy file requirements và cài thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy toàn bộ source code vào container
COPY . .

# 7. Cấp quyền chạy cho script khởi động (sẽ tạo ở bước 2)
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 8. Mở port 8000
EXPOSE 8000

# 9. Lệnh chạy mặc định (Gọi file script)
CMD ["/start.sh"]
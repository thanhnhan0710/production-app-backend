FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Chỉ cài build-essential nếu các thư viện trong requirements.txt yêu cầu compile
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Đảm bảo file start.sh có trong thư mục gốc của bạn
COPY start.sh /start.sh
RUN sed -i 's/\r$//' /start.sh && chmod +x /start.sh

EXPOSE 8000

CMD ["/start.sh"]
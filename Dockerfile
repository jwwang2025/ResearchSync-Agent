FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（轻量）
RUN apt-get update && apt-get install -y build-essential git && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖（项目应包括 requirements.txt 和 requirements-api.txt）
COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-api.txt

# 复制项目代码
COPY . .

# 默认命令由 docker-compose 覆盖；使用新的 backend 启动入口以统一入口位置
CMD ["python", "-m", "backend.main"]



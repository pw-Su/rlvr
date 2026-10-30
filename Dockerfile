FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 先复制依赖文件，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制项目代码
COPY . .

# 健康检查：运行自验证测试，确认环境可用
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python main.py --test || exit 1

# 默认启动标准演示
CMD ["python", "main.py"]
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码和配置文件，保持目录结构
COPY app/ ./app/
COPY prompt_template.txt .

# 创建配置目录用于挂载外部环境变量
RUN mkdir -p /app/config

VOLUME ["/app/config"]
CMD ["python", "app/func_annotator.py"]
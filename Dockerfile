FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY func_annotator.py prompt_template.txt .
CMD ["python", "func_annotator.py"]
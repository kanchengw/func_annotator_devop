# Func Annotator

Func Annotator is a simple Python tool that generates natural language annotations for Python functions using a plain-text prompt. The annotation describes the function's input, processing, and output in clear, concise English.

## Features

- Generates structured, plain-English documentation for Python functions.
- Outputs annotation in three parts: Input, Processing, Output.
- Simple to run locally or in Docker.
- Designed for clarity—no Markdown or extraneous formatting.

## Usage

1. **Clone the repository** and install dependencies:
   ```
   git clone <your-repo-url>
   cd <repo>
   pip install -r requirements.txt
   ```

2. **Run the annotator** (interactive mode):
   ```
   python app/func_annotator.py
   ```
   Paste your function when prompted, end your input with 'end'(case ignored) in a new line to get result.

3. **Batch annotation** (process all function samples):
   ```
   python app/batch_annotator.py
   ```
   This will process all functions in `feedings/` and save annotated results to `outputs/`.

4. **Run the test:**
   ```
   pytest tests/test.py
   ```

## Docker

You can also use Docker for easy setup and execution:

```
# 构建 Docker 镜像
docker build -t func-annotator .

# 运行标注工具（需要挂载配置文件）
docker run --rm -v $(pwd)/docker.env:/app/config/docker.env func-annotator

# 运行测试
docker run --rm -v $(pwd)/docker.env:/app/config/docker.env func-annotator pytest tests/test.py -v
```

## API & Annotation Prompt Template

The tool uses `.env` to store model info and credentials:

```
API_KEY=YOUR_API_KEY
API_URL=YOUR_API_URL
MODEL_NAME=YOUR_MODEL_NAME
```

The tool uses `prompt_template.txt` to modify prompt sending to models.

## Data Version Control (DVC)

This project uses **DVC** to version control function samples in the `feedings/` directory. This allows you to track changes to your training data and collaborate with others.

### Setting up DVC

1. **Install DVC** (already included in requirements.txt):
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize DVC** manually:
   ```bash
   # Initialize DVC repository
   dvc init
   
   # Add function sample files to version control
   dvc add feedings/function_sample1.py
   dvc add feedings/function_sample2.py
   ```
   
   This will create `.dvc` files that track your function samples and add them to DVC cache.

### DVC Commands

```bash
# View current status
dvc status

# Commit changes
dvc commit -m "Updated function samples"

# Push to remote storage
dvc push

# Pull latest version
dvc pull

# View history
dvc list .

# Show differences
dvc diff
```

### Current Function Samples

- **function_sample1.py** - Arithmetic and mathematical functions (20 functions)
  - Arithmetic operations, geometry, statistics, linear algebra
- **function_sample2.py** - Text processing functions (20 functions)
  - String operations, text analysis, data formatting, encryption

## Version 1.0.1:

- debugged errors in Dockerfile.
- added error captures in func_annotator.py.
- attached readme.md.
- added cache files in .gitignore and .dockerignore.

## Version 1.1.0:
- added model performance traced by integrating mlflow & dagshub.
- restructured project with app/ and tests/ directories.
- enhanced error handling and monitoring metrics.

## Version 1.2.0:
- integrated DVC (Data Version Control) for managing function samples.
- added version control for feedings/ function sample files.
- reorganized project structure with docs/ directory.
- added batch annotation script (app/batch_annotator.py) for processing multiple functions at once.
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

2. **Run the annotator:**
   ```
   python func_annotator.py
   ```

   Paste your function when prompted, end your input with 'end'(case ignored) in a new line to get result.

3. **Run the test:**
   ```
   pytest test.py
   ```

## Docker

You can also use Docker for easy setup and execution:

```
docker build -t func-annotator .
docker run --rm -v $(pwd):/app func-annotator
docker run --rm -v $(pwd):/app func-annotator pytest test.py -v
```

## API & Annotation Prompt Template

The tool uses `.env` to store model info and credentials:

```
API_KEY=YOUR_API_KEY
API_URL=YOUR_API_URL
MODEL_NAME=YOUR_MODEL_NAME
```

The tool uses `prompt_template.txt` to modify prompt sending to models.



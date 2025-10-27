# Project Structure

## Directory Organization

```
func_annotator_devop/
├── app/                        # Application code
│   └── func_annotator.py      # Main application (function annotation tool)
│
├── tests/                      # Test code
│   └── test.py                # Unit tests
│
├── feedings/                   # Function sample data (DVC version control)
│   ├── function_sample1.py    # Arithmetic and mathematical functions (20 functions)
│   └── function_sample2.py   # Text processing functions (20 functions)
│
├── config/                     # Configuration files
│   └── function_samples.yaml  # Function sample configuration
│
├── docs/                       # Documentation
│   └── readme.md              # Project documentation
│
├── Dockerfile                  # Docker build file
├── docker.env                  # Docker environment variables
├── .dockerignore              # Docker ignore file
├── .gitignore                  # Git ignore file
├── .dvcignore                  # DVC ignore file
├── .pylintrc                   # Pylint configuration
├── requirements.txt            # Python dependencies
├── dvc.yaml                    # DVC configuration
└── prompt_template.txt         # Prompt template
```

## Directory Descriptions

### `app/` - Application Code
- Contains core functionality: function comment generation, API calls, MLflow tracking
- Main module: `func_annotator.py`

### `tests/` - Tests
- Unit tests and integration tests
- Uses pytest for testing

### `feedings/` - Training Data
- Function sample data, version controlled with DVC
- `function_sample1.py`: Arithmetic and mathematical operations (20 functions)
- `function_sample2.py`: Text processing (20 functions)

### `config/` - Configuration
- `function_samples.yaml`: Metadata and configuration for function samples

### `docs/` - Documentation
- Project description, usage guide, version history

## File Descriptions

### Root Directory Configuration Files
- **Dockerfile**: Docker image build configuration
- **docker.env**: Docker container environment variables (API configuration, etc.)
- **requirements.txt**: Python package dependency list
- **dvc.yaml**: DVC data version control configuration
- **prompt_template.txt**: Model prompt template

### Configuration Files
- **.gitignore**: Git version control ignore rules
- **.dockerignore**: Docker build ignore rules
- **.dvcignore**: DVC ignore rules
- **.pylintrc**: Python code style checking configuration

## Usage

### 1. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python app/func_annotator.py

# Run tests
pytest tests/test.py
```

### 2. DVC Data Management
```bash
# Initialize DVC
dvc init

# Add function sample files to version control
dvc add feedings/function_sample1.py
dvc add feedings/function_sample2.py

# View status
dvc status

# Commit changes
dvc commit -m "Updated function samples"

# Push to remote storage
dvc push
```

### 3. Docker Deployment
```bash
# Build image
docker build -t func-annotator .

# Run container
docker run --rm -v $(pwd)/docker.env:/app/config/docker.env func-annotator
```

## Version History
- **v1.2.0**: Integrated DVC for training data management
- **v1.1.0**: Integrated MLflow tracking, restructured directory
- **v1.0.1**: Basic functionality and Docker support

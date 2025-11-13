# Component Tests for *Models.py

## Overview
Simple standalone unit tests for the Option model class that mock database connections.

## Prerequisites
```bash
pip install pytest --break-system-packages
pip install flask flask-mail flask-bcrypt pymysql python-dotenv
```

## Running the Tests...replace * with model being tested
```bash
pytest tests/test_*.py -v
```
### Ex. Run tests for optionModels.py:
```bash
pytest tests/test_optionModels.py -v
```

### If you want to run a specific test:
```bash
pytest tests/test_optionModels.py::test_option_init_creates_instance_with_correct_attributes -v
```

### Run with more detailed output:
```bash
pytest tests/test_optionModels.py -v -s
```

### Run with coverage (if you want to see code coverage):
```bash
pip install pytest-cov --break-system-packages
pytest tests/test_optionModels.py --cov=flask_app.models.optionModels --cov-report=term-missing
```

## What's Being Tested

### 1. **__init__()** - Constructor
- ✓ Creates instance with correct attributes
- ✓ Handles different data types

### 2. **getByEventId()** - Retrieve options by event ID
- ✓ Returns list of Option objects
- ✓ Returns empty list when no options found

### 3. **create()** - Create new option
- ✓ Inserts option into database
- ✓ Returns database response

### 4. **deleteByEventId()** - Delete options by event ID
- ✓ Calls delete query with correct parameters
- ✓ Handles nonexistent events

### 5. **Basic Cluster Integration Test**
- ✓ Tests workflow: create → retrieve → delete

## Test Structure

Each test is **standalone** and uses **mocked database connections**, meaning:
- ✓  No actual database required
- ✓  Fast execution
- ✓  No side effects
- ✓  Can run anywhere

## Understanding the Mocks

The tests use `unittest.mock` to simulate database behavior:

```python
# This automatically mocks the database for ALL tests
@pytest.fixture(autouse=True)
def mock_db_connection():
    with patch('flask_app.models.optionModels.connectToMySQL') as mock_connect:
        yield mock_connect
```

# When a test needs specific database behavior:
```python
# Make the mock return specific data
mock_query = Mock(return_value=[...])
mock_db_connection.return_value.query_db = mock_query
```

## Expected Output - test_optionModels.py
When all tests pass, you'll see:
```
tests/test_optionModels.py::test_option_init_creates_instance_with_correct_attributes PASSED
...
tests/test_optionModels.py::test_option_workflow_create_retrieve_delete PASSED

======= 9 passed in 0.XX s =======
```

## Troubleshooting

### Import Error: "No module named 'flask_app'"
Make sure you're running pytest from the project root directory where `flask_app/` exists.

### ModuleNotFoundError
run with Python module syntax:
```bash
python -m pytest tests/test_optionModels.py -v
```
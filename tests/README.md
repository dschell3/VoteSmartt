# Component Tests for optionModels.py

## Overview
Simple standalone unit tests for the Option model class that mock database connections.

## Prerequisites
```bash
pip install pytest --break-system-packages
```

## Running the Tests

### Run all tests in the file:
```bash
pytest tests/test_optionModels.py -v
```

### Run a specific test:
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

### 5. **Integration Test**
- ✓ Tests workflow: create → retrieve → delete

## Test Structure

Each test is **standalone** and uses **mocked database connections**, meaning:
- ✅ No actual database required
- ✅ Fast execution
- ✅ No side effects
- ✅ Can run anywhere

## Understanding the Mocks

The tests use `unittest.mock` to simulate database behavior:

```python
# This automatically mocks the database for ALL tests
@pytest.fixture(autouse=True)
def mock_db_connection():
    with patch('flask_app.models.optionModels.connectToMySQL') as mock_connect:
        yield mock_connect
```

When a test needs specific database behavior:
```python
# Make the mock return specific data
mock_query = Mock(return_value=[...])
mock_db_connection.return_value.query_db = mock_query
```

## Expected Output

When all tests pass, you'll see:
```
tests/test_optionModels.py::test_option_init_creates_instance_with_correct_attributes PASSED
tests/test_optionModels.py::test_option_init_handles_different_data_types PASSED
tests/test_optionModels.py::test_getByEventId_returns_list_of_options PASSED
tests/test_optionModels.py::test_getByEventId_returns_empty_list_when_no_options PASSED
tests/test_optionModels.py::test_create_inserts_option_into_database PASSED
tests/test_optionModels.py::test_create_returns_database_response PASSED
tests/test_optionModels.py::test_deleteByEventId_calls_delete_query PASSED
tests/test_optionModels.py::test_deleteByEventId_handles_nonexistent_event PASSED
tests/test_optionModels.py::test_option_workflow_create_retrieve_delete PASSED

======= 9 passed in 0.XX s =======
```

## Troubleshooting

### Import Error: "No module named 'flask_app'"
Make sure you're running pytest from the project root directory where `flask_app/` exists.

### ModuleNotFoundError
Ensure your PYTHONPATH includes the project root:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/test_optionModels.py -v
```

Or run with Python module syntax:
```bash
python -m pytest tests/test_optionModels.py -v
```
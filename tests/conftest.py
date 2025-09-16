#!/usr/bin/env python3
"""
Configuration file for pytest.
Provides common fixtures and setup for all tests.
"""

import sys
import os
import tempfile
import logging
from pathlib import Path

try:
    import pytest
except ImportError:
    # pytest not installed, define dummy decorators
    class pytest:
        class mark:
            @staticmethod
            def rag(func):
                return func
            @staticmethod
            def integration(func):
                return func
            @staticmethod
            def voice(func):
                return func
            @staticmethod
            def agent(func):
                return func
            @staticmethod
            def asyncio(func):
                return func
            @staticmethod
            def skip(reason=""):
                def decorator(func):
                    return func
                return decorator
        
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func
            return decorator

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for tests
logging.basicConfig(level=logging.WARNING, format='%(name)s - %(levelname)s - %(message)s')


@pytest.fixture(scope="session")
def project_root_path():
    """Fixture providing the project root path."""
    return project_root


@pytest.fixture(scope="function")
def temp_directory():
    """Fixture providing a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture(scope="function")
def temp_file(temp_directory):
    """Fixture providing a temporary file for tests."""
    temp_file_path = os.path.join(temp_directory, "test_file.txt")
    yield temp_file_path


@pytest.fixture(scope="session")
def ollama_available():
    """Check if Ollama is available for integration tests."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


@pytest.fixture(scope="function") 
def suppress_warnings():
    """Suppress warnings during tests."""
    import warnings
    warnings.filterwarnings("ignore")
    yield
    warnings.resetwarnings()


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip integration tests if Ollama is not available."""
    if config.getoption("--run-integration"):
        return
    
    skip_integration = pytest.mark.skip(reason="Integration tests skipped. Use --run-integration to run them.")
    
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests (requires Ollama)"
    )
    parser.addoption(
        "--run-manual",
        action="store_true", 
        default=False,
        help="Run manual tests"
    )


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "manual: marks tests as manual/interactive tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
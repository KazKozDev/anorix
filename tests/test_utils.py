#!/usr/bin/env python3
"""
Utilities for tests - provides pytest compatibility without requiring pytest.
"""

# Handle pytest import gracefully
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    
    # Define dummy pytest decorators for direct execution
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
            def manual(func):
                return func
            @staticmethod
            def slow(func):
                return func
            @staticmethod
            def asyncio(func):
                return func


def requires_pytest():
    """Decorator to skip tests if pytest is not available."""
    def decorator(func):
        if not PYTEST_AVAILABLE:
            def wrapper(*args, **kwargs):
                print(f"⚠️  Skipping {func.__name__} - pytest not available")
                print("   Install pytest: pip install pytest")
                return None
            return wrapper
        return func
    return decorator


def requires_ollama():
    """Decorator to skip tests if Ollama is not available."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                import requests
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code != 200:
                    print(f"⚠️  Skipping {func.__name__} - Ollama not available")
                    print("   Start Ollama: ollama serve")
                    return None
            except:
                print(f"⚠️  Skipping {func.__name__} - Ollama not available")
                print("   Start Ollama: ollama serve")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator
"""
Global pytest fixtures for NeuralForge tests
"""
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.utils.lazy_loading import LazyLoader, ComponentLoader

@pytest.fixture(scope="function")
def qapp():
    """Create QApplication instance"""
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture(scope="function")
def lazy_loader():
    """Create lazy loader instance"""
    loader = LazyLoader()
    yield loader
    loader.clear()  # Очищаем кэш после каждого теста

@pytest.fixture(scope="function")
def component_loader():
    """Create component loader instance"""
    loader = ComponentLoader()
    yield loader
    loader.clear()  # Очищаем кэш после каждого теста

@pytest.fixture(scope="function")
def cleanup_widgets():
    """Cleanup widgets after tests"""
    widgets = []
    yield widgets
    for widget in widgets:
        if widget.parent() is None:  # Очищаем только виджеты верхнего уровня
            widget.close()
            widget.deleteLater()

@pytest.fixture(scope="function")
def process_events(qapp):
    """Process Qt events"""
    def _process():
        qapp.processEvents()
    return _process

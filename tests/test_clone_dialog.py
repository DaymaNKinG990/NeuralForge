import pytest
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QApplication, QMessageBox
from PyQt6.QtCore import Qt
from src.ui.dialogs.clone_dialog import CloneDialog
from pathlib import Path
import tempfile
from unittest.mock import patch
import gc
import logging
import sys
from weakref import ref

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Маркируем все тесты в этом файле как требующие изоляции Qt
pytestmark = pytest.mark.qt_no_exception_capture

@pytest.fixture(scope="function")
def qapp():
    """Create the Qt Application."""
    logger.debug("Setting up QApplication")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        logger.debug("Created new QApplication instance")
    yield app
    logger.debug("Test finished, but keeping QApplication for other tests")

@pytest.fixture(autouse=True)
def setup_test_environment(qapp):
    """Setup test environment before each test."""
    logger.debug("Setting up test environment")
    # Очищаем все существующие виджеты верхнего уровня
    for widget in qapp.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    qapp.processEvents()
    gc.collect()
    yield
    logger.debug("Cleaning up test environment")
    # Снова очищаем после теста
    for widget in qapp.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    qapp.processEvents()
    gc.collect()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    logger.debug("Creating temporary directory")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        logger.debug(f"Created temp directory at: {temp_path}")
        yield temp_path
        logger.debug("Cleaning up temporary directory")

@pytest.fixture
def clone_dialog(qtbot, qapp, temp_dir):
    """Create a CloneDialog instance with a temporary directory."""
    logger.debug("Setting up CloneDialog fixture")
    
    with patch('src.utils.git_manager.GitManager._ensure_repo'):
        logger.debug("Creating CloneDialog instance")
        dialog = CloneDialog()
        
        dialog.default_clone_path = temp_dir
        dialog.directory_input.setText(str(temp_dir))
        dialog.git_manager.project_path = temp_dir
        
        logger.debug("Adding widget to qtbot")
        qtbot.addWidget(dialog)
        
        # Отключаем автоматическое удаление
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        
        logger.debug("Showing dialog")
        dialog.show()
        
        # Безопасная обработка событий
        app = QApplication.instance()
        if app:
            app.processEvents()
        
        logger.debug("Waiting for dialog to be exposed")
        qtbot.waitExposed(dialog, timeout=5000)
        
        logger.debug("Dialog setup complete")
        yield dialog
        
        logger.debug("Starting cleanup")
        try:
            if dialog.isVisible():
                logger.debug("Hiding dialog")
                dialog.hide()
                if app:
                    app.processEvents()
            
            logger.debug("Closing dialog")
            dialog.close()
            if app:
                app.processEvents()
            
            # Даем время на обработку событий
            qtbot.wait(100)
            if app:
                app.processEvents()
            
        except RuntimeError as e:
            logger.debug(f"Runtime error during cleanup: {e}")
        finally:
            logger.debug("Cleanup complete")

@pytest.mark.qt
def test_dialog_initialization(clone_dialog, temp_dir):
    """Test dialog initialization."""
    logger.debug("Starting initialization test")
    try:
        assert isinstance(clone_dialog, QDialog)
        assert clone_dialog.windowTitle() == "Clone Repository"
        assert Path(clone_dialog.directory_input.text()) == temp_dir
        logger.debug("Initialization test completed successfully")
    except Exception as e:
        logger.error(f"Error in initialization test: {e}", exc_info=True)
        raise

@pytest.mark.qt
def test_url_input(clone_dialog, qtbot):
    """Test URL input field."""
    logger.debug("Starting URL input test")
    try:
        test_url = "https://github.com/test/repo.git"
        qtbot.keyClicks(clone_dialog.url_input, test_url)
        qtbot.wait(100)
        assert clone_dialog.url_input.text() == test_url
        logger.debug("URL input test completed successfully")
    except Exception as e:
        logger.error(f"Error in URL input test: {e}", exc_info=True)
        raise

@pytest.mark.qt
def test_directory_selection(clone_dialog, qtbot, mocker, temp_dir):
    """Test directory selection."""
    logger.debug("Starting directory selection test")
    try:
        test_dir = temp_dir / "test_clone"
        mock_get_directory = mocker.patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory')
        mock_get_directory.return_value = str(test_dir)
        
        qtbot.mouseClick(clone_dialog.browse_button, Qt.MouseButton.LeftButton)
        qtbot.wait(100)
        assert clone_dialog.directory_input.text() == str(test_dir)
        logger.debug("Directory selection test completed successfully")
    except Exception as e:
        logger.error(f"Error in directory selection test: {e}", exc_info=True)
        raise

@pytest.mark.qt
def test_validation(clone_dialog, qtbot, monkeypatch):
    """Test input validation."""
    logger.debug("Starting validation test")
    try:
        # Подменяем QMessageBox.warning чтобы избежать показа диалога
        def mock_warning(*args, **kwargs):
            return QMessageBox.StandardButton.Ok
            
        monkeypatch.setattr(QMessageBox, 'warning', mock_warning)
        
        # Test with empty URL
        assert not clone_dialog.validate_inputs()
        
        # Test with valid URL and directory
        clone_dialog.url_input.setText("https://github.com/test/repo.git")
        clone_dialog.directory_input.setText(str(temp_dir))
        assert clone_dialog.validate_inputs()
        logger.debug("Validation test completed successfully")
    except Exception as e:
        logger.error(f"Error in validation test: {e}", exc_info=True)
        raise

@pytest.mark.qt
def test_accept(clone_dialog, qtbot, temp_dir):
    """Test accept functionality."""
    logger.debug("Starting accept test")
    try:
        with patch('src.ui.dialogs.clone_dialog.GitManager.clone_repository') as mock_clone:
            # Setup test data
            test_url = "https://github.com/test/repo.git"
            clone_dialog.url_input.setText(test_url)
            clone_dialog.directory_input.setText(str(temp_dir))
            
            # Test accept
            mock_clone.return_value = True
            
            # Сохраняем состояние до клика
            was_visible = clone_dialog.isVisible()
            
            qtbot.mouseClick(
                clone_dialog.button_box.button(QDialogButtonBox.StandardButton.Ok),
                Qt.MouseButton.LeftButton
            )
            
            # Даем время на обработку событий
            qtbot.wait(100)
            QApplication.instance().processEvents()
            
            # Проверяем результаты
            assert mock_clone.called
            assert was_visible  # Диалог был видим до клика
            assert clone_dialog.result() == QDialog.DialogCode.Accepted
            
            logger.debug("Accept test completed successfully")
    except Exception as e:
        logger.error(f"Error in accept test: {e}", exc_info=True)
        raise

@pytest.mark.qt
def test_reject(clone_dialog, qtbot, temp_dir):
    """Test reject functionality."""
    logger.debug("Starting reject test")
    try:
        # Сохраняем состояние до клика
        was_visible = clone_dialog.isVisible()
        
        # Test reject
        qtbot.mouseClick(
            clone_dialog.button_box.button(QDialogButtonBox.StandardButton.Cancel),
            Qt.MouseButton.LeftButton
        )
        
        # Даем время на обработку событий
        qtbot.wait(100)
        QApplication.instance().processEvents()
        
        # Проверяем результаты
        assert was_visible  # Диалог был видим до клика
        assert clone_dialog.result() == QDialog.DialogCode.Rejected
        
        logger.debug("Reject test completed successfully")
    except Exception as e:
        logger.error(f"Error in reject test: {e}", exc_info=True)
        raise

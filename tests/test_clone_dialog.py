import pytest
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt
from src.ui.dialogs.clone_dialog import CloneDialog

@pytest.fixture
def clone_dialog(qtbot):
    dialog = CloneDialog()
    qtbot.addWidget(dialog)
    return dialog

def test_dialog_initialization(clone_dialog):
    assert isinstance(clone_dialog, QDialog)
    assert clone_dialog.windowTitle() == "Clone Repository"

def test_url_input(clone_dialog, qtbot):
    test_url = "https://github.com/test/repo.git"
    qtbot.keyClicks(clone_dialog.url_input, test_url)
    assert clone_dialog.url_input.text() == test_url

def test_directory_selection(clone_dialog, qtbot, mocker):
    mock_get_directory = mocker.patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory')
    test_dir = "/test/directory"
    mock_get_directory.return_value = test_dir
    
    qtbot.mouseClick(clone_dialog.browse_button, Qt.MouseButton.LeftButton)
    assert clone_dialog.directory_input.text() == test_dir

def test_validation(clone_dialog):
    # Test with empty URL
    assert not clone_dialog.validate_inputs()
    
    # Test with valid URL
    clone_dialog.url_input.setText("https://github.com/test/repo.git")
    clone_dialog.directory_input.setText("/test/directory")
    assert clone_dialog.validate_inputs()

def test_accept_reject(clone_dialog, qtbot):
    # Test accept
    clone_dialog.url_input.setText("https://github.com/test/repo.git")
    clone_dialog.directory_input.setText("/test/directory")
    qtbot.mouseClick(clone_dialog.button_box.button(QDialogButtonBox.StandardButton.Ok), Qt.MouseButton.LeftButton)
    assert clone_dialog.result() == QDialog.DialogCode.Accepted

    # Test reject
    qtbot.mouseClick(clone_dialog.button_box.button(QDialogButtonBox.StandardButton.Cancel), Qt.MouseButton.LeftButton)
    assert clone_dialog.result() == QDialog.DialogCode.Rejected

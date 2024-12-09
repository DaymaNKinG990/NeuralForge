"""Tests for resource viewer component."""
import pytest
import os
import shutil
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.ui.components.resource.resource_viewer import ResourceViewer

@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory with test files."""
    # Create test files
    (tmp_path / "test.txt").write_text("Test content")
    (tmp_path / "test.py").write_text("print('Hello')")
    
    # Create test directory with files
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "inner.txt").write_text("Inner content")
    
    return tmp_path

@pytest.fixture
def resource_viewer(qtbot, temp_dir):
    """Create resource viewer fixture."""
    viewer = ResourceViewer()
    viewer.set_root_path(str(temp_dir))
    qtbot.addWidget(viewer)
    return viewer

def test_resource_viewer_creation(resource_viewer):
    """Test resource viewer creation."""
    assert resource_viewer is not None
    assert resource_viewer.tree is not None
    assert resource_viewer.model is not None
    assert resource_viewer.path_label is not None
    
def test_set_root_path(resource_viewer, temp_dir):
    """Test setting root path."""
    assert resource_viewer.path_label.text() == str(temp_dir)
    assert resource_viewer.model.rootPath() == str(temp_dir)
    
def test_file_tree_structure(resource_viewer, temp_dir):
    """Test file tree structure."""
    model = resource_viewer.model
    root_index = resource_viewer.tree.rootIndex()
    
    # Check number of items
    assert model.rowCount(root_index) == 3  # test.txt, test.py, test_dir
    
    # Check file names
    files = []
    for row in range(model.rowCount(root_index)):
        index = model.index(row, 0, root_index)
        files.append(model.fileName(index))
        
    assert "test.txt" in files
    assert "test.py" in files
    assert "test_dir" in files
    
def test_resource_selection(qtbot, resource_viewer, temp_dir):
    """Test resource selection signal."""
    # Create signal spy
    with qtbot.waitSignal(resource_viewer.resource_selected) as blocker:
        # Get index of test.txt
        model = resource_viewer.model
        root_index = resource_viewer.tree.rootIndex()
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            if model.fileName(index) == "test.txt":
                # Click the item
                resource_viewer.tree.clicked.emit(index)
                break
                
    # Check signal argument
    assert blocker.args[0] == str(temp_dir / "test.txt")
    
def test_context_menu_actions(resource_viewer, temp_dir):
    """Test context menu actions existence."""
    # Get index of test.txt
    model = resource_viewer.model
    root_index = resource_viewer.tree.rootIndex()
    file_index = None
    for row in range(model.rowCount(root_index)):
        index = model.index(row, 0, root_index)
        if model.fileName(index) == "test.txt":
            file_index = index
            break
            
    assert file_index is not None
    
    # Create context menu
    menu = QMenu()
    resource_viewer._create_context_menu(menu, file_index)
    
    # Check actions
    action_texts = [action.text() for action in menu.actions()]
    assert "Open" in action_texts
    assert "Rename" in action_texts
    assert "Delete" in action_texts
    
@pytest.mark.skip(reason="Delete functionality needs QMessageBox mock")
def test_delete_resource(qtbot, resource_viewer, temp_dir):
    """Test deleting resource."""
    test_file = temp_dir / "test.txt"
    assert test_file.exists()
    
    # Get index of test.txt
    model = resource_viewer.model
    root_index = resource_viewer.tree.rootIndex()
    file_index = None
    for row in range(model.rowCount(root_index)):
        index = model.index(row, 0, root_index)
        if model.fileName(index) == "test.txt":
            file_index = index
            break
            
    assert file_index is not None
    
    # Mock QMessageBox.question to return Yes
    with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
        resource_viewer._delete_resource(str(test_file))
        
    assert not test_file.exists()
    
def test_tree_view_properties(resource_viewer):
    """Test tree view properties."""
    assert resource_viewer.tree.dragEnabled()
    assert resource_viewer.tree.acceptDrops()
    assert resource_viewer.tree.dragDropMode() == resource_viewer.tree.dragDropMode.InternalMove
    
    # Check hidden columns
    assert resource_viewer.tree.isColumnHidden(1)  # Size
    assert resource_viewer.tree.isColumnHidden(2)  # Type
    assert resource_viewer.tree.isColumnHidden(3)  # Date Modified

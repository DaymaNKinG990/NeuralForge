"""Tests for Project Explorer components."""
import pytest
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtCore import Qt
from src.ui.project_explorer.tree_view import ProjectTreeView
from src.ui.project_explorer.actions import ProjectActions

@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project structure."""
    # Create project structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('main')")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass")
    (tmp_path / "data").mkdir()
    (tmp_path / "models").mkdir()
    return tmp_path

@pytest.fixture
def project_tree(qtbot, temp_project):
    """Create project tree view fixture."""
    tree = ProjectTreeView()
    tree.set_root_path(str(temp_project))
    qtbot.addWidget(tree)
    return tree

@pytest.fixture
def project_actions(project_tree):
    """Create project actions fixture."""
    return ProjectActions(project_tree)

def test_project_tree_creation(project_tree):
    """Test project tree view creation."""
    assert project_tree is not None
    assert project_tree.model() is not None
    
def test_project_structure(project_tree, temp_project):
    """Test project structure display."""
    model = project_tree.model()
    root_index = project_tree.rootIndex()
    
    # Check root folders
    root_items = []
    for row in range(model.rowCount(root_index)):
        index = model.index(row, 0, root_index)
        root_items.append(model.fileName(index))
    
    assert "src" in root_items
    assert "tests" in root_items
    assert "data" in root_items
    assert "models" in root_items

def test_file_selection(project_tree, temp_project, qtbot):
    """Test file selection signal."""
    # Find main.py
    model = project_tree.model()
    root_index = project_tree.rootIndex()
    main_py_path = None
    
    for row in range(model.rowCount(root_index)):
        parent_index = model.index(row, 0, root_index)
        if model.fileName(parent_index) == "src":
            for child_row in range(model.rowCount(parent_index)):
                child_index = model.index(child_row, 0, parent_index)
                if model.fileName(child_index) == "main.py":
                    main_py_path = model.filePath(child_index)
                    # Simulate selection
                    with qtbot.waitSignal(project_tree.file_selected):
                        project_tree.setCurrentIndex(child_index)
                    break
    
    assert main_py_path is not None
    assert main_py_path == str(temp_project / "src" / "main.py")

def test_context_menu(project_tree, project_actions, temp_project):
    """Test context menu creation."""
    # Get src folder index
    model = project_tree.model()
    root_index = project_tree.rootIndex()
    src_index = None
    
    for row in range(model.rowCount(root_index)):
        index = model.index(row, 0, root_index)
        if model.fileName(index) == "src":
            src_index = index
            break
    
    assert src_index is not None
    
    # Create context menu
    menu = QMenu()
    project_actions.create_context_menu(menu, src_index)
    
    # Check actions
    action_texts = [action.text() for action in menu.actions()]
    assert "New File" in action_texts
    assert "New Folder" in action_texts
    assert "Delete" in action_texts
    assert "Rename" in action_texts

def test_file_operations(project_tree, project_actions, temp_project, qtbot):
    """Test file operations."""
    # Get src folder index
    model = project_tree.model()
    root_index = project_tree.rootIndex()
    src_index = None
    
    for row in range(model.rowCount(root_index)):
        index = model.index(row, 0, root_index)
        if model.fileName(index) == "src":
            src_index = index
            break
    
    assert src_index is not None
    
    # Test new file creation
    new_file_path = temp_project / "src" / "new_file.py"
    project_actions.create_file(src_index, "new_file.py")
    assert new_file_path.exists()
    
    # Test new folder creation
    new_folder_path = temp_project / "src" / "new_folder"
    project_actions.create_folder(src_index, "new_folder")
    assert new_folder_path.exists()
    assert new_folder_path.is_dir()

def test_file_filters(project_tree):
    """Test file filtering."""
    filters = project_tree.model().nameFilters()
    assert "*.py" in filters
    assert "*.json" in filters
    assert "*.yaml" in filters
    assert "*.yml" in filters

def test_hidden_files(project_tree, temp_project):
    """Test hidden files handling."""
    # Create hidden file
    hidden_file = temp_project / ".hidden"
    hidden_file.write_text("hidden")
    
    # Check it's not visible
    model = project_tree.model()
    root_index = project_tree.rootIndex()
    
    visible_files = []
    for row in range(model.rowCount(root_index)):
        index = model.index(row, 0, root_index)
        visible_files.append(model.fileName(index))
    
    assert ".hidden" not in visible_files

def test_drag_drop_support(project_tree):
    """Test drag and drop support."""
    assert project_tree.dragEnabled()
    assert project_tree.acceptDrops()
    assert project_tree.dragDropMode() == project_tree.DragDropMode.InternalMove

def test_project_actions_signals(project_actions):
    """Test project actions signals."""
    assert hasattr(project_actions, 'file_created')
    assert hasattr(project_actions, 'folder_created')
    assert hasattr(project_actions, 'item_deleted')
    assert hasattr(project_actions, 'item_renamed')

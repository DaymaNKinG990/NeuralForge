"""Tests for LLM workspace components."""
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QThread
from src.ui.llm_workspace.workspace import LLMWorkspace
from src.ui.llm_workspace.threads import LLMThread
from src.ui.llm_workspace.generation import GenerationPanel

@pytest.fixture
def llm_workspace(qtbot):
    """Create LLM workspace fixture."""
    workspace = LLMWorkspace()
    qtbot.addWidget(workspace)
    return workspace

@pytest.fixture
def generation_panel(qtbot):
    """Create generation panel fixture."""
    panel = GenerationPanel()
    qtbot.addWidget(panel)
    return panel

def test_llm_workspace_creation(llm_workspace):
    """Test LLM workspace creation."""
    assert llm_workspace is not None
    assert llm_workspace.generation_panel is not None
    assert llm_workspace.chat_history is not None
    assert llm_workspace.model_selector is not None

def test_model_selection(llm_workspace):
    """Test model selection functionality."""
    # Check default model
    assert llm_workspace.model_selector.currentText() != ""
    
    # Change model
    model_name = llm_workspace.model_selector.itemText(1)
    llm_workspace.model_selector.setCurrentText(model_name)
    assert llm_workspace.model_selector.currentText() == model_name

def test_generation_panel_creation(generation_panel):
    """Test generation panel creation."""
    assert generation_panel is not None
    assert generation_panel.prompt_input is not None
    assert generation_panel.generate_button is not None
    assert generation_panel.stop_button is not None
    assert not generation_panel.stop_button.isEnabled()

def test_generation_panel_input(qtbot, generation_panel):
    """Test generation panel input handling."""
    test_prompt = "Test prompt"
    qtbot.keyClicks(generation_panel.prompt_input, test_prompt)
    assert generation_panel.prompt_input.toPlainText() == test_prompt
    
    # Check generate button enabled state
    assert generation_panel.generate_button.isEnabled()
    generation_panel.prompt_input.clear()
    assert not generation_panel.generate_button.isEnabled()

def test_llm_thread_creation():
    """Test LLM thread creation."""
    thread = LLMThread("test prompt", "test model")
    assert thread is not None
    assert isinstance(thread, QThread)
    assert thread.prompt == "test prompt"
    assert thread.model == "test model"

def test_llm_thread_signals():
    """Test LLM thread signals."""
    thread = LLMThread("test prompt", "test model")
    
    # Check signal existence
    assert hasattr(thread, 'response_received')
    assert hasattr(thread, 'error_occurred')
    assert hasattr(thread, 'generation_finished')

@pytest.mark.asyncio
async def test_generation_process(qtbot, generation_panel):
    """Test the generation process flow."""
    # Setup test prompt
    test_prompt = "Test generation"
    qtbot.keyClicks(generation_panel.prompt_input, test_prompt)
    
    # Start generation
    with qtbot.waitSignal(generation_panel.generation_started, timeout=1000):
        qtbot.mouseClick(generation_panel.generate_button, Qt.MouseButton.LeftButton)
    
    # Check UI state during generation
    assert generation_panel.stop_button.isEnabled()
    assert not generation_panel.generate_button.isEnabled()
    assert generation_panel.prompt_input.isReadOnly()

def test_chat_history(llm_workspace):
    """Test chat history functionality."""
    # Check initial state
    assert llm_workspace.chat_history.toPlainText() == ""
    
    # Add messages
    test_messages = [
        ("user", "Hello"),
        ("assistant", "Hi there!"),
        ("user", "How are you?"),
        ("assistant", "I'm doing well, thank you!")
    ]
    
    for role, content in test_messages:
        llm_workspace.chat_history.append_message(role, content)
        assert content in llm_workspace.chat_history.toPlainText()

def test_workspace_state_management(llm_workspace):
    """Test workspace state management."""
    # Test busy state
    llm_workspace.set_busy_state(True)
    assert llm_workspace.generation_panel.generate_button.isEnabled() == False
    assert llm_workspace.generation_panel.stop_button.isEnabled() == True
    
    llm_workspace.set_busy_state(False)
    assert llm_workspace.generation_panel.generate_button.isEnabled() == True
    assert llm_workspace.generation_panel.stop_button.isEnabled() == False

def test_error_handling(llm_workspace, qtbot):
    """Test error handling in workspace."""
    test_error = "Test error message"
    
    # Simulate error
    with qtbot.waitSignal(llm_workspace.error_occurred):
        llm_workspace.handle_error(test_error)
    
    # Check error is displayed in chat history
    assert test_error in llm_workspace.chat_history.toPlainText()
    assert not llm_workspace.generation_panel.stop_button.isEnabled()
    assert llm_workspace.generation_panel.generate_button.isEnabled()

def test_stop_generation(generation_panel, qtbot):
    """Test stopping generation process."""
    # Start generation
    test_prompt = "Test generation"
    qtbot.keyClicks(generation_panel.prompt_input, test_prompt)
    qtbot.mouseClick(generation_panel.generate_button, Qt.MouseButton.LeftButton)
    
    # Stop generation
    assert generation_panel.stop_button.isEnabled()
    qtbot.mouseClick(generation_panel.stop_button, Qt.MouseButton.LeftButton)
    
    # Check state after stopping
    assert not generation_panel.stop_button.isEnabled()
    assert generation_panel.generate_button.isEnabled()
    assert not generation_panel.prompt_input.isReadOnly()

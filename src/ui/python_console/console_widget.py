"""Main Python console widget."""
from typing import Optional, List
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter,
    QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor
import logging
from ..styles.style_manager import StyleManager
from .input_widget import ConsoleInputWidget
from .output_widget import ConsoleOutputWidget
from .history_manager import ConsoleHistoryManager
from .interpreter import PythonInterpreter

logger = logging.getLogger(__name__)

class PythonConsoleWidget(QWidget):
    """Main Python console widget."""
    
    execution_started = pyqtSignal(str)  # Emits code being executed
    execution_finished = pyqtSignal(bool)  # Emits success status
    
    def __init__(self, parent=None):
        """Initialize console widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.interpreter = PythonInterpreter()
        self.history = ConsoleHistoryManager()
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the console UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for input/output
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Output widget
        self.output_widget = ConsoleOutputWidget()
        splitter.addWidget(self.output_widget)
        
        # Input widget
        self.input_widget = ConsoleInputWidget()
        splitter.addWidget(self.input_widget)
        
        # Set initial sizes
        splitter.setSizes([200, 100])
        layout.addWidget(splitter)
        
        # Set up context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def connect_signals(self):
        """Connect widget signals."""
        # Input widget signals
        self.input_widget.code_executed.connect(self.execute_code)
        self.input_widget.history_up.connect(self.history.get_previous)
        self.input_widget.history_down.connect(self.history.get_next)
        
        # History signals
        self.history.history_item.connect(self.input_widget.set_input)
        
        # Interpreter signals
        self.interpreter.output_written.connect(self.output_widget.write_output)
        self.interpreter.error_written.connect(self.output_widget.write_error)
        
    def execute_code(self, code: str):
        """Execute Python code.
        
        Args:
            code: Code to execute
        """
        if not code.strip():
            return
            
        # Add to history
        self.history.add_item(code)
        
        # Show in output
        self.output_widget.write_input(code)
        
        # Execute code
        self.execution_started.emit(code)
        try:
            self.interpreter.execute(code)
            success = True
        except Exception as e:
            self.output_widget.write_error(str(e))
            success = False
        finally:
            self.execution_finished.emit(success)
            
    def show_context_menu(self, pos):
        """Show context menu.
        
        Args:
            pos: Menu position
        """
        menu = QMenu(self)
        
        # Clear actions
        menu.addAction("Clear Output", self.output_widget.clear)
        menu.addAction("Clear Input", self.input_widget.clear)
        menu.addAction("Clear History", self.history.clear)
        
        # Copy/paste actions
        menu.addSeparator()
        menu.addAction("Copy", self.copy_selection)
        menu.addAction("Paste", self.paste_clipboard)
        
        # Execute actions
        menu.addSeparator()
        menu.addAction("Execute", self.input_widget.execute_current)
        menu.addAction("Interrupt", self.interpreter.interrupt)
        
        menu.exec(self.mapToGlobal(pos))
        
    def copy_selection(self):
        """Copy selected text."""
        if self.output_widget.hasFocus():
            self.output_widget.copy()
        else:
            self.input_widget.copy()
            
    def paste_clipboard(self):
        """Paste clipboard text."""
        self.input_widget.paste()
        
    def set_font_size(self, size: int):
        """Set console font size.
        
        Args:
            size: Font size
        """
        self.input_widget.set_font_size(size)
        self.output_widget.set_font_size(size)
        
    def get_state(self) -> dict:
        """Get console state.
        
        Returns:
            State dictionary
        """
        return {
            'history': self.history.get_items(),
            'input': self.input_widget.get_input(),
            'interpreter': self.interpreter.get_state()
        }
        
    def set_state(self, state: dict):
        """Set console state.
        
        Args:
            state: State dictionary
        """
        if 'history' in state:
            self.history.set_items(state['history'])
        if 'input' in state:
            self.input_widget.set_input(state['input'])
        if 'interpreter' in state:
            self.interpreter.set_state(state['interpreter'])

import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PyQt6.QtGui import QTextCursor, QColor, QPalette
from PyQt6.QtCore import Qt, pyqtSignal
from code import InteractiveInterpreter
from io import StringIO

class PythonConsole(QWidget, InteractiveInterpreter):
    command_executed = pyqtSignal(str, str)  # signal for command and its output
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        InteractiveInterpreter.__init__(self)
        
        self.prompt = ">>> "
        self.continuation_prompt = "... "
        self.setup_ui()
        self.history = []
        self.history_index = 0
        self.current_command = []
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create console output widget
        self.console = QPlainTextEdit()
        self.console.setReadOnly(False)
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                font-family: 'Consolas';
                font-size: 10pt;
            }
        """)
        
        # Enable syntax highlighting for input
        self.console.keyPressEvent = self.handle_key_press
        layout.addWidget(self.console)
        
        # Write initial prompt
        self.write_prompt()
        
    def write_prompt(self, prompt=None):
        if prompt is None:
            prompt = self.prompt
        self.console.insertPlainText(prompt)
        
    def write_output(self, text):
        self.console.insertPlainText(text + '\n')
        
    def handle_key_press(self, event):
        cursor = self.console.textCursor()
        
        # Handle special keys
        if event.key() == Qt.Key.Key_Return:
            self.handle_return()
            return
        elif event.key() == Qt.Key.Key_Backspace:
            if cursor.position() <= self.get_command_start_position():
                return
        elif event.key() == Qt.Key.Key_Up:
            self.handle_history_up()
            return
        elif event.key() == Qt.Key.Key_Down:
            self.handle_history_down()
            return
        
        # Allow normal key processing
        QPlainTextEdit.keyPressEvent(self.console, event)
        
    def handle_return(self):
        command = self.get_current_command()
        
        if command.strip():
            self.history.append(command)
            self.history_index = len(self.history)
            
            # Capture stdout
            stdout = StringIO()
            stderr = StringIO()
            sys.stdout = stdout
            sys.stderr = stderr
            
            # Execute the command
            more = self.runsource(command)
            
            # Restore stdout
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            
            # Get output
            output = stdout.getvalue() + stderr.getvalue()
            
            # Write output
            if output:
                self.write_output(output.rstrip())
            
            # Emit signal
            self.command_executed.emit(command, output)
        
        self.console.insertPlainText('\n')
        self.write_prompt()
        
    def handle_history_up(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.replace_current_command(self.history[self.history_index])
            
    def handle_history_down(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.replace_current_command(self.history[self.history_index])
        else:
            self.history_index = len(self.history)
            self.replace_current_command('')
            
    def get_command_start_position(self):
        doc = self.console.document()
        block = doc.findBlockByLineNumber(doc.lineCount() - 1)
        return block.position() + len(self.prompt)
        
    def get_current_command(self):
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(
            QTextCursor.MoveOperation.StartOfLine,
            QTextCursor.MoveMode.KeepAnchor
        )
        line = cursor.selectedText()
        return line[len(self.prompt):]
        
    def replace_current_command(self, command):
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(
            QTextCursor.MoveOperation.StartOfLine,
            QTextCursor.MoveMode.KeepAnchor
        )
        cursor.removeSelectedText()
        self.write_prompt()
        self.console.insertPlainText(command)
        
    def get_namespace(self):
        return self.locals

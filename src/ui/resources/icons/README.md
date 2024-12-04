# NeuralForge Icons

This directory contains SVG icons used throughout the NeuralForge IDE. The icons follow a consistent VS Code-inspired design language with a modern, minimalist style.

## Color Palette
- Primary Blue: #569CD6
- Secondary Blue: #9CDCFE
- Green: #89D185
- Purple: #C586C0
- Orange: #CE9178
- Folder Yellow: #DCB67A
- Teal: #4EC9B0
- Error Red: #F48771

## Icon Set
- `play.svg` - Run/Start training button
- `stop.svg` - Stop/Cancel operation button
- `clear.svg` - Clear/Reset button
- `settings.svg` - Configuration and settings
- `save.svg` - Save model/project
- `folder.svg` - Open/Browse directory
- `neural-network.svg` - Neural network visualization
- `chart.svg` - Training metrics and charts
- `code.svg` - Code editor
- `terminal.svg` - Terminal/Console output
- `debug.svg` - Debugging tools
- `zoom.svg` - Zoom controls for visualizations

## Usage
These icons are used with PyQt6's QIcon system. Load them using:
```python
from PyQt6.QtGui import QIcon
icon = QIcon("path/to/icon.svg")

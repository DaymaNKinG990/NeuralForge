from enum import Enum, auto

class ThemeType(Enum):
    """Theme types for the application."""
    DARK = auto()
    LIGHT = auto()
    HIGH_CONTRAST = auto()

class ColorScheme(Enum):
    """Color scheme for the application UI."""
    # Base colors
    BACKGROUND = "#252526"
    FOREGROUND = "#CCCCCC"
    ACCENT = "#0E639C"
    ERROR = "#F44747"
    WARNING = "#CC7832"
    SUCCESS = "#4EC9B0"
    
    # UI elements
    MENU_BACKGROUND = "#2D2D2D"
    MENU_HOVER = "#094771"
    MENU_BORDER = "#454545"
    
    # Project tree
    TREE_BACKGROUND = "#252526"
    TREE_ITEM_HOVER = "#2A2D2E"
    TREE_ITEM_SELECTED = "#094771"
    
    # Editor
    EDITOR_BACKGROUND = "#1E1E1E"
    EDITOR_CURRENT_LINE = "#2A2D2E"
    EDITOR_SELECTION = "#264F78"
    EDITOR_GUTTER = "#252526"
    EDITOR_LINE_NUMBER = "#858585"
    EDITOR_MATCHING_BRACKET = "#4EC9B0"
    EDITOR_CURSOR = "#A6A6A6"
    
    # Syntax highlighting
    SYNTAX_KEYWORD = "#569CD6"
    SYNTAX_STRING = "#CE9178"
    SYNTAX_COMMENT = "#6A9955"
    SYNTAX_FUNCTION = "#DCDCAA"
    SYNTAX_CLASS = "#4EC9B0"
    SYNTAX_NUMBER = "#B5CEA8"
    SYNTAX_DECORATOR = "#C586C0"
    SYNTAX_OPERATOR = "#D4D4D4"
    SYNTAX_VARIABLE = "#9CDCFE"
    SYNTAX_CONSTANT = "#4FC1FF"
    
    # ML Workspace
    ML_BACKGROUND = "#1E1E1E"
    ML_BORDER = "#2D2D2D"
    ML_HEADER = "#252526"
    ML_PROGRESS = "#0E639C"
    ML_GRAPH_GRID = "#2D2D2D"
    ML_GRAPH_LINE = "#4EC9B0"
    
    # Performance Monitor
    PERF_BACKGROUND = "#1E1E1E"
    PERF_CPU_LINE = "#4EC9B0"
    PERF_MEMORY_LINE = "#C586C0"
    PERF_GPU_LINE = "#569CD6"
    PERF_DISK_LINE = "#CE9178"
    PERF_GRID = "#2D2D2D"
    
    # Status indicators
    STATUS_INFO = "#75BEFF"
    STATUS_ERROR = "#F44747"
    STATUS_WARNING = "#CCA700"
    STATUS_SUCCESS = "#89D185"

class StyleClass(Enum):
    """Style classes for UI components."""
    # Main components
    MAIN_WINDOW = "MainWindow"
    MENU_BAR = "MenuBar"
    TOOL_BAR = "ToolBar"
    STATUS_BAR = "StatusBar"
    DOCK_WIDGET = "DockWidget"
    
    # Views and editors
    TREE_VIEW = "TreeView"
    CODE_EDITOR = "CodeEditor"
    PROJECT_EXPLORER = "ProjectExplorer"
    ML_WORKSPACE = "MLWorkspace"
    PERFORMANCE_MONITOR = "PerformanceMonitor"
    
    # Common widgets
    TAB_WIDGET = "TabWidget"
    PROGRESS_BAR = "ProgressBar"
    BUTTON = "Button"
    LINE_EDIT = "LineEdit"
    COMBO_BOX = "ComboBox"
    SCROLL_BAR = "ScrollBar"
    MENU = "Menu"
    DIALOG = "Dialog"
    SPLITTER = "Splitter"
    TOOLBAR_BUTTON = "ToolbarButton"
    LABEL = "Label"
    
    # Custom components
    LINE_NUMBER_AREA = "LineNumberArea"
    GRAPH_WIDGET = "GraphWidget"
    MODEL_CONFIG = "ModelConfig"
    TRAINING_CONTROL = "TrainingControl"
    METRICS_TABLE = "MetricsTable"

class StyleProperty(Enum):
    """Style properties for UI components."""
    # Basic properties
    BACKGROUND = "background"
    FOREGROUND = "color"
    BORDER = "border"
    PADDING = "padding"
    MARGIN = "margin"
    
    # Text and icons
    FONT = "font"
    FONT_SIZE = "font-size"
    FONT_WEIGHT = "font-weight"
    FONT_STYLE = "font-style"
    ICON = "icon"
    
    # Layout
    WIDTH = "width"
    HEIGHT = "height"
    MIN_WIDTH = "min-width"
    MIN_HEIGHT = "min-height"
    MAX_WIDTH = "max-width"
    MAX_HEIGHT = "max-height"
    
    # Positioning
    ALIGNMENT = "alignment"
    SPACING = "spacing"
    POSITION = "position"
    TOP = "top"
    RIGHT = "right"
    BOTTOM = "bottom"
    LEFT = "left"
    
    # Visual effects
    OPACITY = "opacity"
    SHADOW = "box-shadow"
    RADIUS = "border-radius"
    GRADIENT = "background-gradient"

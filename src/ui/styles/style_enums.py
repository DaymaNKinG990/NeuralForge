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
    
    # Status colors
    STATUS_INFO = "#4FC1FF"     # Bright blue for info
    STATUS_WARNING = "#FFA500"   # Orange for warnings
    
    # Line numbers
    LINE_NUMBER_BG = "#1E1E1E"  # Line number area background
    LINE_NUMBER_FG = "#858585"  # Line number text color
    
    # UI elements
    MENU_BACKGROUND = "#2D2D2D"
    MENU_HOVER = "#094771"
    MENU_BORDER = "#454545"
    
    # Input elements
    INPUT_BACKGROUND = "#3C3C3C"
    INPUT_BORDER = "#454545"
    INPUT_FOCUS_BORDER = "#007ACC"
    
    # Button elements
    BUTTON_BACKGROUND = "#4D4D4D"
    BUTTON_HOVER = "#606060"
    BUTTON_BORDER = "#454545"
    BUTTON_TEXT = "#CCCCCC"
    BUTTON_DISABLED = "#2D2D2D"
    
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
    LINE_NUMBER_BACKGROUND = "#1E1E1E"  # Line number area background
    LINE_NUMBER_FOREGROUND = "#858585"  # Line number text color
    
    # Syntax highlighting
    SYNTAX_KEYWORD = "#569CD6"      # Python keywords
    SYNTAX_BUILTIN = "#4EC9B0"      # Built-in functions
    SYNTAX_STRING = "#CE9178"       # String literals
    SYNTAX_NUMBER = "#B5CEA8"       # Numeric literals
    SYNTAX_COMMENT = "#6A9955"      # Comments
    SYNTAX_FUNCTION = "#DCDCAA"     # Function names
    SYNTAX_CLASS = "#4EC9B0"        # Class names
    SYNTAX_DECORATOR = "#C586C0"    # Decorators
    SYNTAX_OPERATOR = "#D4D4D4"     # Operators
    SYNTAX_CONSTANT = "#4FC1FF"     # Constants

class StyleClass(Enum):
    """Style classes for UI elements."""
    # Main window
    MAIN_WINDOW = "main-window"
    CENTRAL_WIDGET = "central-widget"
    STATUS_BAR = "status-bar"
    
    # Dock widgets
    DOCK_WIDGET = "dock-widget"
    DOCK_TITLE_BAR = "dock-title-bar"
    DOCK_CONTENT = "dock-content"
    
    # Tree view and navigation
    TREE_VIEW = "tree-view"
    TREE_VIEW_ITEM = "tree-view-item"
    TREE_VIEW_BRANCH = "tree-view-branch"
    TREE_VIEW_SELECTED = "tree-view-selected"
    PROJECT_EXPLORER = "project-explorer"  # For project navigation
    ML_WORKSPACE = "ml-workspace"         # For ML tools
    LLM_WORKSPACE = "llm-workspace"       # For LLM tools
    PYTHON_CONSOLE = "python-console"     # For Python REPL
    
    # Editor components
    EDITOR = "editor"
    EDITOR_BACKGROUND = "editor-background"
    EDITOR_SELECTION = "editor-selection"
    EDITOR_CURRENT_LINE = "editor-current-line"
    CODE_EDITOR = "code-editor"           # Legacy support
    LINE_NUMBER_AREA = "line-number-area"
    LINE_NUMBER_BG = "line-number-area"   # For backward compatibility
    LINE_NUMBER_FG = "line-number-text"   # For backward compatibility
    LINE_NUMBER_BACKGROUND = "line-number-area"  # Legacy support
    LINE_NUMBER_FOREGROUND = "line-number-text"  # Legacy support
    MINIMAP = "minimap"
    SCROLLBAR = "scrollbar"
    TAB_WIDGET = "tab-widget"
    
    # Menus and toolbars
    MENU_BAR = "menu-bar"
    MENU_ITEM = "menu-item"
    MENU = "menu"                         # Legacy support
    TOOLBAR = "toolbar"
    TOOLBAR_BUTTON = "toolbar-button"
    TOOL_BAR = "toolbar"                  # Legacy support
    
    # Input elements
    INPUT = "input"
    BUTTON = "button"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    COMBOBOX = "combobox"
    LINE_EDIT = "line-edit"               # Legacy support
    COMBO_BOX = "combobox"                # Legacy support
    DIALOG = "dialog"
    SPLITTER = "splitter"
    LABEL = "label"
    
    # Status elements
    STATUS_INFO = "status-info"
    STATUS_WARNING = "status-warning"
    STATUS_ERROR = "status-error"
    
    # ML components
    GRAPH_WIDGET = "graph-widget"
    MODEL_CONFIG = "model-config"
    TRAINING_CONTROL = "training-control"
    METRICS_TABLE = "metrics-table"
    
    # Common styles (legacy support)
    FOREGROUND = "foreground"
    BACKGROUND = "background"
    BORDER = "border"
    ACCENT = "accent"

class StyleProperty(Enum):
    """Style properties for UI components."""
    # Basic properties
    BACKGROUND = "background"
    FOREGROUND = "color"
    BORDER = "border"
    PADDING = "padding"
    MARGIN = "margin"
    
    # Font properties
    FONT = "font"
    FONT_SIZE = "font-size"
    FONT_WEIGHT = "font-weight"
    FONT_STYLE = "font-style"
    
    # Layout properties
    WIDTH = "width"
    HEIGHT = "height"
    MIN_WIDTH = "min-width"
    MIN_HEIGHT = "min-height"
    MAX_WIDTH = "max-width"
    MAX_HEIGHT = "max-height"
    ALIGNMENT = "alignment"
    SPACING = "spacing"
    
    # Position properties
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

from .style_enums import ColorScheme, StyleClass, StyleProperty

class BaseStyles:
    """Базовые стили для всех виджетов"""
    
    @staticmethod
    def get_base_style() -> str:
        return f"""
            QWidget {{
                background: {ColorScheme.BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
                border: none;
            }}
            
            QMainWindow {{
                background: {ColorScheme.BACKGROUND.value};
            }}
            
            QMenuBar {{
                background: {ColorScheme.MENU_BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
                border-bottom: 1px solid {ColorScheme.MENU_BORDER.value};
            }}
            
            QMenuBar::item:selected {{
                background: {ColorScheme.MENU_HOVER.value};
            }}
            
            QMenu {{
                background: {ColorScheme.MENU_BACKGROUND.value};
                border: 1px solid {ColorScheme.MENU_BORDER.value};
            }}
            
            QMenu::item:selected {{
                background: {ColorScheme.MENU_HOVER.value};
            }}
            
            QToolBar {{
                background: {ColorScheme.MENU_BACKGROUND.value};
                border: none;
                spacing: 3px;
            }}
            
            QStatusBar {{
                background: {ColorScheme.MENU_BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
            }}
            
            QDockWidget {{
                titlebar-close-icon: url(resources/icons/close.svg);
                titlebar-normal-icon: url(resources/icons/dock.svg);
            }}
            
            QDockWidget::title {{
                background: {ColorScheme.MENU_BACKGROUND.value};
                padding-left: 5px;
                padding-top: 2px;
            }}
            
            QTabWidget::pane {{
                border: 1px solid {ColorScheme.MENU_BORDER.value};
            }}
            
            QTabBar::tab {{
                background: {ColorScheme.MENU_BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
                padding: 5px 10px;
                border: none;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background: {ColorScheme.ACCENT.value};
            }}
            
            QProgressBar {{
                border: 1px solid {ColorScheme.MENU_BORDER.value};
                border-radius: 2px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background: {ColorScheme.ACCENT.value};
            }}
            
            QPushButton {{
                background: {ColorScheme.MENU_BACKGROUND.value};
                border: 1px solid {ColorScheme.MENU_BORDER.value};
                padding: 5px 15px;
                border-radius: 2px;
            }}
            
            QPushButton:hover {{
                background: {ColorScheme.MENU_HOVER.value};
            }}
            
            QLineEdit {{
                background: {ColorScheme.EDITOR_BACKGROUND.value};
                border: 1px solid {ColorScheme.MENU_BORDER.value};
                padding: 3px;
                border-radius: 2px;
            }}
            
            QComboBox {{
                background: {ColorScheme.MENU_BACKGROUND.value};
                border: 1px solid {ColorScheme.MENU_BORDER.value};
                padding: 3px;
                border-radius: 2px;
            }}
            
            QScrollBar:vertical {{
                background: {ColorScheme.BACKGROUND.value};
                width: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {ColorScheme.MENU_BACKGROUND.value};
                min-height: 20px;
                border-radius: 6px;
            }}
            
            QScrollBar:horizontal {{
                background: {ColorScheme.BACKGROUND.value};
                height: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: {ColorScheme.MENU_BACKGROUND.value};
                min-width: 20px;
                border-radius: 6px;
            }}
        """

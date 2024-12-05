from .style_enums import ColorScheme, StyleClass

class PerformanceMonitorStyles:
    """Стили для виджета мониторинга производительности"""
    
    @staticmethod
    def get_style() -> str:
        return f"""
            QWidget#performanceMonitor {{
                background: {ColorScheme.BACKGROUND.value};
                padding: 10px;
            }}
            
            QLabel#statsLabel {{
                font-size: 12px;
                color: {ColorScheme.STATUS_INFO.value};
            }}
            
            QProgressBar#memoryBar {{
                border: 1px solid {ColorScheme.MENU_BORDER.value};
                border-radius: 2px;
                text-align: center;
            }}
            
            QProgressBar#memoryBar::chunk {{
                background: {ColorScheme.STATUS_INFO.value};
            }}
            
            QProgressBar#cpuBar {{
                border: 1px solid {ColorScheme.MENU_BORDER.value};
                border-radius: 2px;
                text-align: center;
            }}
            
            QProgressBar#cpuBar::chunk {{
                background: {ColorScheme.STATUS_WARNING.value};
            }}
        """

class ProjectExplorerStyles:
    """Стили для проводника проекта"""
    
    @staticmethod
    def get_style() -> str:
        return f"""
            QTreeView {{
                background: {ColorScheme.TREE_BACKGROUND.value};
                border: none;
                show-decoration-selected: 1;
            }}
            
            QTreeView::item {{
                padding: 2px;
            }}
            
            QTreeView::item:hover {{
                background: {ColorScheme.TREE_ITEM_HOVER.value};
            }}
            
            QTreeView::item:selected {{
                background: {ColorScheme.TREE_ITEM_SELECTED.value};
            }}
            
            QTreeView::branch:has-siblings:!adjoins-item {{
                border-image: url(src/ui/resources/icons/vline.svg) 0;
            }}
            
            QTreeView::branch:has-siblings:adjoins-item {{
                border-image: url(src/ui/resources/icons/branch-more.svg) 0;
            }}
            
            QTreeView::branch:!has-children:!has-siblings:adjoins-item {{
                border-image: url(src/ui/resources/icons/branch-end.svg) 0;
            }}
        """

class EditorStyles:
    """Стили для редактора кода"""
    
    @staticmethod
    def get_style() -> str:
        return f"""
            QPlainTextEdit {{
                background: {ColorScheme.EDITOR_BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
                selection-background-color: {ColorScheme.EDITOR_SELECTION.value};
                selection-color: {ColorScheme.FOREGROUND.value};
            }}
            
            QWidget#lineNumberArea {{
                background: {ColorScheme.EDITOR_BACKGROUND.value};
                border-right: 1px solid {ColorScheme.MENU_BORDER.value};
            }}
        """

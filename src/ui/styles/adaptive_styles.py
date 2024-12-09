"""Адаптивные стили для компонентов"""
from typing import Dict
from .theme_manager import ThemeManager, ColorRole
import logging

class AdaptiveStyles:
    """Генератор адаптивных стилей"""
    
    # Cache for generated styles
    _style_cache = {}
    
    # Default font settings
    DEFAULT_FONT_FAMILY = "Segoe UI"
    DEFAULT_FONT_SIZE = "12px"
    FALLBACK_FONTS = ["Arial", "sans-serif"]
    
    # Default colors for fallback
    FALLBACK_COLORS = {
        "background": "#2D2D2D",
        "on_background": "#FFFFFF",
        "surface": "#363636",
        "on_surface": "#FFFFFF",
        "primary": "#007ACC",
        "on_primary": "#FFFFFF",
        "border": "#404040"
    }

    @staticmethod
    def get_base_style(theme: ThemeManager) -> str:
        """Базовые стили приложения"""
        try:
            # Validate theme manager
            if not isinstance(theme, ThemeManager):
                raise ValueError("Invalid theme manager provided")
                
            # Check cache
            cache_key = hash(str(theme.get_palette()))
            if cache_key in AdaptiveStyles._style_cache:
                return AdaptiveStyles._style_cache[cache_key]
            
            # Get colors with fallbacks
            def get_color_safe(role: ColorRole) -> str:
                try:
                    return theme.get_color(role)
                except Exception:
                    role_name = role.name.lower()
                    return AdaptiveStyles.FALLBACK_COLORS.get(role_name, "#000000")
            
            # Build font string with fallbacks
            font_family = f'"{AdaptiveStyles.DEFAULT_FONT_FAMILY}", ' + \
                         ', '.join(f'"{font}"' for font in AdaptiveStyles.FALLBACK_FONTS)
            
            # Generate style
            style = f"""
                QMainWindow {{
                    background-color: {get_color_safe(ColorRole.BACKGROUND)};
                    color: {get_color_safe(ColorRole.ON_BACKGROUND)};
                }}
                
                QWidget {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    color: {get_color_safe(ColorRole.ON_SURFACE)};
                    font-family: {font_family};
                    font-size: {AdaptiveStyles.DEFAULT_FONT_SIZE};
                }}
                
                QMenuBar {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    color: {get_color_safe(ColorRole.ON_SURFACE)};
                    border-bottom: 1px solid {get_color_safe(ColorRole.BORDER)};
                    padding: 2px;
                }}
                
                QMenuBar::item {{
                    background-color: transparent;
                    padding: 4px 8px;
                    border-radius: 4px;
                }}
                
                QMenuBar::item:selected {{
                    background-color: {get_color_safe(ColorRole.PRIMARY)};
                    color: {get_color_safe(ColorRole.ON_PRIMARY)};
                }}
                
                QMenu {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    border: 1px solid {get_color_safe(ColorRole.BORDER)};
                    border-radius: 4px;
                    padding: 4px;
                }}
                
                QMenu::item {{
                    padding: 4px 24px;
                    border-radius: 2px;
                }}
                
                QMenu::item:selected {{
                    background-color: {get_color_safe(ColorRole.PRIMARY)};
                    color: {get_color_safe(ColorRole.ON_PRIMARY)};
                }}
                
                QPushButton {{
                    background-color: {get_color_safe(ColorRole.PRIMARY)};
                    color: {get_color_safe(ColorRole.ON_PRIMARY)};
                    border: none;
                    border-radius: 4px;
                    padding: 6px 16px;
                    font-weight: bold;
                }}
                
                QPushButton:hover {{
                    background-color: {get_color_safe(ColorRole.ACCENT)};
                }}
                
                QPushButton:pressed {{
                    background-color: {get_color_safe(ColorRole.SECONDARY)};
                }}
                
                QPushButton:disabled {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    color: {get_color_safe(ColorRole.BORDER)};
                }}
                
                QLineEdit {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    color: {get_color_safe(ColorRole.ON_SURFACE)};
                    border: 1px solid {get_color_safe(ColorRole.BORDER)};
                    border-radius: 4px;
                    padding: 4px 8px;
                }}
                
                QLineEdit:focus {{
                    border-color: {get_color_safe(ColorRole.PRIMARY)};
                }}
                
                QTabWidget::pane {{
                    border: 1px solid {get_color_safe(ColorRole.BORDER)};
                    border-radius: 4px;
                }}
                
                QTabBar::tab {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    color: {get_color_safe(ColorRole.ON_SURFACE)};
                    border: 1px solid {get_color_safe(ColorRole.BORDER)};
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    padding: 6px 12px;
                    margin-right: 2px;
                }}
                
                QTabBar::tab:selected {{
                    background-color: {get_color_safe(ColorRole.PRIMARY)};
                    color: {get_color_safe(ColorRole.ON_PRIMARY)};
                }}
                
                QScrollBar:vertical {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    width: 12px;
                    margin: 0;
                }}
                
                QScrollBar::handle:vertical {{
                    background-color: {get_color_safe(ColorRole.BORDER)};
                    border-radius: 6px;
                    min-height: 20px;
                    margin: 2px;
                }}
                
                QScrollBar::handle:vertical:hover {{
                    background-color: {get_color_safe(ColorRole.PRIMARY)};
                }}
                
                QScrollBar:horizontal {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    height: 12px;
                    margin: 0;
                }}
                
                QScrollBar::handle:horizontal {{
                    background-color: {get_color_safe(ColorRole.BORDER)};
                    border-radius: 6px;
                    min-width: 20px;
                    margin: 2px;
                }}
                
                QScrollBar::handle:horizontal:hover {{
                    background-color: {get_color_safe(ColorRole.PRIMARY)};
                }}
                
                QDockWidget {{
                    titlebar-close-icon: url(close.png);
                    titlebar-normal-icon: url(float.png);
                }}
                
                QDockWidget::title {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    padding: 6px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }}
                
                QStatusBar {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    color: {get_color_safe(ColorRole.ON_SURFACE)};
                    border-top: 1px solid {get_color_safe(ColorRole.BORDER)};
                }}
            """
            
            # Cache the generated style
            AdaptiveStyles._style_cache[cache_key] = style
            return style
            
        except Exception as e:
            logging.error(f"Error generating adaptive styles: {str(e)}", exc_info=True)
            # Return a minimal fallback style
            return """
                QMainWindow, QWidget {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                    font-family: "Segoe UI", Arial, sans-serif;
                }
            """
    
    @classmethod
    def clear_cache(cls):
        """Clear the style cache"""
        cls._style_cache.clear()

    @staticmethod
    def get_code_editor_style(theme: ThemeManager) -> str:
        """Стили для редактора кода"""
        try:
            # Validate theme manager
            if not isinstance(theme, ThemeManager):
                raise ValueError("Invalid theme manager provided")
                
            # Get colors with fallbacks
            def get_color_safe(role: ColorRole) -> str:
                try:
                    return theme.get_color(role)
                except Exception:
                    role_name = role.name.lower()
                    return AdaptiveStyles.FALLBACK_COLORS.get(role_name, "#000000")
            
            # Generate style
            style = f"""
                QPlainTextEdit {{
                    background-color: {get_color_safe(ColorRole.BACKGROUND)};
                    color: {get_color_safe(ColorRole.ON_BACKGROUND)};
                    border: none;
                    font-family: "Cascadia Code", "Fira Code", monospace;
                    font-size: 13px;
                    line-height: 1.5;
                }}
                
                QPlainTextEdit[readOnly="true"] {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                }}
            """
            return style
            
        except Exception as e:
            logging.error(f"Error generating code editor styles: {str(e)}", exc_info=True)
            # Return a minimal fallback style
            return """
                QPlainTextEdit {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                    font-family: "Cascadia Code", "Fira Code", monospace;
                }
            """

    @staticmethod
    def get_project_explorer_style(theme: ThemeManager) -> str:
        """Стили для проводника проекта"""
        try:
            # Validate theme manager
            if not isinstance(theme, ThemeManager):
                raise ValueError("Invalid theme manager provided")
                
            # Get colors with fallbacks
            def get_color_safe(role: ColorRole) -> str:
                try:
                    return theme.get_color(role)
                except Exception:
                    role_name = role.name.lower()
                    return AdaptiveStyles.FALLBACK_COLORS.get(role_name, "#000000")
            
            # Generate style
            style = f"""
                QTreeView {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    border: none;
                    padding: 4px;
                }}
                
                QTreeView::item {{
                    padding: 4px;
                    border-radius: 4px;
                }}
                
                QTreeView::item:selected {{
                    background-color: {get_color_safe(ColorRole.PRIMARY)};
                    color: {get_color_safe(ColorRole.ON_PRIMARY)};
                }}
                
                QTreeView::branch {{
                    background-color: transparent;
                }}
                
                QTreeView::branch:has-siblings:!adjoins-item {{
                    border-image: url(vline.png) 0;
                }}
                
                QTreeView::branch:has-siblings:adjoins-item {{
                    border-image: url(branch-more.png) 0;
                }}
                
                QTreeView::branch:!has-children:!has-siblings:adjoins-item {{
                    border-image: url(branch-end.png) 0;
                }}
            """
            return style
            
        except Exception as e:
            logging.error(f"Error generating project explorer styles: {str(e)}", exc_info=True)
            # Return a minimal fallback style
            return """
                QTreeView {
                    background-color: #363636;
                    border: none;
                    padding: 4px;
                }
            """

    @staticmethod
    def get_performance_monitor_style(theme: ThemeManager) -> str:
        """Стили для монитора производительности"""
        try:
            # Validate theme manager
            if not isinstance(theme, ThemeManager):
                raise ValueError("Invalid theme manager provided")
                
            # Get colors with fallbacks
            def get_color_safe(role: ColorRole) -> str:
                try:
                    return theme.get_color(role)
                except Exception:
                    role_name = role.name.lower()
                    return AdaptiveStyles.FALLBACK_COLORS.get(role_name, "#000000")
            
            # Generate style
            style = f"""
                QWidget#PerformanceWidget {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    border-radius: 8px;
                    padding: 8px;
                }}
                
                QLabel#PerformanceLabel {{
                    color: {get_color_safe(ColorRole.ON_SURFACE)};
                    font-weight: bold;
                }}
                
                QProgressBar {{
                    background-color: {get_color_safe(ColorRole.BACKGROUND)};
                    border: none;
                    border-radius: 4px;
                    text-align: center;
                }}
                
                QProgressBar::chunk {{
                    background-color: {get_color_safe(ColorRole.PRIMARY)};
                    border-radius: 4px;
                }}
            """
            return style
            
        except Exception as e:
            logging.error(f"Error generating performance monitor styles: {str(e)}", exc_info=True)
            # Return a minimal fallback style
            return """
                QWidget#PerformanceWidget {
                    background-color: #363636;
                    border-radius: 8px;
                    padding: 8px;
                }
            """

    @staticmethod
    def get_network_visualizer_style(theme: ThemeManager) -> str:
        """Стили для визуализатора нейронной сети"""
        try:
            # Validate theme manager
            if not isinstance(theme, ThemeManager):
                raise ValueError("Invalid theme manager provided")
                
            # Get colors with fallbacks
            def get_color_safe(role: ColorRole) -> str:
                try:
                    return theme.get_color(role)
                except Exception:
                    role_name = role.name.lower()
                    return AdaptiveStyles.FALLBACK_COLORS.get(role_name, "#000000")
            
            # Generate style
            style = f"""
                QGraphicsView {{
                    background-color: {get_color_safe(ColorRole.BACKGROUND)};
                    border: none;
                }}
                
                QLabel#LayerLabel {{
                    background-color: {get_color_safe(ColorRole.SURFACE)};
                    color: {get_color_safe(ColorRole.ON_SURFACE)};
                    border: 1px solid {get_color_safe(ColorRole.BORDER)};
                    border-radius: 4px;
                    padding: 4px 8px;
                }}
            """
            return style
            
        except Exception as e:
            logging.error(f"Error generating network visualizer styles: {str(e)}", exc_info=True)
            # Return a minimal fallback style
            return """
                QGraphicsView {
                    background-color: #2D2D2D;
                    border: none;
                }
            """

    @staticmethod
    def get_text_style(theme: ThemeManager) -> str:
        """Get style for text components"""
        try:
            # Get base colors
            background = theme.get_color(ColorRole.BACKGROUND)
            text_color = theme.get_color(ColorRole.ON_BACKGROUND)
            border = theme.get_color(ColorRole.BORDER)
            
            style = f"""
                QTextEdit, QPlainTextEdit {{
                    background-color: {background};
                    color: {text_color};
                    border: 1px solid {border};
                    border-radius: 4px;
                    padding: 8px;
                    font-family: {AdaptiveStyles.DEFAULT_FONT_FAMILY}, {', '.join(AdaptiveStyles.FALLBACK_FONTS)};
                    font-size: {AdaptiveStyles.DEFAULT_FONT_SIZE};
                    selection-background-color: {theme.get_color(ColorRole.PRIMARY)};
                    selection-color: {theme.get_color(ColorRole.ON_PRIMARY)};
                }}
                
                QTextEdit:focus, QPlainTextEdit:focus {{
                    border: 2px solid {theme.get_color(ColorRole.PRIMARY)};
                }}
            """
            return style
            
        except Exception as e:
            logging.error(f"Error generating text style: {str(e)}", exc_info=True)
            return ""

    @staticmethod
    def get_button_style(theme: ThemeManager) -> str:
        """Get style for button components"""
        try:
            # Get base colors
            primary = theme.get_color(ColorRole.PRIMARY)
            on_primary = theme.get_color(ColorRole.ON_PRIMARY)
            surface = theme.get_color(ColorRole.SURFACE)
            on_surface = theme.get_color(ColorRole.ON_SURFACE)
            border = theme.get_color(ColorRole.BORDER)
            
            style = f"""
                QPushButton {{
                    background-color: {surface};
                    color: {on_surface};
                    border: 1px solid {border};
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-family: {AdaptiveStyles.DEFAULT_FONT_FAMILY}, {', '.join(AdaptiveStyles.FALLBACK_FONTS)};
                    font-size: {AdaptiveStyles.DEFAULT_FONT_SIZE};
                    min-width: 80px;
                }}
                
                QPushButton:hover {{
                    background-color: {primary};
                    color: {on_primary};
                    border: 1px solid {primary};
                }}
                
                QPushButton:pressed {{
                    background-color: {theme.get_color(ColorRole.BORDER)};
                    border: 1px solid {theme.get_color(ColorRole.BORDER)};
                    padding: 7px 11px 5px 13px;
                }}
                
                QPushButton:disabled {{
                    background-color: {surface};
                    color: {theme.get_color(ColorRole.BORDER)};
                    border: 1px solid {theme.get_color(ColorRole.BORDER)};
                }}
                
                QPushButton:checked {{
                    background-color: {primary};
                    color: {on_primary};
                    border: 1px solid {primary};
                }}
            """
            return style
            
        except Exception as e:
            logging.error(f"Error generating button style: {str(e)}", exc_info=True)
            return ""

    @staticmethod
    def get_table_style(theme: ThemeManager) -> str:
        """Get style for table components"""
        try:
            # Get base colors
            background = theme.get_color(ColorRole.BACKGROUND)
            surface = theme.get_color(ColorRole.SURFACE)
            text_color = theme.get_color(ColorRole.ON_SURFACE)
            border = theme.get_color(ColorRole.BORDER)
            primary = theme.get_color(ColorRole.PRIMARY)
            on_primary = theme.get_color(ColorRole.ON_PRIMARY)
            
            style = f"""
                QTableWidget, QTableView {{
                    background-color: {background};
                    color: {text_color};
                    border: 1px solid {border};
                    border-radius: 4px;
                    gridline-color: {border};
                    font-family: {AdaptiveStyles.DEFAULT_FONT_FAMILY}, {', '.join(AdaptiveStyles.FALLBACK_FONTS)};
                    font-size: {AdaptiveStyles.DEFAULT_FONT_SIZE};
                }}
                
                QTableWidget::item, QTableView::item {{
                    padding: 5px;
                    border: none;
                }}
                
                QTableWidget::item:selected, QTableView::item:selected {{
                    background-color: {primary};
                    color: {on_primary};
                }}
                
                QHeaderView::section {{
                    background-color: {surface};
                    color: {text_color};
                    padding: 5px;
                    border: none;
                    border-right: 1px solid {border};
                    border-bottom: 1px solid {border};
                    font-weight: bold;
                }}
                
                QHeaderView::section:checked {{
                    background-color: {primary};
                    color: {on_primary};
                }}
                
                QHeaderView::section:horizontal {{
                    border-top: none;
                }}
                
                QHeaderView::section:vertical {{
                    border-left: none;
                }}
                
                QTableWidget::item:hover, QTableView::item:hover {{
                    background-color: {surface};
                }}
                
                QScrollBar:vertical {{
                    background: {background};
                    width: 12px;
                    margin: 0px;
                }}
                
                QScrollBar::handle:vertical {{
                    background: {border};
                    min-height: 20px;
                    border-radius: 6px;
                }}
                
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
                
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: none;
                }}
                
                QScrollBar:horizontal {{
                    background: {background};
                    height: 12px;
                    margin: 0px;
                }}
                
                QScrollBar::handle:horizontal {{
                    background: {border};
                    min-width: 20px;
                    border-radius: 6px;
                }}
                
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                    width: 0px;
                }}
                
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                    background: none;
                }}
            """
            return style
            
        except Exception as e:
            logging.error(f"Error generating table style: {str(e)}", exc_info=True)
            return ""

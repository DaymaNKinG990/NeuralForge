from typing import Dict
from .style_enums import ThemeType, StyleClass, ColorScheme
from .base_styles import BaseStyles
from .component_styles import (
    PerformanceMonitorStyles,
    ProjectExplorerStyles,
    EditorStyles
)

class StyleManager:
    """Менеджер стилей приложения"""
    
    def __init__(self):
        self._current_theme = ThemeType.DARK
        self._style_cache: Dict[StyleClass, str] = {}
        
    @property
    def current_theme(self) -> ThemeType:
        return self._current_theme
    
    def set_theme(self, theme: ThemeType) -> None:
        """Установить тему оформления"""
        self._current_theme = theme
        self._style_cache.clear()  # Сбрасываем кэш при смене темы
        
    def get_base_style(self) -> str:
        """Получить базовые стили"""
        return BaseStyles.get_base_style()
    
    def get_performance_monitor_style(self) -> str:
        """Получить стили для монитора производительности"""
        return PerformanceMonitorStyles.get_style()
    
    def get_project_explorer_style(self) -> str:
        """Получить стили для проводника проекта"""
        return ProjectExplorerStyles.get_style()
    
    def get_editor_style(self) -> str:
        """Получить стили для редактора"""
        return EditorStyles.get_style()
    
    def get_component_style(self, style_class: StyleClass) -> str:
        """Получить стиль для конкретного компонента"""
        if style_class not in self._style_cache:
            style = self._generate_component_style(style_class)
            self._style_cache[style_class] = style
        return self._style_cache[style_class]
    
    def _generate_component_style(self, style_class: StyleClass) -> str:
        """Генерация стиля для компонента"""
        style_map = {
            StyleClass.MAIN_WINDOW: self.get_base_style(),
            StyleClass.DOCK_WIDGET: self.get_performance_monitor_style(),
            StyleClass.TREE_VIEW: self.get_project_explorer_style(),
            StyleClass.TAB_WIDGET: self.get_editor_style(),
        }
        return style_map.get(style_class, "")

    def get_color(self, color_class: StyleClass) -> str:
        """Get color value for a style class.
        
        Args:
            color_class: Style class to get color for
            
        Returns:
            str: Color value in hex format
        """
        color_map = {
            StyleClass.EDITOR_BACKGROUND: ColorScheme.EDITOR_BACKGROUND.value,
            StyleClass.FOREGROUND: ColorScheme.FOREGROUND.value,
            StyleClass.EDITOR_SELECTION: ColorScheme.EDITOR_SELECTION.value,
            StyleClass.LINE_NUMBER_BG: ColorScheme.LINE_NUMBER_BG.value,
            StyleClass.LINE_NUMBER_FG: ColorScheme.LINE_NUMBER_FG.value,
            StyleClass.EDITOR_CURRENT_LINE: ColorScheme.EDITOR_CURRENT_LINE.value,
        }
        
        return color_map.get(color_class, ColorScheme.FOREGROUND.value)

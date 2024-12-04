import sys
import os
import logging
import logging.config
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QLoggingCategory, QThread
from src.ui.main_window import MainWindow
from config.debug_config import DEBUG_CONFIG

def setup_logging():
    """Настройка системы логирования"""
    logging.config.dictConfig(DEBUG_CONFIG['logging'])
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized in debug mode")

def setup_qt_debug():
    """Настройка отладочных флагов Qt"""
    for flag in DEBUG_CONFIG['qt']['debug_flags']:
        QLoggingCategory.setFilterRules(f"qt.{flag.lower()}=true")

def main():
    # Инициализация логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Создание директории для логов если её нет
        os.makedirs('logs', exist_ok=True)
        
        # Инициализация приложения
        app = QApplication(sys.argv)
        
        # Настройка отладки Qt
        setup_qt_debug()
        
        # Создание главного окна
        window = MainWindow()
        window.show()
        
        # Убедимся, что окно отображается
        window.raise_()
        window.activateWindow()
        
        logger.info("Application started successfully")
        return app.exec()
        
    except Exception as e:
        logger.exception(f"Fatal error occurred: {str(e)}")
        raise

if __name__ == '__main__':
    sys.exit(main())

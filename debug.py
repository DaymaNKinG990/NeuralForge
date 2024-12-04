"""
Скрипт для запуска приложения в режиме отладки
"""
import os
import sys
import pdb
import logging
from PyQt6.QtCore import QThread, QObject, QTimer
from PyQt6.QtWidgets import QWidget
from main import main

def debug_widget_info(widget: QWidget) -> None:
    """Вывести отладочную информацию о виджете"""
    logger = logging.getLogger(__name__)
    logger.debug(f"Widget: {widget.__class__.__name__}")
    logger.debug(f"Parent: {widget.parent().__class__.__name__ if widget.parent() else 'None'}")
    logger.debug(f"Visible: {widget.isVisible()}")
    logger.debug(f"Window flags: {widget.windowFlags()}")
    logger.debug(f"Geometry: {widget.geometry()}")
    logger.debug(f"Thread: {QThread.currentThread().objectName()}")

def debug_qt_threads() -> None:
    """Вывести информацию о текущих Qt потоках"""
    logger = logging.getLogger(__name__)
    main_thread = QThread.currentThread()
    logger.debug(f"Main thread: {main_thread.objectName()}")
    logger.debug(f"Current thread: {QThread.currentThread().objectName()}")

if __name__ == '__main__':
    # Установка переменных окружения для debug режима
    os.environ['NEURALFORGE_DEBUG'] = '1'
    os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Включаем отладочный режим Python
        sys.excepthook = lambda type, value, traceback: pdb.post_mortem(traceback)
        
        # Настраиваем логирование для Qt
        logging.basicConfig(level=logging.DEBUG)
        
        # Запускаем приложение с отладочной информацией
        debug_qt_threads()
        main()
    except Exception as e:
        logging.exception("Error in debug mode")
        pdb.post_mortem()

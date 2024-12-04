"""
Конфигурация для debug режима
"""

DEBUG_CONFIG = {
    # Логирование
    'logging': {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': 'debug.log',
                'level': 'DEBUG',
                'formatter': 'detailed',
            }
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    },
    
    # Отладка PyQt
    'qt': {
        'debug_flags': [
            'DEBUG_FLAG_DISABLE_RENDER_CACHING',
            'DEBUG_FLAG_SHOW_UPDATES',
            'DEBUG_FLAG_SHOW_DIRTY'
        ]
    },
    
    # Кэширование
    'caching': {
        'enable_debug_info': True,
        'log_cache_operations': True,
        'max_memory_size': '1GB',
        'cleanup_interval': 300
    },
    
    # Профилирование
    'profiling': {
        'enabled': True,
        'log_threshold_ms': 100,
        'sample_interval': 0.1
    },
    
    # Мониторинг ресурсов
    'resource_monitoring': {
        'enabled': True,
        'update_interval': 1.0,
        'warning_threshold': 0.8
    }
}

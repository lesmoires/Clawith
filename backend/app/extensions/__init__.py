"""
Clawith Custom Extensions

This module provides custom extensions for Clawith that are not part of
the upstream OpenClaw project.
"""

from loguru import logger


def load_extensions():
    """
    Load all Clawith custom extensions.
    
    Extensions are loaded in alphabetical order. Each extension should
    have a `register_extension()` function that will be called automatically.
    """
    import importlib
    import pkgutil
    
    logger.info("[Extensions] Loading Clawith custom extensions...")
    
    # Get all modules in this package
    for _, name, _ in pkgutil.iter_modules(__path__):
        if name != '__init__':
            try:
                module = importlib.import_module(f'app.extensions.{name}')
                if hasattr(module, 'register_extension'):
                    module.register_extension()
            except Exception as e:
                logger.error(f"[Extensions] Failed to load extension {name}: {e}")
                raise
    
    logger.info("[Extensions] All extensions loaded")

"""Git panel package for version control integration."""
from .panel import GitPanel
from .dialogs import CommitDialog, CloneDialog, RemoteManagerDialog

__all__ = [
    'GitPanel',
    'CommitDialog',
    'CloneDialog',
    'RemoteManagerDialog'
]

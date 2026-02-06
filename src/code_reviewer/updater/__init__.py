"""Módulo de auto-update para verificação e atualização de versões."""

from .version_check import check_for_update, clear_cache, UpdateInfo
from .notifier import notify_update
from .upgrade import detect_installer, run_upgrade

__all__ = [
    "check_for_update",
    "clear_cache",
    "UpdateInfo",
    "notify_update",
    "detect_installer",
    "run_upgrade",
]

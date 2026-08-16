from Developer.utilities.development_backup_dialog import (
	DevelopmentBackupDialog as BaseDevelopmentBackupDialog,
)


class DevelopmentBackupDialog(BaseDevelopmentBackupDialog):
	"""Backup/Restore service supplied by the Developer Services extension."""

__all__ = ["DevelopmentBackupDialog"]
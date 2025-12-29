"""
Backward-compatible wrapper for EnhancedReportService.

The report service has been modularized into api/services/report/
This file maintains backward compatibility for existing imports.
"""
# Import from the new modular structure
from .report import EnhancedReportService

# Re-export for backward compatibility
__all__ = ['EnhancedReportService']

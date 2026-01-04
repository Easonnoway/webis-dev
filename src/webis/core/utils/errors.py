import sys
import traceback
from typing import Optional

class WebisError(Exception):
    """Base class for Webis exceptions."""
    def __init__(self, message: str, suggestion: Optional[str] = None, code: str = "WEBIS_ERR"):
        self.message = message
        self.suggestion = suggestion
        self.code = code
        super().__init__(message)

def print_friendly_error(e: Exception):
    """
    Prints a user-friendly error message with suggestions.
    """
    if isinstance(e, WebisError):
        print(f"\n❌ Error [{e.code}]: {e.message}")
        if e.suggestion:
            print(f"💡 Suggestion: {e.suggestion}")
    else:
        # Generic error
        print(f"\n❌ Unexpected Error: {str(e)}")
        print("💡 Suggestion: Check the logs for full traceback or run with --debug.")
        
    # In debug mode, print full traceback
    # if is_debug:
    #     traceback.print_exc()

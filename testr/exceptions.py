# core/exceptions.py
class TestrError(Exception):
    """Base framework exception"""
    
class ElementNotFoundError(TestrError):
    """Raised when text/image not found on screen"""
    
class ApplicationLaunchError(TestrError):
    """Raised when app fails to launch"""
# core/utils.py
import platform
import os

class CrossPlatformUtils:
    @staticmethod
    def get_os():
        return platform.system()
    
    @staticmethod
    def convert_path(path):
        """Handle OS-specific path formatting"""
        if CrossPlatformUtils.get_os() == 'Windows':
            return path.replace('/', '\\')
        return path
    
    @staticmethod
    def get_special_key(key):
        """Handle OS-specific special keys"""
        modifier_keys = {
            'command': 'win' if CrossPlatformUtils.get_os() == 'Windows' else 'command'
        }
        return modifier_keys.get(key.lower(), key)
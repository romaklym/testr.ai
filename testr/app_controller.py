# core/app_controller.py
import subprocess
import platform
import os
import winreg
from pathlib import Path
from .exceptions import ApplicationLaunchError
from .logger import log_action

class AppController:
    def __init__(self, parent):
        self.parent = parent
        print("AppController initialized")

    @log_action
    def find_executable_path(self, app_name):
        """Find the executable path for an application on Windows
        
        Args:
            app_name: Name of the application (with or without .exe)
        """
        # Ensure app_name has .exe extension
        if not app_name.lower().endswith('.exe'):
            app_name = f"{app_name}.exe"

        # Common installation directories to search
        search_paths = [
            os.environ.get('PROGRAMFILES', 'C:/Program Files'),
            os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)'),
            os.environ.get('LOCALAPPDATA', ''),
            os.environ.get('APPDATA', ''),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs'),
            os.path.join(os.environ.get('APPDATA', ''), 'Programs'),
            'C:/Program Files/WindowsApps'
        ]

        # First, try to find in PATH
        if platform.system() == 'Windows':
            try:
                result = subprocess.run(['where', app_name], 
                                     capture_output=True, 
                                     text=True)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            except subprocess.SubprocessError:
                pass

        # Search in common installation directories
        for base_path in search_paths:
            if not base_path:
                continue
                
            for root, _, files in os.walk(base_path):
                if app_name.lower() in (f.lower() for f in files):
                    return os.path.join(root, app_name)

        # Try to find in Windows Registry
        try:
            for hkey in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                for key_path in (
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
                ):
                    try:
                        key = winreg.OpenKey(hkey, key_path)
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                if app_name.lower() in subkey_name.lower():
                                    subkey = winreg.OpenKey(key, subkey_name)
                                    path = winreg.QueryValue(subkey, None)
                                    if path and os.path.exists(path):
                                        return path
                            except WindowsError:
                                continue
                    except WindowsError:
                        continue
        except Exception:
            pass

        return None

    @log_action
    def launch_app(self, app_name_or_path, as_admin=False):
        """Launch application by name or path
        
        Args:
            app_name_or_path: Name of the application (e.g., 'chrome', 'windsurf') 
                            or full path to executable
            as_admin: If True, launches the application with administrator privileges (Windows only)
        """
        try:
            # If it's a full path or contains directory separators, use it directly
            if os.path.isfile(app_name_or_path) or '/' in app_name_or_path or '\\' in app_name_or_path:
                app_path = app_name_or_path
            else:
                # Try to find the executable path
                app_path = self.find_executable_path(app_name_or_path)
                if not app_path:
                    raise ApplicationLaunchError(f"Could not find executable for: {app_name_or_path}")

            print(f"Launching application: {app_path}")
            
            if platform.system() == 'Windows':
                print("Detected Windows OS")
                if as_admin:
                    print("Launching with administrator privileges")
                    # Use ctypes to launch with admin privileges via ShellExecute
                    import ctypes
                    if not ctypes.windll.shell32.ShellExecuteW(None, "runas", app_path, None, None, 1):
                        raise ApplicationLaunchError("Failed to launch with admin privileges")
                else:
                    subprocess.Popen(app_path, shell=True)
            elif platform.system() == 'Darwin':
                print("Detected macOS")
                if as_admin:
                    print("Launching with sudo (will require password)")
                    subprocess.Popen(['sudo', 'open', app_path])
                else:
                    subprocess.Popen(['open', app_path])
                
            print(f"Successfully launched: {app_path}")
            return self.parent
            
        except Exception as e:
            print(f"ERROR launching app: {str(e)}")
            raise ApplicationLaunchError(f"Failed to launch app: {str(e)}")

    @log_action
    def close_app(self, app_name):
        """Close application by process name"""
        try:
            # Ensure app_name has .exe extension on Windows
            if platform.system() == 'Windows' and not app_name.lower().endswith('.exe'):
                app_name = f"{app_name}.exe"

            print(f"Attempting to close application: {app_name}")
            if platform.system() == 'Windows':
                print(f"Killing process on Windows: {app_name}")
                subprocess.run(['taskkill', '/F', '/IM', app_name], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
            elif platform.system() == 'Darwin':
                print(f"Killing process on macOS: {app_name}")
                subprocess.run(['pkill', app_name], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
            print(f"Successfully closed: {app_name}")
            return self.parent
        except Exception as e:
            print(f"ERROR closing app: {str(e)}")
            raise ApplicationLaunchError(f"Failed to close app: {str(e)}")
# core/input_simulator.py
import pyautogui
import time
import ctypes
import win32api
import win32con
from ctypes import wintypes
from .logger import log_action

# Load user32.dll
user32 = ctypes.WinDLL('user32', use_last_error=True)

# Since we're only using mouse_event and SetCursorPos, we don't need the complex INPUT structure
# Remove the SendInput related code that was causing the error
class InputSimulator:
    def __init__(self, parent):
        self.parent = parent
        self._delay = 0.1  # Default delay between actions
        pyautogui.PAUSE = self._delay
        print("InputSimulator initialized with delay:", self._delay)
    
    @log_action
    def send_mouse_event(self, x, y, event_type):
        """Send a mouse event using Win32 API"""
        # Move the mouse
        win32api.SetCursorPos((x, y))
        time.sleep(0.1)  # Small delay to ensure movement is complete
        
        # Send the mouse event
        if event_type == "click":
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            time.sleep(0.1)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        elif event_type == "down":
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        elif event_type == "up":
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
    
    @log_action 
    def move_to_text(self, text, confidence=90):
        """Move mouse to text using OCR"""
        from .screen_analyzer import ScreenAnalyzer
        position = ScreenAnalyzer().find_text_position(text, confidence)
        if position:
            x, y = position
            win32api.SetCursorPos((int(x), int(y)))

    @log_action   
    def drag_to_text(self, source_text, target_text):
        """Drag from one text position to another"""
        self.move_to_text(source_text)
        self.send_mouse_event(win32api.GetCursorPos()[0], win32api.GetCursorPos()[1], "down")
        self.move_to_text(target_text)
        self.send_mouse_event(win32api.GetCursorPos()[0], win32api.GetCursorPos()[1], "up")

    @log_action   
    def smooth_drag(self, start, end, duration=1):
        """Human-like drag motion"""
        win32api.SetCursorPos((int(start[0]), int(start[1])))
        time.sleep(0.1)
        self.send_mouse_event(int(start[0]), int(start[1]), "down")
        
        # Calculate intermediate points for smooth movement
        steps = int(duration * 10)  # 10 steps per second
        for i in range(steps):
            x = int(start[0] + (end[0] - start[0]) * i / steps)
            y = int(start[1] + (end[1] - start[1]) * i / steps)
            win32api.SetCursorPos((x, y))
            time.sleep(duration / steps)
            
        self.send_mouse_event(int(end[0]), int(end[1]), "up")
 

    @log_action
    def type(self, text):
        print(f"Typing text: '{text}'")
        pyautogui.write(text)
        return self.parent

    @log_action
    def press(self, key):
        print(f"Pressing key: '{key}'")
        pyautogui.press(key)
        return self.parent

    @log_action
    def hotkey(self, *keys):
        """Press multiple keys simultaneously
        
        Args:
            *keys: Variable number of key names to press together
                  e.g. hotkey('ctrl', 'alt', 'del') or hotkey('windows', 'r')
                  
        Common modifier keys:
            - 'ctrl' or 'control'
            - 'alt'
            - 'shift'
            - 'windows' or 'win'
            - 'command' or 'cmd' (macOS)
            - 'option' (macOS)
        """
        print(f"Pressing hotkey combination: {' + '.join(keys)}")
        pyautogui.hotkey(*keys)
        return self.parent

    @log_action
    def click(self):
        x, y = win32api.GetCursorPos()
        print(f"Clicking at position: ({x}, {y})")
        self.send_mouse_event(x, y, "click")
        return self.parent
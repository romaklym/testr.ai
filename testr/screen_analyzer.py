import cv2
import numpy as np
import pyautogui
import easyocr
from PIL import Image
import os
import time
import win32api
import win32con
from datetime import datetime
from .exceptions import ElementNotFoundError

class ScreenAnalyzer:
    def __init__(self, parent):
        self.parent = parent
        # Initialize EasyOCR reader (only need to do this once)
        print("Initializing EasyOCR (this may take a moment on first run)...")
        self.reader = easyocr.Reader(['en'])
        self.assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
        os.makedirs(self.assets_dir, exist_ok=True)

    def normalize_text(self, text):
        """Normalize text by removing spaces and converting to lowercase"""
        return ''.join(text.lower().split())

    def save_screenshot_with_highlight(self, screenshot, bbox, text):
        """Save screenshot with highlighted text area"""
        # Convert PIL image to OpenCV format
        cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Draw red rectangle around text
        x_min, y_min = bbox[0]
        x_max, y_max = bbox[2]
        cv2.rectangle(cv_image, 
                     (int(x_min), int(y_min)), 
                     (int(x_max), int(y_max)), 
                     (0, 0, 255),  # BGR color (red)
                     2)  # Thickness
        
        # Add text label above rectangle
        cv2.putText(cv_image, 
                   f'Found: {text}',
                   (int(x_min), int(y_min) - 10),
                   cv2.FONT_HERSHEY_SIMPLEX,
                   0.5,
                   (0, 0, 255),
                   1)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'text_match_{text.replace(" ", "_")}_{timestamp}.png'
        filepath = os.path.join(self.assets_dir, filename)
        
        # Save image
        cv2.imwrite(filepath, cv_image)
        print(f"Screenshot saved: {filepath}")

    def save_screenshot_with_color_highlight(self, screenshot, x, y, hex_color, radius=20):
        """Save screenshot with highlighted color match area
        
        Args:
            screenshot: PIL Image screenshot
            x, y: Coordinates of the color match
            hex_color: The hex color that was matched
            radius: Size of the highlight box
        """
        # Convert PIL image to OpenCV format
        cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Draw red rectangle around the color match
        cv2.rectangle(cv_image, 
                     (int(x - radius), int(y - radius)), 
                     (int(x + radius), int(y + radius)), 
                     (0, 0, 255),  # BGR color (red)
                     2)  # Thickness
        
        # Add color info label above rectangle
        cv2.putText(cv_image, 
                   f'Found color: {hex_color}',
                   (int(x - radius), int(y - radius - 10)),
                   cv2.FONT_HERSHEY_SIMPLEX,
                   0.5,
                   (0, 0, 255),
                   1)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'color_match_{hex_color.replace("#", "")}_{timestamp}.png'
        filepath = os.path.join(self.assets_dir, filename)
        
        # Save the image
        cv2.imwrite(filepath, cv_image)
        print(f"Screenshot saved: {filepath}")

    def get_region_screenshot(self, region=None):
        """Take a screenshot of the specified region or full screen
        
        Args:
            region: Tuple of (x, y, width, height) or None for full screen
        """
        if region is None:
            return pyautogui.screenshot()
        else:
            x, y, width, height = region
            return pyautogui.screenshot(region=(x, y, width, height))

    def find_color_position(self, hex_color, tolerance=5, max_retries=3, retry_delay=1, region=None):
        """Find position of a specific color on screen or in region
        
        Args:
            hex_color: Color in hex format (e.g. '#FF0000' for red)
            tolerance: Color matching tolerance (0-255)
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            region: Tuple of (x, y, width, height) to search within, or None for full screen
        """        
        rgb_color = self.hex_to_rgb(hex_color)
        region_offset_x = int(region[0]) if region else 0
        region_offset_y = int(region[1]) if region else 0
        
        for attempt in range(max_retries):
            try:
                print(f"\n🔍 Attempt {attempt + 1}/{max_retries} - Searching for color: {hex_color}")
                
                # Take screenshot
                screenshot = self.get_region_screenshot(region)
                
                # Convert to numpy array and get dimensions
                img_array = np.array(screenshot)
                height, width = img_array.shape[:2]
                
                # Find pixels matching the color within tolerance
                matches = np.where(
                    (abs(img_array[..., 0] - rgb_color[0]) <= tolerance) &
                    (abs(img_array[..., 1] - rgb_color[1]) <= tolerance) &
                    (abs(img_array[..., 2] - rgb_color[2]) <= tolerance)
                )
                
                if len(matches[0]) > 0:
                    # Get center of first matching region
                    y, x = matches[0][0], matches[1][0]
                    screen_x = int(x + region_offset_x)
                    screen_y = int(y + region_offset_y)
                    
                    print(f"✅ Found color at coordinates: ({screen_x}, {screen_y})")
                    
                    # Save screenshot with highlight
                    self.save_screenshot_with_color_highlight(screenshot, x, y, hex_color)
                    
                    return (screen_x, screen_y)
                
                print("❌ Color not found in current screenshot")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        
        raise ElementNotFoundError(f"Color {hex_color} not found after {max_retries} attempts")

    def find_template_position(self, template_path, confidence=0.8, max_retries=3, retry_delay=1, region=None):
        """Find position of a template image on screen or in region
        
        Args:
            template_path: Path to template image file
            confidence: Matching confidence threshold (0-1)
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            region: Tuple of (x, y, width, height) to search within, or None for full screen
        """
        region_offset_x = int(region[0]) if region else 0
        region_offset_y = int(region[1]) if region else 0
        
        for attempt in range(max_retries):
            try:
                print(f"\n🔍 Attempt {attempt + 1}/{max_retries} - Searching for template: {template_path}")
                
                # Take screenshot and load template
                screenshot = self.get_region_screenshot(region)
                template = cv2.imread(template_path)
                
                if template is None:
                    raise ElementNotFoundError(f"Template image not found: {template_path}")
                
                # Convert images to grayscale
                screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                
                # Perform template matching
                result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= confidence:
                    # Calculate center position
                    template_h, template_w = template_gray.shape
                    center_x = int(max_loc[0] + template_w/2 + region_offset_x)
                    center_y = int(max_loc[1] + template_h/2 + region_offset_y)
                    
                    print(f"✅ Found template at coordinates: ({center_x}, {center_y}) with confidence: {max_val:.2f}")
                    return (center_x, center_y)
                
                print(f"❌ Template not found (best match: {max_val:.2f} < {confidence})")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        
        raise ElementNotFoundError(f"Template {template_path} not found after {max_retries} attempts")

    def find_text_position(self, text, min_confidence=0.4, exact_match=False, max_retries=3, retry_delay=1, region=None):
        """Find text position using OCR"""
        region_offset_x = int(region[0]) if region else 0
        region_offset_y = int(region[1]) if region else 0
        
        # Handle both single string and list of strings
        text_variations = [text] if isinstance(text, str) else text
        
        for attempt in range(max_retries):
            try:
                print(f"\n🔍 Attempt {attempt + 1}/{max_retries} - Searching for: {text_variations}")
                
                # Take screenshot
                screenshot = self.get_region_screenshot(region)
                
                # Perform OCR
                results = self.reader.readtext(np.array(screenshot))
                print(f"\n📝 Detected text: {' '.join(result[1] for result in results)}")
                
                # Search for each text variation
                for text_variant in text_variations:
                    for bbox, detected_text, confidence in results:
                        if confidence >= min_confidence:
                            detected_normalized = self.normalize_text(detected_text)
                            search_normalized = self.normalize_text(text_variant)
                            
                            if (exact_match and detected_normalized == search_normalized) or \
                               (not exact_match and search_normalized in detected_normalized):
                                print(f"✅ Found: '{text_variant}' (confidence: {confidence:.2f})")
                                
                                # Calculate center position
                                center_x = int((bbox[0][0] + bbox[2][0])/2 + region_offset_x)
                                center_y = int((bbox[0][1] + bbox[2][1])/2 + region_offset_y)
                                
                                # Save debug image
                                self.save_screenshot_with_highlight(screenshot, bbox, text_variant)
                                return (center_x, center_y)
                
                print("❌ Text not found in current screenshot")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        
        raise ElementNotFoundError(f"Text {text} not found after {max_retries} attempts")

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def click_position(self, x, y):
        """Click at specific coordinates using Win32 API"""
        # Convert numpy floats to integers
        x = int(round(float(x)))
        y = int(round(float(y)))
        
        # Move cursor
        win32api.SetCursorPos((x, y))
        time.sleep(0.1)  # Small delay to ensure movement is complete
        
        # Perform click
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

    def move_to_position(self, x, y):
        """Move mouse to specific coordinates"""
        x = int(round(float(x)))
        y = int(round(float(y)))
        win32api.SetCursorPos((x, y))
        time.sleep(0.5)  # Small delay to ensure movement is complete
        return self.parent

    def move_to_position_and_click(self, x, y):
        """Move mouse to specific coordinates and click"""
        x = int(round(float(x)))
        y = int(round(float(y)))
        self.move_to_position(x, y)
        self.click_position(x, y)
        return self.parent

    def find_text_position_and_click(self, text, min_confidence=0.4, exact_match=False, max_retries=3, retry_delay=1, region=None):
        """Find text using OCR and click on it
        
        Args:
            text: Text to search for
            min_confidence: Minimum confidence threshold for matches
            exact_match: If True, requires exact text match
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            region: Tuple of (x, y, width, height) to search within
        """
        position = self.find_text_position(text, min_confidence, exact_match, max_retries, retry_delay, region)
        if position:
            x, y = position
            try:
                self.click_position(x, y)
                time.sleep(0.5)  # Wait for click to register
            except Exception as e:
                print(f"Error clicking at position ({x}, {y}): {str(e)}")
                raise
        return self.parent

    def find_color_position_and_click(self, hex_color, tolerance=5, max_retries=3, retry_delay=1, region=None):
        """Find and click on a specific color on screen or in region
        
        Args:
            hex_color: Color in hex format (e.g. '#FF0000' for red)
            tolerance: Color matching tolerance (0-255)
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            region: Tuple of (x, y, width, height) to search within, or None for full screen
        """
        position = self.find_color_position(hex_color, tolerance, max_retries, retry_delay, region)
        if position:
            x, y = position
            try:
                self.click_position(x, y)
                time.sleep(0.5)  # Wait for click to register
            except Exception as e:
                print(f"Error clicking at position ({x}, {y}): {str(e)}")
                raise
        return self.parent

    def drag_to_position(self, start_x, start_y, end_x, end_y, duration=0.5):
        """Click and drag from start position to end position
        
        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration: Duration of drag operation in seconds
        """
        pyautogui.moveTo(start_x, start_y)
        pyautogui.mouseDown()
        pyautogui.moveTo(end_x, end_y, duration=duration)
        pyautogui.mouseUp()
        time.sleep(2)  # Built-in wait
        return self.parent

    def double_click_position(self, x, y):
        """Move to position and double click"""
        pyautogui.moveTo(x, y)
        pyautogui.doubleClick()
        time.sleep(2)  # Built-in wait
        return self.parent

    def right_click_position(self, x, y):
        """Move to position and right click"""
        pyautogui.moveTo(x, y)
        pyautogui.rightClick()
        time.sleep(2)  # Built-in wait
        return self.parent
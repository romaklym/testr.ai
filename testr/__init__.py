# testr/__init__.py
import time
from .utils import CrossPlatformUtils
from .exceptions import ElementNotFoundError
from .app_controller import AppController
from .input_simulator import InputSimulator
from .screen_analyzer import ScreenAnalyzer
from .logger import log_action, TestLogger

class Testr:
    def __init__(self, log_dir="logs"):
        self.logger = TestLogger(log_dir)
        print("\n=== Initializing Testr Framework ===")
        self.app = AppController(self)
        print(" AppController initialized")
        self.input = InputSimulator(self)
        print(" InputSimulator initialized")
        self.screen = ScreenAnalyzer(self)
        print(" ScreenAnalyzer initialized")
        print("=== Testr Framework Ready ===\n")

    def chain(self):
        print("Starting new action chain")
        return self

    def wait(self, seconds):
        print(f"Waiting for {seconds} seconds...")
        time.sleep(seconds)
        print("Wait complete")
        return self
# setup.py
from setuptools import setup, find_packages

setup(
    name='testr',
    version='0.1',
    packages=find_packages(),
    package_dir={
        'testr': 'testr'
    },
    # setup.py
    install_requires=[
        'pyautogui',
        'opencv-python',
        'easyocr',  # Added EasyOCR
        'pillow', 
        'numpy',
        'psutil',  # Required for process management
        'pywin32; platform_system=="Windows"'  # Windows-specific dependencies
    ],
    entry_points={
        'console_scripts': [
            'testr=testr.cli:main',
        ],
    },
)
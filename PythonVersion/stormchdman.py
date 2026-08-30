# stormchdman.py - Main Entry Point
import sys
import os
import multiprocessing

# Ensure we can import from src package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.gui import MainWindow
from src.config import get_resource_path

# Windows multiprocessing fix
if sys.platform.startswith('win'):
    multiprocessing.freeze_support()

def main():
    app = QApplication(sys.argv)
    
    # Load Icon
    icon_path = get_resource_path("stormchdman.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Global stylesheet for specific tweaks if needed
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

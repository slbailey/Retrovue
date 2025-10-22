#!/usr/bin/env python3
"""
Retrovue GUI Launcher - New Modular Qt Application

This launcher starts the new modular Qt-based GUI.
The old monolithic GUI (enhanced_retrovue_gui.py) will be removed after full migration.
"""

import sys
import os
from pathlib import Path

# Ensure we're in the right directory
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Add src directory to Python path
sys.path.insert(0, str(script_dir / "src"))

# Import and run the new modular Qt GUI
try:
    from retrovue.gui.app import launch
    if __name__ == "__main__":
        launch()
except Exception as e:
    print(f"Error starting GUI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# NOTE: The old monolithic GUI at enhanced_retrovue_gui.py is kept for reference
# during migration. It will be removed once all features are migrated.


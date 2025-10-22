#!/usr/bin/env python3
"""
Enhanced Retrovue GUI Launcher
"""

import sys
import os
from pathlib import Path

# Ensure we're in the right directory
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Import and run the GUI
try:
    from enhanced_retrovue_gui import main
    main()
except Exception as e:
    print(f"Error starting GUI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


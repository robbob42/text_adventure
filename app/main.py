# app/main.py
# Main entry point for running the Flask web application using the app factory.
# Refactored: Uses create_app from app package (__init__.py).

import sys
import os
import traceback

# --- Add project root to sys.path ---
# This allows the 'app' package and 'game_logic', 'database' to be found
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Project root '{project_root}' added to sys.path.")
except Exception as e:
     print(f"Error adjusting sys.path: {e}")
     sys.exit(1)

# --- Import the Application Factory ---
try:
    # Imports create_app from app/__init__.py
    # This also triggers the global game_manager initialization within __init__.py
    from app import create_app
except Exception as e:
     print(f"ERROR importing create_app from app package: {e}")
     traceback.print_exc()
     sys.exit(1)

# --- Create the App Instance ---
# The factory handles app creation, game init, and blueprint registration
try:
     app = create_app()
except Exception as e:
     print(f"CRITICAL ERROR during create_app(): {e}")
     traceback.print_exc()
     sys.exit(1)

# --- Run Application ---
if __name__ == '__main__':
    # Check if app creation was successful before running
    if app is None:
         print("CRITICAL ERROR: Flask app is None after create_app(). Exiting.")
         sys.exit(1)

    print("Starting Flask server via app factory (main.py)...")
    # Use host='0.0.0.0' to make accessible on network, debug=True for development
    # Flask's debug reloader should work better with the factory pattern
    app.run(debug=True, host='0.0.0.0', port=5000)

# app/__init__.py
# Application factory pattern implementation.

import traceback
from flask import Flask
from typing import Optional

# Import game setup function and GameManager type hint
try:
    from .game_setup import initialize_game
    from game_logic.game_manager import GameManager # Type hint only
except ImportError as e:
    print(f"ERROR: Failed to import initialize_game or GameManager in app/__init__.py: {e}")
    traceback.print_exc()
    # Cannot proceed without game setup
    raise RuntimeError("Failed to import core components for app creation.") from e

# --- Initialize Game Manager Globally within the Package ---
# This instance is created when the package is first imported and
# can then be imported by other modules within the package (like routes).
print("Initializing game manager via app/__init__.py...")
game_manager_instance: Optional['GameManager'] = None
try:
    game_manager_instance = initialize_game()
    if game_manager_instance is None:
        raise RuntimeError("Game Manager initialization failed (returned None).")
    print("Game manager initialized globally in app package.")
except Exception as e:
    print(f"CRITICAL ERROR during global game initialization in app/__init__.py: {e}")
    traceback.print_exc()
    # Optionally re-raise or handle differently
    raise RuntimeError("Failed to initialize game manager instance.") from e


def create_app():
    """Creates and configures the Flask application instance."""
    app = Flask(__name__)
    print("Flask app instance created in create_app().")

    # Add any app configurations here if needed later
    # app.config.from_object('config_module')

    # Import and register blueprints
    try:
        from .routes import bp as main_routes_bp # Import the blueprint from routes.py
        app.register_blueprint(main_routes_bp)
        print("Blueprint 'main_routes_bp' registered in create_app.")
    except Exception as e:
         print(f"ERROR registering blueprint in create_app: {e}")
         traceback.print_exc()
         # Decide if the app can run without this blueprint
         raise RuntimeError("Failed to register main blueprint.") from e

    # Optional: Attach game manager to app context if needed by extensions later
    # app.game_manager = game_manager_instance

    print("create_app() finished.")
    return app


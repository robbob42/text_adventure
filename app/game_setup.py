# app/game_setup.py
# Contains logic for initializing the game state, including GameManager creation
# and loading persistent data from the database.

import traceback
from typing import Optional

# --- Import Game Logic & DB Components ---
# Assuming these are importable because project root is in sys.path (added in main.py)
try:
    from game_logic.game_manager import GameManager
    from game_logic.content import PLAYER_START # Needed for potential revert on load error
    from database.db_setup import get_db_connection
    from database.crud import initialize_character_row_if_not_exists, load_character_state
except ImportError as e:
    print(f"ERROR: Failed to import necessary modules in app/game_setup.py: {e}")
    # Define dummies or re-raise depending on desired robustness
    GameManager = None
    PLAYER_START = {}
    def get_db_connection(): return None
    def initialize_character_row_if_not_exists(*args): return False
    def load_character_state(*args): return None
    # Re-raise might be better for critical components
    raise RuntimeError(f"Failed imports in game_setup: {e}") from e

def initialize_game() -> Optional[GameManager]:
    """
    Initializes the GameManager instance and loads persistent state.

    Returns:
        An initialized GameManager instance, or None if a critical error occurs.
    """
    local_game_manager: Optional[GameManager] = None
    try:
        print("Initializing GameManager...")
        local_game_manager = GameManager()
        print("GameManager created with default state.")

        # --- Load Persistent State ---
        print("Attempting to load persistent state from database...")
        db_conn = get_db_connection()
        initial_load_success = False
        if db_conn:
            try:
                # Ensure the character row exists or create it with defaults
                init_success = initialize_character_row_if_not_exists(db_conn, char_id=1)
                if init_success:
                    # Attempt to load the character state
                    loaded_character = load_character_state(db_conn, character_id=1)
                    if loaded_character and local_game_manager:
                        local_game_manager.character = loaded_character
                        # TODO: Restore discovered actions/LLM actions from save file?
                        # TODO: Restore tutorial flags from save file?

                        # Ensure the loaded location ID is valid
                        local_game_manager.current_location = local_game_manager.locations.get(loaded_character.current_location_id)
                        if local_game_manager.current_location is None:
                             print(f"Warning: Loaded character location ID '{loaded_character.current_location_id}' not found. Reverting.")
                             # Use PLAYER_START as fallback if needed
                             default_start_id = PLAYER_START.get('current_location_id', 'entry_cave')
                             local_game_manager.character.current_location_id = default_start_id
                             local_game_manager.current_location = local_game_manager.locations.get(default_start_id)
                        print(f"Successfully loaded persistent state for Character ID 1.")
                        initial_load_success = True
                    else:
                        print("Persistent state row exists/created, but loading failed or returned None. Using default state.")
                        initial_load_success = True # Allow continuing with default state
                else:
                    print("Failed to initialize character row in database. Cannot load state.")
            except Exception as e:
                print(f"Error during database initialization/load: {e}")
                traceback.print_exc() # Print full traceback for DB errors
            finally:
                if db_conn:
                    db_conn.close()
                    print("Initial database connection closed.")
        else:
            print("Failed to connect to database for initial load.")

        if not initial_load_success:
            print("Warning: Proceeding with default game state potentially due to DB load issues.")
        # Even if load failed, return the manager with default state if it was created
        return local_game_manager

    except ValueError as e:
        # Error during GameManager() creation itself
        print(f"CRITICAL ERROR during GameManager initialization: {e}")
        traceback.print_exc()
        return None # Indicate failure
    except Exception as e:
        print(f"CRITICAL ERROR: An unexpected error occurred during game setup: {e}")
        traceback.print_exc()
        return None # Indicate failure


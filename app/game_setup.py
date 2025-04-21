# app/game_setup.py
# Contains functions for initializing the game state and GameManager.
# Created for Phase P3.
# Updated: Implemented load_or_initialize_character to handle tuple return from crud.load_character_state (P3.1).
# Updated: Pass loaded state (character, sets, flags) to GameManager constructor (P3.2).

import sys
import os
import traceback
from typing import Optional, Tuple, Set, TYPE_CHECKING

# --- Add project root to sys.path if needed ---
# Ensures game_logic and database packages can be found
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) # Assuming app/ is one level down from root
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Project root '{project_root}' added to sys.path in game_setup.")
except Exception as e:
     print(f"Error adjusting sys.path in game_setup: {e}")
     # Decide if fatal or not

# --- Import necessary components ---
try:
    from game_logic.game_manager import GameManager
    from game_logic.models import Character
    from database.db_setup import get_db_connection, create_tables
    from database.crud import initialize_character_row_if_not_exists, load_character_state
    from game_logic.content import PLAYER_START # Needed for fallback location ID
except ImportError as e:
    print(f"ERROR importing modules in game_setup.py: {e}")
    traceback.print_exc()
    # Define dummies or raise error
    class GameManager: pass
    class Character: pass
    def get_db_connection(): return None
    def create_tables(*args): return False
    def initialize_character_row_if_not_exists(*args): return False
    def load_character_state(*args): return None
    PLAYER_START = {}
    raise RuntimeError(f"Failed imports in game_setup: {e}") from e

if TYPE_CHECKING:
    # Type hint for the return value of load_character_state
    LoadResultType = Optional[Tuple[Character, Set[str], Set[str], bool, bool]]


# --- Helper Function to Load/Init Character and Persistence State (P3.1) ---
def load_or_initialize_character(character_id: int = 1) -> 'LoadResultType':
    """
    Connects to DB, ensures table/row exist, and loads character state
    including persistence fields (discovered actions, tutorial flags).

    Returns:
        A tuple (Character, discovered_actions_set, discovered_llm_actions_set,
                 tutorial_pickaxe_taken_bool, tutorial_blockage_cleared_bool)
        or None if loading fails critically.
    """
    print("Attempting to load or initialize character...")
    db_conn = None
    loaded_data: 'LoadResultType' = None
    try:
        db_conn = get_db_connection()
        if not db_conn:
            raise ConnectionError("Failed to get DB connection.")

        # Ensure tables exist (idempotent)
        if not create_tables(db_conn):
             raise RuntimeError("Failed to ensure database tables exist.")

        # Ensure character row exists (idempotent)
        if not initialize_character_row_if_not_exists(db_conn, character_id):
            raise RuntimeError("Failed to initialize character row.")

        # Load character state using the updated function from crud.py (P2.2)
        loaded_data = load_character_state(db_conn, character_id)

        if loaded_data is None:
             # This shouldn't happen if init worked, but handle defensively
             print(f"ERROR: load_character_state returned None after initialization for ID {character_id}.")
             # Decide how to handle - raise error, return defaults? Raising for now.
             raise ValueError("Failed to load character state after initialization.")
        else:
             # Unpack just to log success
             char_obj, disc_actions, llm_actions, pickaxe_flag, blockage_flag = loaded_data
             print(f"Successfully loaded character '{char_obj.name}' and persistence state.")
             print(f"  Loaded {len(disc_actions)} discovered actions, {len(llm_actions)} LLM actions.")
             print(f"  Loaded tutorial flags: Pickaxe={pickaxe_flag}, Blockage={blockage_flag}")

    except Exception as e:
        print(f"CRITICAL ERROR during character load/init: {e}")
        traceback.print_exc()
        loaded_data = None # Ensure None is returned on error
    finally:
        if db_conn:
            db_conn.close()
            print("DB connection closed in load_or_initialize_character.")

    # Return the loaded tuple (or None if error occurred)
    return loaded_data


# --- Main Initialization Function (Updated P3.2) ---
def initialize_game() -> Optional[GameManager]:
    """
    Initializes the entire game state, including loading character data
    and creating the GameManager instance using the loaded state.

    Returns:
        An initialized GameManager instance, or None if initialization fails.
    """
    print("Starting game initialization...")
    game_manager = None
    try:
        # Load character and persistence state using the helper (P3.1)
        loaded_data = load_or_initialize_character(character_id=1)

        if loaded_data is None:
            print("ERROR: Failed to load or initialize character data. Cannot start game.")
            return None

        # Unpack the loaded data tuple (P3.1)
        character_obj, discovered_actions, discovered_llm_actions, tutorial_pickaxe_taken, tutorial_blockage_cleared = loaded_data

        # --- Create GameManager Instance (Updated P3.2) ---
        # Pass the loaded state directly to the constructor.
        # This requires GameManager.__init__ to be updated in Step P3.3
        # to accept these arguments.
        print("Creating GameManager instance with loaded state...")
        game_manager = GameManager(
            initial_character=character_obj,
            initial_discovered_actions=discovered_actions,
            initial_discovered_llm_actions=discovered_llm_actions,
            initial_tutorial_pickaxe_taken=tutorial_pickaxe_taken,
            initial_tutorial_blockage_cleared=tutorial_blockage_cleared
        )
        print("GameManager instance created.")
        # --- End GameManager Creation ---

        # --- Validation (Optional): Check if GM correctly loaded state ---
        # (Requires GameManager.__init__ to be updated first in P3.3)
        # if game_manager.character.name != character_obj.name:
        #     print("Warning: GM character name mismatch after init.")
        # if game_manager.discovered_actions != discovered_actions:
        #     print("Warning: GM discovered_actions mismatch after init.")
        # if game_manager.tutorial_pickaxe_taken != tutorial_pickaxe_taken:
        #      print("Warning: GM tutorial_pickaxe_taken mismatch after init.")
        # --- End Validation ---


        print("Game initialization successful.")

    except Exception as e:
        print(f"CRITICAL ERROR during game initialization: {e}")
        traceback.print_exc()
        game_manager = None # Ensure None is returned on error

    return game_manager


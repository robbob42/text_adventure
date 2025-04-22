# app/game_setup.py
# Contains functions for initializing the game state and GameManager.
# Created for Phase P3.
# Updated: Implemented load_or_initialize_character to handle tuple return from crud.load_character_state (P3.1).
# Updated: Pass loaded state (character, sets, flags) to GameManager constructor (P3.2).
# Updated: Load location modifications after GM init (Location Persistence Plan L2.1).
# Updated: Call apply_modifications after loading mods (Location Persistence Plan L2.3).

import sys
import os
import traceback
from typing import Optional, Tuple, Set, List, TYPE_CHECKING # Added List

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
    # Import all necessary CRUD functions
    from database.crud import (
        initialize_character_row_if_not_exists,
        load_character_state,
        load_location_modifications # Added for L2.1
    )
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
    def load_location_modifications(*args): return [] # Added dummy
    PLAYER_START = {}
    raise RuntimeError(f"Failed imports in game_setup: {e}") from e

if TYPE_CHECKING:
    # Type hint for the return value of load_character_state
    LoadResultType = Optional[Tuple[Character, Set[str], Set[str], bool, bool]]
    # Type hint for location modifications
    ModListType = List[Tuple[str, str, str]]


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
        if not db_conn: raise ConnectionError("Failed to get DB connection.")
        if not create_tables(db_conn): raise RuntimeError("Failed to ensure database tables exist.")
        if not initialize_character_row_if_not_exists(db_conn, character_id): raise RuntimeError("Failed to initialize character row.")

        loaded_data = load_character_state(db_conn, character_id)

        if loaded_data is None:
             print(f"ERROR: load_character_state returned None after initialization for ID {character_id}.")
             raise ValueError("Failed to load character state after initialization.")
        else:
             char_obj, disc_actions, llm_actions, pickaxe_flag, blockage_flag = loaded_data
             print(f"Successfully loaded character '{char_obj.name}' and persistence state.")
             # print(f"  Loaded {len(disc_actions)} discovered actions, {len(llm_actions)} LLM actions.") # Reduced verbosity
             # print(f"  Loaded tutorial flags: Pickaxe={pickaxe_flag}, Blockage={blockage_flag}")

    except Exception as e:
        print(f"CRITICAL ERROR during character load/init: {e}"); traceback.print_exc()
        loaded_data = None # Ensure None is returned on error
    finally:
        if db_conn: db_conn.close(); print("DB connection closed in load_or_initialize_character.")

    return loaded_data


# --- Main Initialization Function (Updated L2.1, L2.3) ---
def initialize_game() -> Optional[GameManager]:
    """
    Initializes the entire game state, including loading character data,
    creating the GameManager instance, loading location modifications,
    and applying those modifications.

    Returns:
        An initialized GameManager instance, or None if initialization fails.
    """
    print("Starting game initialization...")
    game_manager = None
    loaded_mods: 'ModListType' = [] # Initialize empty list for mods

    try:
        # Load character and persistence state using the helper (P3.1)
        loaded_data = load_or_initialize_character(character_id=1)
        if loaded_data is None: print("ERROR: Failed to load or initialize character data. Cannot start game."); return None
        character_obj, discovered_actions, discovered_llm_actions, tutorial_pickaxe_taken, tutorial_blockage_cleared = loaded_data

        # --- Create GameManager Instance (P3.2) ---
        print("Creating GameManager instance with loaded state...")
        game_manager = GameManager(
            initial_character=character_obj,
            initial_discovered_actions=discovered_actions,
            initial_discovered_llm_actions=discovered_llm_actions,
            initial_tutorial_pickaxe_taken=tutorial_pickaxe_taken,
            initial_tutorial_blockage_cleared=tutorial_blockage_cleared
        )
        print("GameManager instance created.")

        # --- Load Location Modifications (L2.1) ---
        print("Attempting to load location modifications...")
        db_conn_mods = None
        try:
            db_conn_mods = get_db_connection()
            if db_conn_mods:
                # Assuming character ID 1 for now
                loaded_mods = load_location_modifications(db_conn_mods, character_id=1)
                print(f"Loaded {len(loaded_mods)} location modifications from database.")
            else:
                print("Warning: Could not get DB connection to load location modifications.")
        except Exception as mod_load_err:
             print(f"Error loading location modifications: {mod_load_err}")
             traceback.print_exc()
             loaded_mods = [] # Ensure empty list on error
        finally:
             if db_conn_mods: db_conn_mods.close(); print("DB connection closed after loading mods.")
        # --- End Load Location Modifications ---

        # --- Apply Modifications (Added L2.3) ---
        if game_manager and loaded_mods: # Check if GM exists and mods were loaded
            print("Calling GameManager to apply loaded modifications...")
            game_manager.apply_modifications(loaded_mods)
            # apply_modifications method now handles internal logging
        elif game_manager:
             print("No location modifications loaded to apply.")
        # --- End Apply Modifications ---


        print("Game initialization successful.")

    except Exception as e:
        print(f"CRITICAL ERROR during game initialization: {e}"); traceback.print_exc()
        game_manager = None # Ensure None is returned on error

    return game_manager


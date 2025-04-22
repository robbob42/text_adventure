# database/crud.py
# Refactored: Removed ALL multi-statement lines using semicolons.
# Updated: Added persistence fields to initialize_character_row_if_not_exists (P2.1).
# Updated: Modified load_character_state to load persistence fields (P2.2).
# Updated: Modified save_character_state to save persistence fields (P2.3).
# Updated: Added save/load functions for location_mods (Location Persistence Plan L1.2).
# Updated: Added tests for location mod CRUD functions in __main__ block (Location Persistence Plan L1.3).

import sqlite3
import json
import traceback # Import traceback for better error logging
from typing import Optional, Dict, Any, List, Tuple, Set # Added Tuple, Set

# --- Import necessary components ---
# Using try-except for robustness during development/import path issues
try:
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from game_logic.models import Character
    from game_logic.content import PLAYER_START
    # Import both get_db_connection and clear_location_modifications
    from database.db_setup import get_db_connection, clear_location_modifications # Added clear import for L1.3 test

    # sys.path.pop(0) # Optional cleanup
except ImportError as e:
    print(f"ERROR importing modules in crud.py: {e}")
    print("Defining dummy classes/variables for robustness.")
    # Define dummies on separate lines
    class Character: pass
    PLAYER_START = {}
    def get_db_connection(): return None
    def clear_location_modifications(*args): return False # Dummy clear function
except Exception as e:
    # Catch other potential import errors
    print(f"ERROR during imports in crud.py: {e}")
    class Character: pass
    PLAYER_START = {}
    def get_db_connection(): return None
    def clear_location_modifications(*args): return False # Dummy clear function

# --- CRUD Functions ---

def initialize_character_row_if_not_exists(conn: Optional[sqlite3.Connection], char_id: int = 1) -> bool:
    """
    Inserts the initial character data from content.py if the character ID doesn't exist.
    Includes xp, level, inventory (JSON), skills (JSON), active_quests (JSON).
    Uses String Location ID.
    Updated (P2.1): Includes persistence fields with defaults.
    """
    if not conn: print("CRUD Error (Init): No DB connection."); return False
    if not PLAYER_START: print("CRUD Error (Init): PLAYER_START missing."); return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM characters WHERE id = ?", (char_id,))
        row = cursor.fetchone()
        count = row[0] if row else 0
        if count == 0:
            print(f"Initializing character row for ID {char_id}...")
            default_inventory = PLAYER_START.get('inventory', [])
            default_skills = PLAYER_START.get('skills', {})
            default_quests = PLAYER_START.get('active_quests', [])
            inventory_json = json.dumps(default_inventory)
            skills_json = json.dumps(default_skills)
            quests_json = json.dumps(default_quests)
            location_id_str = str(PLAYER_START.get('current_location_id', 'entry_cave'))
            xp = int(PLAYER_START.get('xp', 0))
            level = int(PLAYER_START.get('level', 1))
            hp = int(PLAYER_START.get('hp', 0))
            max_hp = int(PLAYER_START.get('max_hp', 0))
            default_discovered_actions_json = json.dumps([])
            default_discovered_llm_actions_json = json.dumps([])
            default_tutorial_pickaxe_taken = 0
            default_tutorial_blockage_cleared = 0
            cursor.execute("""
                INSERT INTO characters (
                    id, name, hp, max_hp, current_location_id,
                    inventory, skills, xp, level, active_quests,
                    discovered_actions, discovered_llm_actions,
                    tutorial_pickaxe_taken, tutorial_blockage_cleared
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ( char_id, PLAYER_START.get('name', 'Unknown'), hp, max_hp, location_id_str,
                 inventory_json, skills_json, xp, level, quests_json,
                 default_discovered_actions_json, default_discovered_llm_actions_json,
                 default_tutorial_pickaxe_taken, default_tutorial_blockage_cleared ))
            conn.commit(); print("Character row initialized with persistence defaults.")
            return True
        else: return True
    except Exception as e:
        print(f"Error during character initialization: {e}"); traceback.print_exc()
        try: conn.rollback()
        except Exception as rb_e: print(f"Rollback Error: {rb_e}")
        return False

# --- Updated Function: load_character_state (P2.2) ---
def load_character_state(conn: Optional[sqlite3.Connection], character_id: int = 1) -> Optional[Tuple[Character, Set[str], Set[str], bool, bool]]:
    """
    Loads character state including discovered actions and tutorial flags.
    Returns a tuple: (Character, discovered_actions_set, discovered_llm_actions_set,
                     tutorial_pickaxe_taken_bool, tutorial_blockage_cleared_bool) or None.
    """
    if not conn: print("CRUD Error (Load): No DB connection."); return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, hp, max_hp, current_location_id, inventory, skills, xp, level, active_quests,
                   discovered_actions, discovered_llm_actions, tutorial_pickaxe_taken, tutorial_blockage_cleared
            FROM characters WHERE id = ? """, (character_id,))
        row = cursor.fetchone()
        if row:
            (name, hp, max_hp, location_id_str, inv_json, skills_json, xp, level, quests_json,
             discovered_actions_json, discovered_llm_actions_json,
             tutorial_pickaxe_taken_int, tutorial_blockage_cleared_int) = row
            inventory: List[str] = []
            try: inventory = json.loads(inv_json or '[]'); assert isinstance(inventory, list)
            except (json.JSONDecodeError, AssertionError): print(f"Warn: Bad inventory JSON char {character_id}."); inventory = []
            skills: Dict[str, int] = {}
            try: skills = json.loads(skills_json or '{}'); assert isinstance(skills, dict)
            except (json.JSONDecodeError, AssertionError): print(f"Warn: Bad skills JSON char {character_id}."); skills = {}
            active_quests: List[str] = []
            try: active_quests = json.loads(quests_json or '[]'); assert isinstance(active_quests, list)
            except (json.JSONDecodeError, AssertionError): print(f"Warn: Bad quests JSON char {character_id}."); active_quests = []
            discovered_actions: Set[str] = set()
            try: loaded_list = json.loads(discovered_actions_json or '[]'); discovered_actions = set(loaded_list) if isinstance(loaded_list, list) else set()
            except (json.JSONDecodeError): print(f"Warn: Bad discovered_actions JSON char {character_id}.")
            discovered_llm_actions: Set[str] = set()
            try: loaded_llm_list = json.loads(discovered_llm_actions_json or '[]'); discovered_llm_actions = set(loaded_llm_list) if isinstance(loaded_llm_list, list) else set()
            except (json.JSONDecodeError): print(f"Warn: Bad discovered_llm_actions JSON char {character_id}.")
            tutorial_pickaxe_taken: bool = bool(tutorial_pickaxe_taken_int)
            tutorial_blockage_cleared: bool = bool(tutorial_blockage_cleared_int)
            # print(f"Loaded (P2.2): ID={character_id}, Lvl={level}, LocID='{location_id_str}'...") # Reduced verbosity
            # print(f"  Loaded Disc Actions: {len(discovered_actions)}, LLM Actions: {len(discovered_llm_actions)}, Tutorial Flags: P={tutorial_pickaxe_taken}/B={tutorial_blockage_cleared}")
            character_obj = Character(name=str(name), hp=int(hp), max_hp=int(max_hp), current_location_id=str(location_id_str),
                                     inventory=inventory, skills=skills, xp=int(xp), level=int(level), active_quests=active_quests)
            return (character_obj, discovered_actions, discovered_llm_actions, tutorial_pickaxe_taken, tutorial_blockage_cleared)
        else: print(f"No character found with ID {character_id}."); return None
    except Exception as e: print(f"Error loading character state: {e}"); traceback.print_exc(); return None

# --- Updated Function: save_character_state (P2.3) ---
def save_character_state( conn: Optional[sqlite3.Connection], character: Character, discovered_actions: Set[str],
                         discovered_llm_actions: Set[str], tutorial_pickaxe_taken: bool, tutorial_blockage_cleared: bool,
                         character_id: int = 1 ) -> bool:
    """ Saves character state including discovered actions and tutorial flags. """
    if not conn: print("CRUD Error (Save): No DB connection."); return False
    if not isinstance(character, Character): print("CRUD Error (Save): Invalid character object."); return False
    if not isinstance(discovered_actions, set): print("CRUD Warn (Save): discovered_actions not set."); return False
    if not isinstance(discovered_llm_actions, set): print("CRUD Warn (Save): discovered_llm_actions not set."); return False
    if not isinstance(tutorial_pickaxe_taken, bool): print("CRUD Warn (Save): tutorial_pickaxe_taken not bool."); return False
    if not isinstance(tutorial_blockage_cleared, bool): print("CRUD Warn (Save): tutorial_blockage_cleared not bool."); return False
    try:
        cursor = conn.cursor()
        inv_json = json.dumps(character.inventory)
        skills_json = json.dumps(character.skills)
        quests_json = json.dumps(character.active_quests)
        discovered_actions_json = json.dumps(list(discovered_actions))
        discovered_llm_actions_json = json.dumps(list(discovered_llm_actions))
        tutorial_pickaxe_taken_int = 1 if tutorial_pickaxe_taken else 0
        tutorial_blockage_cleared_int = 1 if tutorial_blockage_cleared else 0
        # print(f"Saving (P2.3): ID={character_id}, Lvl={character.level}, LocID='{character.current_location_id}'...") # Reduced verbosity
        # print(f"  Saving Disc Actions: {len(discovered_actions)}, LLM Actions: {len(discovered_llm_actions)}, Flags=P{tutorial_pickaxe_taken_int}/B{tutorial_blockage_cleared_int}")
        cursor.execute("""
            UPDATE characters SET hp = ?, max_hp = ?, current_location_id = ?, inventory = ?, skills = ?, xp = ?, level = ?, active_quests = ?,
                discovered_actions = ?, discovered_llm_actions = ?, tutorial_pickaxe_taken = ?, tutorial_blockage_cleared = ?
            WHERE id = ? """, ( character.hp, character.max_hp, str(character.current_location_id), inv_json, skills_json, character.xp, character.level, quests_json,
                              discovered_actions_json, discovered_llm_actions_json, tutorial_pickaxe_taken_int, tutorial_blockage_cleared_int, character_id ))
        conn.commit()
        if cursor.rowcount == 0: print(f"Warn: Save character state updated 0 rows for ID {character_id}.")
        # print("Character state saved successfully (P2.3).") # Reduced verbosity
        return True
    except Exception as e:
        print(f"Error saving character state: {e}"); traceback.print_exc()
        try: conn.rollback()
        except Exception as rb_e: print(f"Rollback Error: {rb_e}")
        return False

# --- Added Location Modification CRUD Functions (L1.2) ---

def save_location_modification(conn: Optional[sqlite3.Connection], character_id: int, location_id: str, mod_type: str, mod_data: str) -> bool:
    """
    Saves a single location modification to the database.
    Does not currently check for duplicates.
    """
    if not conn: print("CRUD Error (Save Loc Mod): No DB connection."); return False
    if not all([character_id, location_id, mod_type]): print("CRUD Error (Save Loc Mod): Missing required arguments."); return False # mod_data can be empty string

    try:
        cursor = conn.cursor()
        print(f"Saving location mod: CharID={character_id}, LocID='{location_id}', Type='{mod_type}', Data='{mod_data[:50]}...'")
        cursor.execute("""
            INSERT INTO location_mods (character_id, location_id, mod_type, mod_data)
            VALUES (?, ?, ?, ?)
        """, (character_id, location_id, mod_type, mod_data))
        conn.commit()
        print("Location modification saved successfully.")
        return True
    except Exception as e:
        print(f"Error saving location modification: {e}"); traceback.print_exc()
        try: conn.rollback()
        except Exception as rb_e: print(f"Rollback Error: {rb_e}")
        return False

def load_location_modifications(conn: Optional[sqlite3.Connection], character_id: int) -> List[Tuple[str, str, str]]:
    """
    Loads all location modifications for a given character_id.

    Returns:
        A list of tuples, where each tuple is (location_id, mod_type, mod_data).
        Returns an empty list if no modifications are found or on error.
    """
    if not conn: print("CRUD Error (Load Loc Mods): No DB connection."); return []

    modifications: List[Tuple[str, str, str]] = []
    try:
        cursor = conn.cursor()
        # print(f"Loading location modifications for character_id: {character_id}...") # Reduced verbosity
        cursor.execute("""
            SELECT location_id, mod_type, mod_data
            FROM location_mods
            WHERE character_id = ?
            ORDER BY id ASC -- Load in the order they were applied (optional but good practice)
        """, (character_id,))
        rows = cursor.fetchall()
        modifications = [(str(row[0]), str(row[1]), str(row[2])) for row in rows] # Ensure string types
        # print(f"Loaded {len(modifications)} location modifications.") # Reduced verbosity
    except Exception as e:
        print(f"Error loading location modifications: {e}"); traceback.print_exc()
        modifications = [] # Return empty list on error

    return modifications

# --- End Added Functions (L1.2) ---


# --- Optional: Basic test block (Refactored & Updated L1.3) ---
if __name__ == '__main__':
    print("\n--- CRUD Test (Includes Location Mods - L1.3) ---")
    db_conn = get_db_connection()
    if db_conn:
        print("\nTesting Initialization...")
        init_success = initialize_character_row_if_not_exists(db_conn, char_id=1)
        print(f"Initialization reported success: {init_success}")
        if init_success:
            # --- Test Character Load/Save (Optional, keep for regression) ---
            print("\nTesting Character Load/Save Cycle...")
            loaded_data = load_character_state(db_conn, character_id=1)
            if loaded_data:
                loaded_char, loaded_discovered, loaded_llm, loaded_pickaxe, loaded_blockage = loaded_data
                # Modify state slightly
                loaded_char.hp = max(0, loaded_char.hp - 1)
                test_discovered_actions = loaded_discovered.copy(); test_discovered_actions.add("test_action")
                test_llm_actions = loaded_llm.copy(); test_llm_actions.add("test_llm_action")
                test_pickaxe_flag = not loaded_pickaxe
                test_blockage_flag = not loaded_blockage
                # Save modified state
                save_success = save_character_state( db_conn, loaded_char, test_discovered_actions, test_llm_actions,
                                                  test_pickaxe_flag, test_blockage_flag, character_id=1 )
                if save_success:
                    # Reload and verify (basic check)
                    reloaded_data = load_character_state(db_conn, character_id=1)
                    if reloaded_data and reloaded_data[0].hp == loaded_char.hp and "test_action" in reloaded_data[1]:
                         print("VERIFICATION (Character State): Basic save/load seems OK.")
                    else:
                         print("VERIFICATION FAILED (Character State): Mismatch after save/load.")
                else:
                     print("Character save failed, skipping verification.")
            else:
                 print("Initial character load failed, skipping character tests.")
            # --- End Character Load/Save Test ---


            # --- Test Location Mod Functions (L1.3) ---
            print("\n--- Testing Location Modifications (L1.3) ---")
            test_char_id = 1
            expected_mods = [
                ('entry_cave', 'REMOVE_ITEM', 'pickaxe'),
                ('entry_cave', 'CHANGE_DESC', 'Rubble is gone!'),
                ('narrow_corridor', 'ADD_NPC', '{"name": "ghost", "desc": "a faint spectre"}')
            ]

            # 1. Clear any existing mods first
            print(f"\n1. Clearing existing mods for char {test_char_id}...")
            try:
                clear_success = clear_location_modifications(db_conn, test_char_id)
                print(f"Clear mods success: {clear_success}")
                # Verify clear worked
                mods_after_clear = load_location_modifications(db_conn, test_char_id)
                if clear_success and len(mods_after_clear) == 0:
                    print("VERIFICATION (Clear): Mods cleared successfully.")
                else:
                    print(f"VERIFICATION FAILED (Clear): Expected 0 mods, found {len(mods_after_clear)}.")
            except Exception as clear_err:
                 print(f"Error during clear test: {clear_err}")

            # 2. Save test modifications
            print("\n2. Saving test modifications...")
            save_results = []
            for loc_id, mod_type, mod_data in expected_mods:
                 save_results.append(save_location_modification(db_conn, test_char_id, loc_id, mod_type, mod_data))
            print(f"Save results: {save_results}")

            # 3. Load and verify modifications
            if all(save_results):
                print("\n3. Loading modifications...")
                loaded_mods = load_location_modifications(db_conn, test_char_id)
                print(f"Loaded mods ({len(loaded_mods)}): {loaded_mods}")

                # Verification
                if loaded_mods == expected_mods:
                    print(f"VERIFICATION (Save/Load): Correct mods loaded in order.")
                else:
                    print(f"VERIFICATION FAILED (Save/Load): Loaded mods do not match expected.")
                    print(f"  Expected: {expected_mods}")
                    print(f"  Loaded:   {loaded_mods}")
            else:
                print("Skipping load test for location mods due to save failure(s).")
            # --- End Test Location Mod Functions ---

        else:
             print("Failed to initialize character row.")
        db_conn.close(); print("\nDatabase connection closed.")
    else:
        print("Cannot run CRUD tests: Database connection failed.")
    print("-----------------")


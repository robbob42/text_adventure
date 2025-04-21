# database/crud.py
# Refactored: Removed ALL multi-statement lines using semicolons.
# Updated: Added persistence fields to initialize_character_row_if_not_exists (P2.1).
# Updated: Modified load_character_state to load persistence fields (P2.2).
# Updated: Modified save_character_state to save persistence fields (P2.3).

import sqlite3
import json
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
    from database.db_setup import get_db_connection

    # sys.path.pop(0) # Optional cleanup
except ImportError as e:
    print(f"ERROR importing modules in crud.py: {e}")
    print("Defining dummy classes/variables for robustness.")
    # Define dummies on separate lines
    class Character:
        pass
    PLAYER_START = {}
    def get_db_connection():
        return None
except Exception as e:
    # Catch other potential import errors
    print(f"ERROR during imports in crud.py: {e}")
    class Character:
        pass
    PLAYER_START = {}
    def get_db_connection():
        return None

# --- CRUD Functions ---

def initialize_character_row_if_not_exists(conn: Optional[sqlite3.Connection], char_id: int = 1) -> bool:
    """
    Inserts the initial character data from content.py if the character ID doesn't exist.
    Includes xp, level, inventory (JSON), skills (JSON), active_quests (JSON).
    Uses String Location ID.
    Updated (P2.1): Includes persistence fields with defaults.
    """
    if not conn:
        print("CRUD Error (Init): No DB connection.")
        return False
    if not PLAYER_START:
        print("CRUD Error (Init): PLAYER_START missing.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM characters WHERE id = ?", (char_id,))
        row = cursor.fetchone()
        # Ensure row is not None before accessing index
        count = row[0] if row else 0

        if count == 0:
            print(f"Initializing character row for ID {char_id}...")
            # Get defaults and convert list/dict to JSON strings
            default_inventory = PLAYER_START.get('inventory', [])
            default_skills = PLAYER_START.get('skills', {})
            default_quests = PLAYER_START.get('active_quests', [])
            inventory_json = json.dumps(default_inventory)
            skills_json = json.dumps(default_skills)
            quests_json = json.dumps(default_quests)
            # Ensure location ID is string and other stats are correct type
            location_id_str = str(PLAYER_START.get('current_location_id', 'entry_cave'))
            xp = int(PLAYER_START.get('xp', 0))
            level = int(PLAYER_START.get('level', 1))
            hp = int(PLAYER_START.get('hp', 0))
            max_hp = int(PLAYER_START.get('max_hp', 0))

            # --- Added Defaults for Persistence Fields (P2.1) ---
            default_discovered_actions_json = json.dumps([])
            default_discovered_llm_actions_json = json.dumps([])
            default_tutorial_pickaxe_taken = 0
            default_tutorial_blockage_cleared = 0
            # --- End Added Defaults ---

            cursor.execute("""
                INSERT INTO characters (
                    id, name, hp, max_hp, current_location_id,
                    inventory, skills, xp, level, active_quests,
                    -- Added Persistence Columns (P2.1) --
                    discovered_actions, discovered_llm_actions,
                    tutorial_pickaxe_taken, tutorial_blockage_cleared
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                char_id,
                PLAYER_START.get('name', 'Unknown'),
                hp,
                max_hp,
                location_id_str, # Use string
                inventory_json,
                skills_json,
                xp,
                level,
                quests_json,
                # --- Added Default Values for Persistence Fields (P2.1) ---
                default_discovered_actions_json,
                default_discovered_llm_actions_json,
                default_tutorial_pickaxe_taken,
                default_tutorial_blockage_cleared
                # --- End Added Default Values ---
            ))
            conn.commit()
            print("Character row initialized with persistence defaults.")
            return True
        else:
            # Row already exists
            return True
    except Exception as e:
        print(f"Error during character initialization: {e}")
        # Ensure rollback happens even if commit wasn't reached
        try:
            conn.rollback()
        except Exception as rb_e:
            print(f"Error during rollback after initialization error: {rb_e}")
        return False


# --- Updated Function: load_character_state (P2.2) ---
def load_character_state(conn: Optional[sqlite3.Connection], character_id: int = 1) -> Optional[Tuple[Character, Set[str], Set[str], bool, bool]]:
    """
    Loads character state including discovered actions and tutorial flags.
    Returns a tuple: (Character, discovered_actions_set, discovered_llm_actions_set,
                     tutorial_pickaxe_taken_bool, tutorial_blockage_cleared_bool) or None.
    """
    if not conn:
        print("CRUD Error (Load): No DB connection.")
        return None

    try:
        cursor = conn.cursor()
        # Select all necessary columns, including the new ones
        cursor.execute("""
            SELECT name, hp, max_hp, current_location_id, inventory, skills, xp, level, active_quests,
                   discovered_actions, discovered_llm_actions, tutorial_pickaxe_taken, tutorial_blockage_cleared
            FROM characters WHERE id = ?
        """, (character_id,))
        row = cursor.fetchone()

        if row:
            # Unpack all columns from the row
            (name, hp, max_hp, location_id_str, inv_json, skills_json, xp, level, quests_json,
             discovered_actions_json, discovered_llm_actions_json,
             tutorial_pickaxe_taken_int, tutorial_blockage_cleared_int) = row

            # --- Process Core Character Data (same as before) ---
            inventory: List[str] = []
            try:
                inventory = json.loads(inv_json or '[]')
                assert isinstance(inventory, list)
            except (json.JSONDecodeError, AssertionError):
                print(f"Warning: Bad inventory JSON for char {character_id}. Defaulting.")
                inventory = []

            skills: Dict[str, int] = {}
            try:
                skills = json.loads(skills_json or '{}')
                assert isinstance(skills, dict)
            except (json.JSONDecodeError, AssertionError):
                print(f"Warning: Bad skills JSON for char {character_id}. Defaulting.")
                skills = {}

            active_quests: List[str] = []
            try:
                active_quests = json.loads(quests_json or '[]')
                assert isinstance(active_quests, list)
            except (json.JSONDecodeError, AssertionError):
                print(f"Warning: Bad quests JSON for char {character_id}. Defaulting.")
                active_quests = []

            # --- Process Persistence Fields (P2.2) ---
            discovered_actions: Set[str] = set()
            try:
                loaded_list = json.loads(discovered_actions_json or '[]')
                if isinstance(loaded_list, list):
                    discovered_actions = set(loaded_list)
                else:
                    print(f"Warning: Bad discovered_actions JSON type for char {character_id}. Defaulting.")
            except (json.JSONDecodeError):
                print(f"Warning: Bad discovered_actions JSON format for char {character_id}. Defaulting.")

            discovered_llm_actions: Set[str] = set()
            try:
                loaded_llm_list = json.loads(discovered_llm_actions_json or '[]')
                if isinstance(loaded_llm_list, list):
                    discovered_llm_actions = set(loaded_llm_list)
                else:
                    print(f"Warning: Bad discovered_llm_actions JSON type for char {character_id}. Defaulting.")
            except (json.JSONDecodeError):
                print(f"Warning: Bad discovered_llm_actions JSON format for char {character_id}. Defaulting.")

            tutorial_pickaxe_taken: bool = bool(tutorial_pickaxe_taken_int) # Convert 0/1 to False/True
            tutorial_blockage_cleared: bool = bool(tutorial_blockage_cleared_int) # Convert 0/1 to False/True
            # --- End Processing Persistence Fields ---

            print(f"Loaded (P2.2): ID={character_id}, Lvl={level}, XP={xp}, HP={hp}, MaxHP={max_hp}, LocID='{location_id_str}'...")
            print(f"  Loaded Discovered Actions: {len(discovered_actions)}")
            print(f"  Loaded LLM Actions: {len(discovered_llm_actions)}")
            print(f"  Loaded Tutorial Flags: Pickaxe={tutorial_pickaxe_taken}, Blockage={tutorial_blockage_cleared}")

            # Create the Character object
            character_obj = Character(
                name=str(name), hp=int(hp), max_hp=int(max_hp),
                current_location_id=str(location_id_str), # Pass as string
                inventory=inventory, skills=skills, xp=int(xp),
                level=int(level), active_quests=active_quests
            )

            # Return the tuple containing the character and the loaded state
            return (character_obj, discovered_actions, discovered_llm_actions,
                    tutorial_pickaxe_taken, tutorial_blockage_cleared)
        else:
            print(f"No character found with ID {character_id}.")
            return None
    except Exception as e:
        print(f"Error loading character state: {e}")
        return None

# --- Updated Function: save_character_state (P2.3) ---
def save_character_state(
    conn: Optional[sqlite3.Connection],
    character: Character,
    discovered_actions: Set[str],
    discovered_llm_actions: Set[str],
    tutorial_pickaxe_taken: bool,
    tutorial_blockage_cleared: bool,
    character_id: int = 1
) -> bool:
    """
    Saves character state including discovered actions and tutorial flags.
    Accepts sets and booleans, converts them for storage.
    """
    if not conn:
        print("CRUD Error (Save): No DB connection.")
        return False
    if not isinstance(character, Character):
         print("CRUD Error (Save): Invalid character object.")
         return False
    # Basic type checks for new parameters
    if not isinstance(discovered_actions, set): print("CRUD Warning (Save): discovered_actions is not a set."); return False
    if not isinstance(discovered_llm_actions, set): print("CRUD Warning (Save): discovered_llm_actions is not a set."); return False
    if not isinstance(tutorial_pickaxe_taken, bool): print("CRUD Warning (Save): tutorial_pickaxe_taken is not a bool."); return False
    if not isinstance(tutorial_blockage_cleared, bool): print("CRUD Warning (Save): tutorial_blockage_cleared is not a bool."); return False


    try:
        cursor = conn.cursor()

        # --- Serialize/Convert Data for Storage (P2.3) ---
        inv_json = json.dumps(character.inventory)
        skills_json = json.dumps(character.skills)
        quests_json = json.dumps(character.active_quests)
        # Convert sets to lists before serializing to JSON
        discovered_actions_json = json.dumps(list(discovered_actions))
        discovered_llm_actions_json = json.dumps(list(discovered_llm_actions))
        # Convert booleans to integers (0 or 1)
        tutorial_pickaxe_taken_int = 1 if tutorial_pickaxe_taken else 0
        tutorial_blockage_cleared_int = 1 if tutorial_blockage_cleared else 0
        # --- End Serialization/Conversion ---

        print(f"Saving (P2.3): ID={character_id}, Lvl={character.level}, XP={character.xp}, HP={character.hp}, MaxHP={character.max_hp}, LocID='{character.current_location_id}'...")
        print(f"  Saving Discovered Actions: {len(discovered_actions)}")
        print(f"  Saving LLM Actions: {len(discovered_llm_actions)}")
        print(f"  Saving Tutorial Flags: Pickaxe={tutorial_pickaxe_taken_int}, Blockage={tutorial_blockage_cleared_int}")


        # Update the UPDATE statement to include all columns
        cursor.execute("""
            UPDATE characters
            SET hp = ?, max_hp = ?, current_location_id = ?, inventory = ?, skills = ?, xp = ?, level = ?, active_quests = ?,
                discovered_actions = ?, discovered_llm_actions = ?, tutorial_pickaxe_taken = ?, tutorial_blockage_cleared = ?
            WHERE id = ?
        """, (
            # Core Character attributes
            character.hp, character.max_hp, str(character.current_location_id), # Ensure string
            inv_json, skills_json, character.xp, character.level, quests_json,
            # Persistence attributes (serialized/converted)
            discovered_actions_json, discovered_llm_actions_json,
            tutorial_pickaxe_taken_int, tutorial_blockage_cleared_int,
            # WHERE clause parameter
            character_id
            ))
        conn.commit()

        if cursor.rowcount == 0:
             print(f"Warning: Save character state did not update any rows for ID {character_id}.")
             # Consider if this should return False or if init should guarantee row exists

        print("Character state saved successfully (P2.3).")
        return True
    except Exception as e:
        print(f"Error saving character state: {e}")
        try:
            conn.rollback() # Attempt rollback on error
        except Exception as rb_e:
            print(f"Error during rollback after save error: {rb_e}")
        return False


# --- Optional: Basic test block (Refactored) ---
if __name__ == '__main__':
    print("\n--- CRUD Test (String Loc IDs & All Fields - No Semicolons) ---")
    # !!! NOTE: This test block needs updating in Step P2.4 !!!
    db_conn = get_db_connection()

    if db_conn:
        print("\nTesting Initialization...")
        init_success = initialize_character_row_if_not_exists(db_conn, char_id=1)
        print(f"Initialization reported success: {init_success}")

        if init_success:
            print("\nTesting Load (P2.2)...")
            # --- Update Load Test Call ---
            loaded_data = load_character_state(db_conn, character_id=1)

            if loaded_data:
                # --- Update Unpacking ---
                loaded_char, loaded_discovered, loaded_llm, loaded_pickaxe, loaded_blockage = loaded_data
                print(f"Loaded Character (P2.2): {loaded_char}")
                print(f"  Loaded Discovered: {loaded_discovered}")
                print(f"  Loaded LLM: {loaded_llm}")
                print(f"  Loaded Tutorial: Pickaxe={loaded_pickaxe}, Blockage={loaded_blockage}")

                # --- Modify state for saving (P2.3/P2.4 Test) ---
                # Modify core character stats
                loaded_char.hp = max(0, loaded_char.hp - 1)
                if loaded_char.current_location_id == 'entry_cave': loaded_char.current_location_id = 'narrow_corridor'
                else: loaded_char.current_location_id = 'entry_cave'
                loaded_char.add_item("test_save_item_str_4")
                loaded_char.skills['saved_skill_str_4'] = loaded_char.skills.get('saved_skill_str_4', 0) + 1
                loaded_char.remove_quest('get_pickaxe')
                loaded_char.add_quest('test_save_quest_str_4')
                leveled = loaded_char.add_xp(10)

                # Modify persistence state directly for test
                test_discovered_actions = loaded_discovered.copy()
                test_discovered_actions.add("look")
                test_discovered_actions.add("go")
                test_llm_actions = loaded_llm.copy()
                test_llm_actions.add("dance")
                test_pickaxe_flag = not loaded_pickaxe # Flip the boolean
                test_blockage_flag = not loaded_blockage # Flip the boolean
                # --- End Modify State ---

                print(f"Modified Character State for Save (P2.3): {loaded_char}")
                print(f"  Modified Discovered: {test_discovered_actions}")
                print(f"  Modified LLM: {test_llm_actions}")
                print(f"  Modified Tutorial: Pickaxe={test_pickaxe_flag}, Blockage={test_blockage_flag}")


                print("\nTesting Save (P2.3)...")
                # --- Update Save call (P2.3) ---
                save_success = save_character_state(
                    db_conn, loaded_char,
                    test_discovered_actions, test_llm_actions,
                    test_pickaxe_flag, test_blockage_flag,
                    character_id=1
                )
                print(f"Save reported success: {save_success}")

                if save_success:
                    print("\nTesting Load After Save (P2.2)...")
                    # --- Update Reload Test Call ---
                    reloaded_data = load_character_state(db_conn, character_id=1)
                    if reloaded_data:
                        # --- Update Unpacking ---
                        reloaded_char, reloaded_discovered, reloaded_llm, reloaded_pickaxe, reloaded_blockage = reloaded_data
                        print(f"Re-loaded Character (P2.2): {reloaded_char}")
                        print(f"  Re-loaded Discovered: {reloaded_discovered}")
                        print(f"  Re-loaded LLM: {reloaded_llm}")
                        print(f"  Re-loaded Tutorial: Pickaxe={reloaded_pickaxe}, Blockage={reloaded_blockage}")

                        # --- Verification (Should pass now if P2.4 updates test block correctly) ---
                        hp_match = reloaded_char.hp == loaded_char.hp
                        max_hp_match = reloaded_char.max_hp == loaded_char.max_hp
                        loc_match = reloaded_char.current_location_id == loaded_char.current_location_id
                        inv_match = reloaded_char.inventory == loaded_char.inventory
                        skills_match = reloaded_char.skills == loaded_char.skills
                        xp_match = reloaded_char.xp == loaded_char.xp
                        level_match = reloaded_char.level == loaded_char.level
                        quests_match = reloaded_char.active_quests == loaded_char.active_quests
                        # --- Add Persistence Field Verification (P2.3) ---
                        discovered_match = reloaded_discovered == test_discovered_actions # Compare reloaded set to the set we tried to save
                        llm_match = reloaded_llm == test_llm_actions
                        pickaxe_match = reloaded_pickaxe == test_pickaxe_flag
                        blockage_match = reloaded_blockage == test_blockage_flag

                        if (hp_match and max_hp_match and loc_match and inv_match and skills_match and
                            xp_match and level_match and quests_match and discovered_match and
                            llm_match and pickaxe_match and blockage_match):
                            print("VERIFICATION: All changes saved/loaded correctly!")
                        else:
                            print("VERIFICATION FAILED:")
                            if not hp_match: print(f"  HP mismatch")
                            if not max_hp_match: print(f"  Max HP mismatch")
                            if not loc_match: print(f"  Location ID mismatch")
                            if not inv_match: print(f"  Inventory mismatch")
                            if not skills_match: print(f"  Skills mismatch")
                            if not xp_match: print(f"  XP mismatch")
                            if not level_match: print(f"  Level mismatch")
                            if not quests_match: print(f"  Quests mismatch")
                            # --- Add Persistence Field Mismatch Info ---
                            if not discovered_match: print(f"  Discovered Actions mismatch (Expected: {test_discovered_actions}, Got: {reloaded_discovered})")
                            if not llm_match: print(f"  LLM Actions mismatch (Expected: {test_llm_actions}, Got: {reloaded_llm})")
                            if not pickaxe_match: print(f"  Tutorial Pickaxe mismatch (Expected: {test_pickaxe_flag}, Got: {reloaded_pickaxe})")
                            if not blockage_match: print(f"  Tutorial Blockage mismatch (Expected: {test_blockage_flag}, Got: {reloaded_blockage})")
                    else:
                        print("Failed to reload character after saving.")
                else:
                    print("Skipping reload test because save failed.")
            else:
                print("Failed to load character initially.")
        else:
             print("Failed to initialize character row.")

        # Close connection
        db_conn.close()
        print("\nDatabase connection closed.")
    else:
        print("Cannot run CRUD tests: Database connection failed.")

    print("-----------------")


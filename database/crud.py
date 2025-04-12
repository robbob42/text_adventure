# database/crud.py
# Refactored: Removed ALL multi-statement lines using semicolons.

import sqlite3
import json
from typing import Optional, Dict, Any, List

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

            cursor.execute("""
                INSERT INTO characters (id, name, hp, max_hp, current_location_id, inventory, skills, xp, level, active_quests)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                quests_json
            ))
            conn.commit()
            print("Character row initialized.")
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


def load_character_state(conn: Optional[sqlite3.Connection], character_id: int = 1) -> Optional[Character]:
    """Loads character state using string location ID."""
    if not conn:
        print("CRUD Error (Load): No DB connection.")
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, hp, max_hp, current_location_id, inventory, skills, xp, level, active_quests FROM characters WHERE id = ?", (character_id,))
        row = cursor.fetchone()

        if row:
            name, hp, max_hp, location_id_str, inv_json, skills_json, xp, level, quests_json = row

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

            print(f"Loaded: ID={character_id}, Lvl={level}, XP={xp}, HP={hp}, MaxHP={max_hp}, LocID='{location_id_str}'...")

            # Create and return Character object
            return Character(
                name=str(name), hp=int(hp), max_hp=int(max_hp),
                current_location_id=str(location_id_str), # Pass as string
                inventory=inventory, skills=skills, xp=int(xp),
                level=int(level), active_quests=active_quests
            )
        else:
            print(f"No character found with ID {character_id}.")
            return None
    except Exception as e:
        print(f"Error loading character state: {e}")
        return None


def save_character_state(conn: Optional[sqlite3.Connection], character: Character, character_id: int = 1) -> bool:
    """Saves character state using string location ID."""
    if not conn:
        print("CRUD Error (Save): No DB connection.")
        return False
    if not isinstance(character, Character):
         print("CRUD Error (Save): Invalid character object.")
         return False

    try:
        cursor = conn.cursor()
        inv_json = json.dumps(character.inventory)
        skills_json = json.dumps(character.skills)
        quests_json = json.dumps(character.active_quests)

        print(f"Saving: ID={character_id}, Lvl={character.level}, XP={character.xp}, HP={character.hp}, MaxHP={character.max_hp}, LocID='{character.current_location_id}'...")

        cursor.execute("""
            UPDATE characters
            SET hp = ?, max_hp = ?, current_location_id = ?, inventory = ?, skills = ?, xp = ?, level = ?, active_quests = ?
            WHERE id = ?
        """, (
            character.hp, character.max_hp, str(character.current_location_id), # Ensure string
            inv_json, skills_json, character.xp, character.level, quests_json,
            character_id
            ))
        conn.commit()

        if cursor.rowcount == 0:
             print(f"Warning: Save character state did not update any rows for ID {character_id}.")
             # Consider if this should return False or if init should guarantee row exists

        print("Character state saved successfully.")
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
    db_conn = get_db_connection()

    if db_conn:
        print("\nTesting Initialization...")
        init_success = initialize_character_row_if_not_exists(db_conn, char_id=1)
        print(f"Initialization reported success: {init_success}")

        if init_success:
            print("\nTesting Load...")
            loaded_char = load_character_state(db_conn, character_id=1)

            if loaded_char:
                print(f"Loaded Character: {loaded_char}")

                # Modify state
                original_max_hp = loaded_char.max_hp
                loaded_char.hp = max(0, loaded_char.hp - 1)
                # Simulate moving - use valid string IDs from content.py
                if loaded_char.current_location_id == 'entry_cave':
                    loaded_char.current_location_id = 'narrow_corridor'
                else:
                    loaded_char.current_location_id = 'entry_cave'
                loaded_char.add_item("test_save_item_str_3") # Use unique item name
                loaded_char.skills['saved_skill_str_3'] = loaded_char.skills.get('saved_skill_str_3', 0) + 1
                loaded_char.remove_quest('get_pickaxe') # Try removing if present
                loaded_char.add_quest('test_save_quest_str_3') # Add unique quest
                leveled = loaded_char.add_xp(10) # Add some XP

                print(f"Modified Character State for Save: {loaded_char}")

                print("\nTesting Save...")
                save_success = save_character_state(db_conn, loaded_char, character_id=1)
                print(f"Save reported success: {save_success}")

                if save_success:
                    print("\nTesting Load After Save...")
                    reloaded_char = load_character_state(db_conn, character_id=1)
                    if reloaded_char:
                        print(f"Re-loaded Character: {reloaded_char}")
                        # Verification
                        hp_match = reloaded_char.hp == loaded_char.hp
                        max_hp_match = reloaded_char.max_hp == loaded_char.max_hp
                        loc_match = reloaded_char.current_location_id == loaded_char.current_location_id
                        inv_match = reloaded_char.inventory == loaded_char.inventory
                        skills_match = reloaded_char.skills == loaded_char.skills
                        xp_match = reloaded_char.xp == loaded_char.xp
                        level_match = reloaded_char.level == loaded_char.level
                        quests_match = reloaded_char.active_quests == loaded_char.active_quests

                        if hp_match and max_hp_match and loc_match and inv_match and skills_match and xp_match and level_match and quests_match:
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


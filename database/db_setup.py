# database/db_setup.py
# Refactored: Removed multi-statement lines using semicolons.
# Updated: Added columns for discovered actions and tutorial flags (Persistence Plan P1.1).
# Updated: Added location_mods table and clear function (Location Persistence Plan L1.1).

import sqlite3
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_FILE = os.path.join(BASE_DIR, 'game.db')

# --- Functions ---

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    print(f"Connecting to database at: {DATABASE_FILE}")
    conn = None
    try:
        # Enable foreign key support
        conn = sqlite3.connect(DATABASE_FILE)
        conn.execute("PRAGMA foreign_keys = ON;") # Important for foreign key constraints
        print("Database connection successful. Foreign keys enabled.")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        if conn:
            conn.close()
        return None

def create_tables(conn):
    """Creates the necessary database tables if they don't already exist."""
    if conn is None:
        print("Cannot create tables: No database connection.")
        return False

    try:
        cursor = conn.cursor()
        print("Ensuring 'characters' table schema...")
        # Using TEXT for location ID, INTEGER for level/xp, TEXT for JSON lists/dicts
        # Added columns for discovered actions (TEXT JSON) and tutorial flags (INTEGER 0/1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                hp INTEGER NOT NULL,
                max_hp INTEGER NOT NULL,
                current_location_id TEXT NOT NULL,
                inventory TEXT NOT NULL DEFAULT '[]',
                skills TEXT NOT NULL DEFAULT '{}',
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                active_quests TEXT NOT NULL DEFAULT '[]',
                discovered_actions TEXT NOT NULL DEFAULT '[]',
                discovered_llm_actions TEXT NOT NULL DEFAULT '[]',
                tutorial_pickaxe_taken INTEGER NOT NULL DEFAULT 0,
                tutorial_blockage_cleared INTEGER NOT NULL DEFAULT 0
            )
        """)
        print("'characters' table schema ensured.")

        # --- Added location_mods table (L1.1) ---
        print("Ensuring 'location_mods' table schema...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS location_mods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                location_id TEXT NOT NULL,
                mod_type TEXT NOT NULL,
                mod_data TEXT NOT NULL,
                FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
            )
        """)
        # Add index for faster lookups by character_id
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_location_mods_character_id
            ON location_mods (character_id);
        """)
        print("'location_mods' table schema ensured.")
        # --- End added table ---

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error creating/altering tables: {e}")
        return False

# --- Added clear function (L1.1) ---
def clear_location_modifications(conn: sqlite3.Connection, character_id: int) -> bool:
    """Removes all location modifications for a specific character."""
    if conn is None:
        print("Cannot clear modifications: No database connection.")
        return False
    try:
        cursor = conn.cursor()
        print(f"Clearing location modifications for character_id: {character_id}...")
        cursor.execute("DELETE FROM location_mods WHERE character_id = ?", (character_id,))
        conn.commit()
        print(f"Cleared {cursor.rowcount} location modifications.")
        return True
    except sqlite3.Error as e:
        print(f"Error clearing location modifications: {e}")
        try:
            conn.rollback()
        except Exception as rb_e:
            print(f"Error during rollback after clear error: {rb_e}")
        return False
# --- End added function ---

# --- Main Execution Block ---
if __name__ == "__main__":
    """
    Establishes a connection and ensures the tables exist with the latest schema.
    Advise deleting existing game.db before running if schema changed significantly.
    """
    print("Running DB Setup...")
    print(f"Target database file: {DATABASE_FILE}")
    print("NOTE: If you changed the table structure, delete the existing game.db file before running this.")

    connection = get_db_connection()
    setup_successful = False
    if connection:
        setup_successful = create_tables(connection)

        # --- Optional: Call clear function during setup/reset if needed ---
        # character_to_clear = 1 # Example character ID
        # if setup_successful:
        #     print(f"\nAttempting to clear existing mods for character {character_to_clear} (for testing)...")
        #     clear_success = clear_location_modifications(connection, character_to_clear)
        #     print(f"Clear operation success: {clear_success}")
        # --- End Optional Call ---

        connection.close() # Close connection after setup
        print("DB Connection closed.")
    else:
        print("DB Setup failed: Could not connect to the database.")

    if setup_successful:
        print("DB Setup Completed Successfully.")
    else:
        print("DB Setup encountered errors.")


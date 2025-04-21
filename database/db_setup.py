# database/db_setup.py
# Refactored: Removed multi-statement lines using semicolons.
# Updated: Added columns for discovered actions and tutorial flags (Persistence Plan P1.1).

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
        conn = sqlite3.connect(DATABASE_FILE)
        print("Database connection successful.")
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
        print("Creating/Updating 'characters' table (if it doesn't exist)...")
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
                -- Added Persistence Columns (Plan P1.1) --
                discovered_actions TEXT NOT NULL DEFAULT '[]',
                discovered_llm_actions TEXT NOT NULL DEFAULT '[]',
                tutorial_pickaxe_taken INTEGER NOT NULL DEFAULT 0,
                tutorial_blockage_cleared INTEGER NOT NULL DEFAULT 0
                -- End Added Columns --
            )
        """)
        conn.commit()
        print("'characters' table schema ensured.")
        return True
    except sqlite3.Error as e:
        print(f"Error creating/altering tables: {e}")
        return False

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
        connection.close() # Close connection after setup
        print("DB Connection closed.")
    else:
        print("DB Setup failed: Could not connect to the database.")

    if setup_successful:
        print("DB Setup Completed Successfully.")
    else:
        print("DB Setup encountered errors.")


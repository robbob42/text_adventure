# app/main.py
# Main entry point for the Flask web application.
# Updated: Removed redundant location header prepending in /chat endpoint.
# Updated: Handle action discovery flag from process_turn (Phase 5, Step 5.2).
# Updated: Use <br> instead of \n when combining direct message and LLM narration.
# Updated: Add discovered actions data to /state endpoint (Phase 7, Step 7.1).
# Updated: Add discovered actions data to /chat endpoint response (Phase 7, Step 7.3).

import sys
import os
import traceback # Import traceback for detailed error logging
from flask import Flask, render_template, request, jsonify
from typing import Optional, Dict, Any

# --- Add project root to sys.path to allow imports ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception as e:
     print(f"Error adjusting sys.path: {e}")
     sys.exit(1)

# --- Import game logic and database functions ---
try:
    from game_logic.game_manager import GameManager
    # Import QUESTS dictionary along with others
    from game_logic.content import PLAYER_START, SYSTEM_PROMPT, QUESTS
    from database.db_setup import get_db_connection
    from database.crud import initialize_character_row_if_not_exists, load_character_state, save_character_state
    # Import LLM interface components needed for the chat endpoint later
    from game_logic.llm_interface import get_llm_narration, llm_chain
except ImportError as e:
    print(f"ERROR: Failed to import necessary modules in app/main.py: {e}")
    print("Ensure game_logic and database packages exist and are importable from project root.")
    sys.exit(1)
except Exception as e:
     print(f"ERROR: Unexpected error during imports: {e}")
     sys.exit(1)


# --- Initialize Flask App ---
app = Flask(__name__) # Assumes templates/static are inside app/
print("Flask app initialized (using default template/static folders relative to app/main.py).")

# --- Initialize Game ---
game_manager: Optional[GameManager] = None
try:
    print("Initializing GameManager...")
    game_manager = GameManager()
    print("GameManager created with default state.")

    # --- Load Persistent State --- (Code remains the same as before)
    print("Attempting to load persistent state from database...")
    db_conn = get_db_connection()
    initial_load_success = False
    if db_conn:
        try:
            init_success = initialize_character_row_if_not_exists(db_conn, char_id=1)
            if init_success:
                loaded_character = load_character_state(db_conn, character_id=1)
                if loaded_character:
                    game_manager.character = loaded_character
                    # TODO: Restore discovered actions from save file? (Not implemented yet)
                    # TODO: Restore tutorial flags from save file? (Not implemented yet)
                    game_manager.current_location = game_manager.locations.get(loaded_character.current_location_id)
                    if game_manager.current_location is None:
                         print(f"Warning: Loaded character location ID '{loaded_character.current_location_id}' not found in LOCATIONS. Reverting to default start.")
                         default_start_id = PLAYER_START.get('current_location_id', 'entry_cave')
                         game_manager.character.current_location_id = default_start_id
                         game_manager.current_location = game_manager.locations.get(default_start_id)
                    print(f"Successfully loaded persistent state for Character ID 1: {game_manager.character}")
                    initial_load_success = True
                else:
                    print("Persistent state row exists/created for Character ID 1, but loading failed or returned None. Using default state.")
                    initial_load_success = True # Consider it success as default state is usable
            else:
                print("Failed to initialize character row in database. Cannot load state.")
        except Exception as e:
            print(f"Error during database initialization/load: {e}")
        finally:
            if db_conn:
                db_conn.close()
                print("Initial database connection closed.")
    else:
        print("Failed to connect to database for initial load. Using default game state.")
    if not initial_load_success: print("Warning: Proceeding with default game state potentially due to DB load issues.")
except ValueError as e: print(f"CRITICAL ERROR during GameManager initialization: {e}"); sys.exit(1)
except Exception as e: print(f"CRITICAL ERROR: An unexpected error occurred during app setup: {e}"); sys.exit(1)


# --- Routes ---
@app.route('/')
def index(): print("Serving index page..."); return render_template('index.html')

@app.route('/state')
def get_initial_state():
    """Returns current game state including discovered actions."""
    print("--- Received /state request ---")
    if game_manager and game_manager.character and game_manager.current_location:
        active_quest_names = [QUESTS.get(qid)['name'] for qid in game_manager.character.active_quests if qid in QUESTS]
        response_data = {
            'character_status': {
                'hp': game_manager.character.hp,
                'max_hp': game_manager.character.max_hp,
                'level': game_manager.character.level,
                'xp': game_manager.character.xp,
                'xp_needed': game_manager.character.level * 100
            },
            'inventory': game_manager.character.inventory,
            'active_quests': active_quest_names,
            'location_name': game_manager.current_location.name,
            # --- Added Actions Discovered Data (Phase 7, Step 7.1) ---
            'discovered_actions': sorted(list(game_manager.discovered_actions)),
            'total_actions': game_manager.total_actions
            # --- End Added Data ---
        }
        return jsonify(response_data)
    else:
        print("Error: GameManager not ready for /state.");
        # Return default structure including new keys
        return jsonify({
            "error": "Game state not available.",
            "character_status": {},
            "inventory": [],
            "active_quests": [],
            "location_name": "Unknown",
            # --- Added Default Actions Data (Phase 7, Step 7.1) ---
            "discovered_actions": [],
            "total_actions": 0
            # --- End Added Data ---
        }), 500

# --- Chat Endpoint ---
@app.route('/chat', methods=['POST'])
def chat():
    """Handles incoming chat messages from the player."""
    print("\n--- Received /chat request ---")
    # --- Input handling ---
    if not request.is_json: return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json(); player_input = data.get('input', None)
    if not player_input: return jsonify({"error": "Missing 'input'"}), 400
    print(f"Player input: '{player_input}'")
    # Add default actions keys to initial error response
    if game_manager is None:
        return jsonify({
            "reply": "[Game Error: Not ready]",
            "character_status": {}, "inventory": [], "active_quests": [],
            "discovered_actions": [], "total_actions": 0 # Default actions
            }), 500

    # --- Process turn ---
    try:
        # Unpack the new return values from process_turn (Step 5.1 Revised)
        direct_message, original_llm_data, newly_discovered, discovered_verb = game_manager.process_turn(player_input)
        print(f"GM direct: '{direct_message}'")
        print(f"GM LLM data: {original_llm_data}")
        print(f"GM Discovery: {newly_discovered}, Verb: {discovered_verb}")

        # --- Handle Action Discovery Feedback (Step 5.2) ---
        llm_prompt_data = original_llm_data # Start with the original data

        if newly_discovered and discovered_verb:
            print(f"Overriding LLM prompt for discovery of '{discovered_verb}'")
            # Create a specific prompt for the LLM to congratulate the player
            llm_prompt_data = {
                'action': 'discovery', # Special action type for the LLM prompt context
                'discovered_verb': discovered_verb,
                'success': True, # Discovery is always a success
                # Message to guide the LLM's response
                'message': f"NEW ACTION DISCOVERED! Congratulate the player on discovering how to use the '{discovered_verb}' command. Briefly explain its general purpose (e.g., 'look' is for observing surroundings, 'get' is for picking things up, 'attack' is for combat)."
            }
        # --- End Discovery Override ---

    except Exception as e:
        print(f"Error during process_turn: {e}"); traceback.print_exc();
        active_quest_names_err = [QUESTS.get(qid)['name'] for qid in game_manager.character.active_quests if qid in QUESTS] if game_manager.character else []
        # Add default actions keys to error response (Phase 7.3)
        return jsonify({
            "reply": "[Game Error: Internal error processing turn.]",
            "character_status": { 'hp': game_manager.character.hp, 'max_hp': game_manager.character.max_hp, 'level': game_manager.character.level, 'xp': game_manager.character.xp, 'xp_needed': game_manager.character.level * 100 } if game_manager.character else {},
            "inventory": game_manager.character.inventory if game_manager.character else [],
            "active_quests": active_quest_names_err,
            "discovered_actions": sorted(list(game_manager.discovered_actions)) if game_manager else [], # Current state if possible
            "total_actions": game_manager.total_actions if game_manager else 0
            }), 500

    # --- LLM Interaction ---
    llm_narration = ""
    # Use the potentially overridden llm_prompt_data here
    if llm_prompt_data and llm_chain:
        print("LLM interaction required...")
        try:
            # Prepare the full state dictionary for the LLM prompt
            inventory_str = ", ".join(game_manager.character.inventory) if game_manager.character.inventory else "Empty"
            skills_str = str(game_manager.character.skills) if game_manager.character.skills else "None"
            active_quests_prompt_str = "None"
            if game_manager.character.active_quests:
                quest_details_list = [f"- {QUESTS.get(qid,{}).get('name', qid)}" for qid in game_manager.character.active_quests]
                active_quests_prompt_str = "\n".join(quest_details_list) if quest_details_list else "None"

            current_state_for_llm = { # Ensure all keys match llm_interface.input_variables
                "system_prompt": SYSTEM_PROMPT or "Default",
                "location_name": game_manager.current_location.name if game_manager.current_location else "?",
                "location_id": str(game_manager.current_location.id) if game_manager.current_location else "unknown",
                "char_name": game_manager.character.name,
                "char_hp": game_manager.character.hp,
                "max_hp": game_manager.character.max_hp,
                "level": game_manager.character.level,
                "xp": game_manager.character.xp,
                "inventory_list_str": inventory_str,
                "skills_dict_str": skills_str,
                "active_quests_str": active_quests_prompt_str,
                "location_description": game_manager.current_location.get_full_description() if game_manager.current_location else "Void",
                # Use the 'message' field from the (potentially overridden) llm_prompt_data
                "action_outcome": llm_prompt_data.get('message', '') if isinstance(llm_prompt_data, dict) else '',
                "player_input": player_input
            }
            llm_narration = get_llm_narration(current_state_for_llm)
            print("LLM narration received.")
        except Exception as e:
            print(f"Error during get_llm_narration: {e}"); traceback.print_exc();
            llm_narration = "[Error processing narration]"
    elif llm_prompt_data:
        print("LLM data present, but LLM chain unavailable.");
        llm_narration = "[LLM narration skipped]"

    # --- Combine messages ---
    final_reply_content = ""
    # Use <br> for HTML line break instead of \n
    if direct_message and llm_narration:
        final_reply_content = f"{direct_message}<br>{llm_narration}" # Use <br> here
    elif llm_narration:
        final_reply_content = llm_narration
    else:
        final_reply_content = direct_message

    final_reply = final_reply_content.strip() # strip() is fine, won't affect internal <br>
    print(f"Final reply being sent (length: {len(final_reply)}): '{final_reply[:200]}...'")

    # --- Save state ---
    if game_manager.character:
        print("Saving character state..."); db_conn_save = get_db_connection(); save_success = False
        if db_conn_save:
            try:
                # TODO: Persist discovered_actions and tutorial flags?
                save_success = save_character_state(db_conn_save, game_manager.character, character_id=1)
            except Exception as e: print(f"Error during save: {e}")
            finally: db_conn_save.close(); print(f"Save connection closed. Success: {save_success}")
        else: print("Failed to get DB connection for saving.")
    else: print("Skipping save state.")

    # --- Return JSON response ---
    active_quest_names_resp = [QUESTS.get(qid)['name'] for qid in game_manager.character.active_quests if qid in QUESTS] if game_manager.character else []
    # Add discovered actions data to the final response (Phase 7.3)
    response_data = {
        'reply': final_reply,
        'character_status': {
            'hp': game_manager.character.hp,
            'max_hp': game_manager.character.max_hp,
            'level': game_manager.character.level,
            'xp': game_manager.character.xp,
            'xp_needed': game_manager.character.level * 100
            } if game_manager.character else {},
        'inventory': game_manager.character.inventory if game_manager.character else [],
        'active_quests': active_quest_names_resp,
        # --- Added Actions Discovered Data ---
        'discovered_actions': sorted(list(game_manager.discovered_actions)),
        'total_actions': game_manager.total_actions
        # --- End Added Data ---
    }
    return jsonify(response_data)


# --- Run Application ---
if __name__ == '__main__':
    if game_manager is None: print("CRITICAL ERROR: GameManager failed init."); sys.exit(1)
    print("Starting Flask server..."); app.run(debug=True, host='0.0.0.0', port=5000)


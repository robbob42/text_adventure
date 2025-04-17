# app/routes.py
# Contains Flask route definitions for the application.
# Refactored: Moved LLM interaction logic to chat_helpers.py (Phase 12.3).
# Fixed: Changed relative imports within 'app' package to absolute imports.
# Refactored: Using Blueprint instead of importing app directly.
# Refactored: Importing game_manager from app package (__init__).

import traceback
from flask import render_template, request, jsonify, Blueprint # Import Blueprint
from typing import Optional, Dict, Any

print("--- Executing app/routes.py ---")

# --- Create a Blueprint ---
bp = Blueprint('main_routes', __name__, url_prefix='/') # Added url_prefix just in case
print("--- Blueprint 'main_routes' created ---")

# --- Import game_manager from app package (__init__.py) ---
try:
    # Import the globally initialized instance from the app package
    from app import game_manager_instance as game_manager
    print("--- Imported game_manager_instance into routes.py ---")
    if game_manager is None:
        print("ERROR: game_manager_instance is None in routes.py!")
        # This indicates an initialization order issue or failure in __init__.py
        raise ImportError("game_manager instance not available")
except ImportError:
    print("ERROR: Could not import game_manager_instance from app in routes.py")
    raise

# --- Import necessary game logic components ---
try:
    from game_logic.content import QUESTS
    from app.chat_helpers import get_llm_response
    from database.crud import save_character_state
    from database.db_setup import get_db_connection
    print("--- Imported game/DB components into routes.py ---")
except ImportError as e:
    print(f"ERROR importing components in routes.py: {e}")
    QUESTS = {}
    def get_llm_response(*args): return "[LLM Helper Error]"
    def save_character_state(*args): return False
    def get_db_connection(): return None
    raise RuntimeError(f"Failed imports in routes: {e}") from e


# --- Route Definitions (using the Blueprint 'bp') ---

# Note: url_prefix='/' was added to Blueprint, so route is just '/'
@bp.route('/')
def index():
    """Serves the main game page."""
    print("--- index() route function called ---")
    print("Serving index page (from routes.py)...")
    return render_template('index.html')

# Note: url_prefix='/', so route is just '/state'
@bp.route('/state')
def get_initial_state():
    """Returns current game state including discovered actions."""
    print("--- get_initial_state() route function called ---")
    print("--- Received /state request (in routes.py) ---")
    if game_manager and game_manager.character and game_manager.current_location:
        active_quest_names = [QUESTS.get(qid, {}).get('name', 'Unknown Quest') for qid in game_manager.character.active_quests]
        response_data = {
            'character_status': {
                'hp': game_manager.character.hp, 'max_hp': game_manager.character.max_hp,
                'level': game_manager.character.level, 'xp': game_manager.character.xp,
                'xp_needed': game_manager.character.level * 100
            },
            'inventory': game_manager.character.inventory,
            'active_quests': active_quest_names,
            'location_name': game_manager.current_location.name,
            'discovered_actions': sorted(list(game_manager.discovered_actions)),
            'total_actions': game_manager.total_actions,
            'discovered_llm_actions': sorted(list(game_manager.discovered_llm_actions))
        }
        return jsonify(response_data)
    else:
        print("Error: GameManager not ready for /state (in routes.py).")
        return jsonify({
            "error": "Game state not available.", "character_status": {},
            "inventory": [], "active_quests": [], "location_name": "Unknown",
            "discovered_actions": [], "total_actions": 0, "discovered_llm_actions": []
        }), 500

# Note: url_prefix='/', so route is just '/chat'
@bp.route('/chat', methods=['POST'])
def chat():
    """Handles incoming chat messages from the player."""
    print("\n--- chat() route function called ---")
    print("\n--- Received /chat request (in routes.py) ---")
    # --- Input handling ---
    if not request.is_json: return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json(); player_input = data.get('input', None)
    if not player_input: return jsonify({"error": "Missing 'input'"}), 400
    print(f"Player input: '{player_input}'")
    if game_manager is None: # Check the imported instance
        return jsonify({
            "reply": "[Game Error: Not ready]", "character_status": {},
            "inventory": [], "active_quests": [], "discovered_actions": [],
            "total_actions": 0, "discovered_llm_actions": []
            }), 500

    # --- Process turn ---
    try:
        direct_message, original_llm_data, newly_discovered, discovered_verb = game_manager.process_turn(player_input)
        print(f"GM direct: '{direct_message}'")
        print(f"GM LLM data: {original_llm_data}")
        print(f"GM Discovery: {newly_discovered}, Verb: {discovered_verb}")

        # --- Handle Action Discovery Feedback ---
        llm_prompt_data = original_llm_data
        if newly_discovered and discovered_verb:
            print(f"Overriding LLM prompt for discovery of '{discovered_verb}'")
            llm_prompt_data = {
                'action': 'discovery', 'discovered_verb': discovered_verb, 'success': True,
                'message': f"NEW ACTION DISCOVERED! Congratulate the player on discovering how to use the '{discovered_verb}' command. Briefly explain its general purpose (e.g., 'look' is for observing surroundings, 'get' is for picking things up, 'attack' is for combat)."
            }
        # --- End Discovery Override ---

        # --- LLM Interaction (Moved to Helper Function - Phase 12.3) ---
        llm_narration = get_llm_response(game_manager, llm_prompt_data, player_input)
        # --- End LLM Interaction ---

    except Exception as e:
        print(f"Error during process_turn or get_llm_response: {e}"); traceback.print_exc();
        active_quest_names_err = [QUESTS.get(qid, {}).get('name', 'Unknown Quest') for qid in game_manager.character.active_quests] if game_manager.character else []
        return jsonify({
            "reply": "[Game Error: Internal error processing turn.]",
            "character_status": { 'hp': game_manager.character.hp, 'max_hp': game_manager.character.max_hp, 'level': game_manager.character.level, 'xp': game_manager.character.xp, 'xp_needed': game_manager.character.level * 100 } if game_manager.character else {},
            "inventory": game_manager.character.inventory if game_manager.character else [],
            "active_quests": active_quest_names_err,
            "discovered_actions": sorted(list(game_manager.discovered_actions)) if game_manager else [],
            "total_actions": game_manager.total_actions if game_manager else 0,
            "discovered_llm_actions": sorted(list(game_manager.discovered_llm_actions)) if game_manager else []
            }), 500

    # --- Combine messages ---
    final_reply_content = ""
    if direct_message and llm_narration:
        final_reply_content = f"{direct_message}<br>{llm_narration}"
    elif llm_narration:
        final_reply_content = llm_narration
    else:
        final_reply_content = direct_message
    final_reply = final_reply_content.strip()
    print(f"Final reply being sent (length: {len(final_reply)}): '{final_reply[:200]}...'")

    # --- Save state ---
    if game_manager.character:
        print("Saving character state..."); db_conn_save = get_db_connection(); save_success = False
        if db_conn_save:
            try:
                save_success = save_character_state(db_conn_save, game_manager.character, character_id=1)
            except Exception as e: print(f"Error during save: {e}")
            finally: db_conn_save.close(); print(f"Save connection closed. Success: {save_success}")
        else: print("Failed to get DB connection for saving.")
    else: print("Skipping save state.")

    # --- Return JSON response ---
    active_quest_names_resp = [QUESTS.get(qid, {}).get('name', 'Unknown Quest') for qid in game_manager.character.active_quests] if game_manager.character else []
    response_data = {
        'reply': final_reply,
        'character_status': {
            'hp': game_manager.character.hp, 'max_hp': game_manager.character.max_hp,
            'level': game_manager.character.level, 'xp': game_manager.character.xp,
            'xp_needed': game_manager.character.level * 100
            } if game_manager.character else {},
        'inventory': game_manager.character.inventory if game_manager.character else [],
        'active_quests': active_quest_names_resp,
        'discovered_actions': sorted(list(game_manager.discovered_actions)),
        'total_actions': game_manager.total_actions,
        'discovered_llm_actions': sorted(list(game_manager.discovered_llm_actions))
    }
    return jsonify(response_data)


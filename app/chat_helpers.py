# app/chat_helpers.py
# Contains helper functions specifically for the /chat route,
# primarily for handling LLM interaction logic.

import traceback
from typing import Optional, Dict, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import for GameManager hint
if TYPE_CHECKING:
    from game_logic.game_manager import GameManager

# Import necessary components for LLM call
try:
    from game_logic.content import SYSTEM_PROMPT, QUESTS
    from game_logic.llm_interface import get_llm_narration, llm_chain
except ImportError as e:
    print(f"ERROR importing game logic/LLM components in chat_helpers.py: {e}")
    # Define dummies or raise error depending on desired robustness
    SYSTEM_PROMPT = "Default Prompt"
    QUESTS = {}
    def get_llm_narration(state): return "[LLM Error]"
    llm_chain = None
    # Re-raise might be better for critical components
    raise RuntimeError(f"Failed imports in chat_helpers: {e}") from e


def get_llm_response(game_manager: 'GameManager', llm_prompt_data: Optional[Dict], player_input: str) -> str:
    """
    Prepares state, calls the LLM if needed, and returns the narration.

    Args:
        game_manager: The active GameManager instance.
        llm_prompt_data: The dictionary containing data/instructions for the LLM,
                         or None if no LLM call is needed.
        player_input: The original input from the player.

    Returns:
        The LLM narration string, or an empty string if no call was made or failed.
    """
    llm_narration = ""
    if llm_prompt_data and llm_chain and game_manager and game_manager.character and game_manager.current_location:
        print("LLM interaction required (called from chat_helpers)...")
        try:
            # Prepare the full state dictionary for the LLM prompt
            inventory_str = ", ".join(game_manager.character.inventory) if game_manager.character.inventory else "Empty"
            skills_str = str(game_manager.character.skills) if game_manager.character.skills else "None"
            active_quests_prompt_str = "None"
            if game_manager.character.active_quests:
                # Use safer dictionary access with default
                quest_details_list = [f"- {QUESTS.get(qid, {}).get('name', qid)}" for qid in game_manager.character.active_quests]
                active_quests_prompt_str = "\n".join(quest_details_list) if quest_details_list else "None"

            current_state_for_llm = { # Ensure all keys match llm_interface.input_variables
                "system_prompt": SYSTEM_PROMPT or "Default",
                "location_name": game_manager.current_location.name,
                "location_id": str(game_manager.current_location.id),
                "char_name": game_manager.character.name,
                "char_hp": game_manager.character.hp,
                "max_hp": game_manager.character.max_hp,
                "level": game_manager.character.level,
                "xp": game_manager.character.xp,
                "inventory_list_str": inventory_str,
                "skills_dict_str": skills_str,
                "active_quests_str": active_quests_prompt_str,
                "location_description": game_manager.current_location.get_full_description(),
                # Use the 'message' field from the llm_prompt_data
                "action_outcome": llm_prompt_data.get('message', '') if isinstance(llm_prompt_data, dict) else '',
                "player_input": player_input
            }
            # Call the actual LLM interface function
            llm_narration = get_llm_narration(current_state_for_llm)
            print("LLM narration received (in chat_helpers).")
        except Exception as e:
            print(f"Error during get_llm_narration call from helper: {e}")
            traceback.print_exc()
            llm_narration = "[Error processing narration]"
    elif llm_prompt_data:
        # LLM was requested, but chain isn't available
        print("LLM data present, but LLM chain unavailable (in chat_helpers).")
        llm_narration = "[LLM narration skipped]"
    else:
        # No LLM data provided, no LLM call needed
        pass

    return llm_narration


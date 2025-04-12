# game_logic/actions/combat.py
# Contains action handlers related to combat.

import random
from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import issues
if TYPE_CHECKING:
    from ..game_manager import GameManager # For type hinting

def handle_attack(manager: 'GameManager', target_name: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'attack' command. Performs a simple attack calculation against an NPC.

    Args:
        manager: The GameManager instance containing the game state.
        target_name: The name of the target the player wants to attack.

    Returns:
        A tuple: (direct_message, llm_prompt_data).
                 llm_prompt_data contains the outcome dict if attack is possible.
                 direct_message contains error or minimal confirmation.
    """
    llm_prompt_data = None # Default to no LLM data needed

    if not target_name:
        return ("Attack what? Please specify a target.", llm_prompt_data)
    if not manager.current_location:
        return ("Cannot attack: Current location is unknown.", llm_prompt_data)

    # Find the NPC using the helper method on the Location object
    npc_dict = manager.current_location.find_npc_by_name(target_name)

    if not npc_dict:
        return (f"You don't see '{target_name}' here to attack.", llm_prompt_data)

    # --- If target found, perform attack ---
    actual_target_desc = npc_dict.get('description', target_name) # Use description for clarity
    hit_chance = 0.6 # Example: 60% chance to hit
    damage = 5 # Example: Fixed damage for MVP
    is_hit = random.random() < hit_chance

    # Prepare outcome dictionary for the LLM prompt
    llm_prompt_data = {
        'action': 'attack',
        'target': actual_target_desc,
        'hit': is_hit,
        'damage': damage if is_hit else 0,
        'message': f"You attack the {actual_target_desc}." # Basic context message for prompt
    }

    # Provide minimal direct feedback, let the LLM describe the action's result
    direct_message = f"You attempt to attack the {actual_target_desc}..."

    # TODO (Later Phase):
    # - Check if attack defeats NPC (requires NPC HP tracking).
    # - If defeated, remove NPC from location, grant XP (manager.character.add_xp(amount)).
    # - Update the llm_prompt_data dict with defeat information.

    print(f"Attack outcome generated: {llm_prompt_data}") # Server log
    return (direct_message, llm_prompt_data) # Return minimal message and outcome dict

# --- Add other combat-related handlers here later (e.g., defend, flee) ---


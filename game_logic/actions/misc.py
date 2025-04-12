# game_logic/actions/misc.py
# Contains action handlers for miscellaneous commands, including LLM-only actions.

from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import issues
if TYPE_CHECKING:
    from ..game_manager import GameManager # For type hinting

def handle_llm_only_action(manager: 'GameManager', command: str, argument: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles actions that don't have specific game logic and should be narrated by the LLM.

    Args:
        manager: The GameManager instance (passed for consistency, though not used here).
        command: The command verb the player typed (e.g., 'dance', 'sing').
        argument: Any arguments provided after the command verb.

    Returns:
        A tuple: (direct_message, llm_prompt_data).
                 direct_message is a minimal confirmation.
                 llm_prompt_data contains info about the attempted action for the LLM.
    """
    # Minimal direct feedback to the player
    direct_message = f"You attempt to {command}..."
    if argument:
        direct_message = f"You attempt to {command} {argument}..."

    # Prepare data for the LLM prompt's 'action_outcome' field
    llm_prompt_data = {
        'action': 'narrative_action', # Indicate this was just an attempt for narration
        'command': command,
        'argument': argument,
        'success': True, # Assume the attempt itself 'succeeds' for narration purposes
        'message': f"You try to {command}{f' {argument}' if argument else ''}." # Context for LLM
    }

    print(f"LLM-Only Action outcome generated: {llm_prompt_data}") # Server log
    return (direct_message, llm_prompt_data)

# --- Add other miscellaneous handlers here later (e.g., help, quit) ---


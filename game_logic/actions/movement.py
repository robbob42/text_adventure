# game_logic/actions/movement.py
# Updated handle_go to add a <br> after the location header on success.

from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import issues
if TYPE_CHECKING:
    from ..game_manager import GameManager # For type hinting

def handle_go(manager: 'GameManager', direction: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'go' command. Attempts to move the character in the specified direction.

    Args:
        manager: The GameManager instance containing the game state.
        direction: The direction the player wants to move (e.g., 'north').

    Returns:
        A tuple: (direct_message, llm_prompt_data).
                 On success, direct_message includes header, <br>, and new location description.
                 On failure, direct_message is an error message.
                 llm_prompt_data is None for this action.
    """
    llm_prompt_data = None # 'go' action doesn't need specific LLM outcome data

    if not direction:
        return ("Go where? Please specify a direction (e.g., 'go north').", llm_prompt_data)

    if not manager.current_location:
        return ("Cannot move: Current location is unknown.", llm_prompt_data)

    # Find the exit using the method on the Location object
    target_location_id = manager.current_location.get_exit(direction)

    if target_location_id is None:
        return ("You can't go that way.", llm_prompt_data)

    # Find the new location object from the manager's dictionary
    new_location = manager.locations.get(target_location_id)
    if new_location is None:
        print(f"ERROR: Location data inconsistency in handle_go. ID '{target_location_id}' not found in manager.locations.")
        return ("Error: That path seems to lead nowhere (invalid location ID defined in content).", llm_prompt_data)

    # --- Success Case: Update state and return formatted description ---
    manager.character.current_location_id = target_location_id
    manager.current_location = new_location
    print(f"Character moved to {manager.current_location.name}") # Server log

    # Format the output string including header, HTML break, then description
    location_name = manager.current_location.name
    description = manager.current_location.get_full_description() # Contains internal <br><br>
    # Added <br> after the bold tag
    direct_message = f"<b>Current Location: {location_name}</b><br>\n\n{description}"

    return (direct_message, llm_prompt_data)

# --- Add other movement-related handlers here later if needed ---


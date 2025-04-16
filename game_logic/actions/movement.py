# game_logic/actions/movement.py
# Contains action handlers related to player movement.
# Updated: Added tutorial gate logic for entry_cave exit (Phase 2, Step 1).

from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import issues
if TYPE_CHECKING:
    from ..game_manager import GameManager # For type hinting

def handle_go(manager: 'GameManager', direction: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'go [direction]' command. Moves the character if the exit is valid.
    Includes tutorial gate logic for 'entry_cave'.

    Args:
        manager: The GameManager instance.
        direction: The direction the player wants to move (e.g., 'north', 'east').

    Returns:
        Tuple (direct_message, llm_prompt_data). llm_prompt_data is None.
    """
    llm_prompt_data = None # No LLM needed for movement confirmation

    # --- Tutorial Gate: Entry Cave Exit (Phase 2, Step 1) ---
    if manager.character.current_location_id == 'entry_cave':
        # Check if the player is trying to leave via a valid exit direction for this cave
        target_exit_id = manager.current_location.get_exit(direction) if manager.current_location and direction else None

        if target_exit_id: # Only intervene if they specified a valid direction out
            if not manager.tutorial_blockage_cleared:
                # Blockage is NOT cleared, prevent movement and give hint
                if not manager.tutorial_pickaxe_taken:
                    # Hint: Need a tool
                    print("Tutorial Gate: Blocked (No Pickaxe)") # Log
                    return ("The exit is blocked by a pile of rubble. You might need a tool to clear it.", None)
                else:
                    # Hint: Have the tool, need to use it
                    print("Tutorial Gate: Blocked (Has Pickaxe, Not Used)") # Log
                    return ("You have the pickaxe. Perhaps you could use it to clear the rubble blocking the exit?", None)
            else:
                # Blockage IS cleared, allow movement to proceed normally by falling through
                print("Tutorial Gate: Passed (Blockage Cleared)") # Log
        # else: Direction was None or invalid for this room, let normal logic handle below.

    # --- End Tutorial Gate ---


    # --- Original Movement Logic ---
    if not direction:
        return ("Go where? Please specify a direction (e.g., north, east, up).", llm_prompt_data)
    if not manager.current_location:
        return ("Cannot move: Current location is unknown.", llm_prompt_data)

    # Get the target location ID using the helper method
    next_location_id = manager.current_location.get_exit(direction)

    if next_location_id is None:
        return (f"You can't go {direction} from here.", llm_prompt_data)

    # Check if the target location exists in the game manager's dictionary
    next_location = manager.locations.get(next_location_id)
    if next_location is None:
        # This indicates an issue in the content.py data (exit points to non-existent location)
        print(f"ERROR: Location '{manager.current_location.id}' exit '{direction}' points to invalid ID '{next_location_id}'.")
        return ("[Error] That path seems to lead nowhere (Invalid location ID).", llm_prompt_data)

    # --- Update Character and Game State ---
    manager.character.current_location_id = next_location_id
    manager.current_location = next_location # Update manager's current location object
    print(f"Player moved to: {next_location.name} (ID: {next_location.id})")

    # Return the description of the new location using handle_look's logic
    # This avoids duplicating the description generation code.
    # We call handle_look internally to get the formatted description.
    look_message, _ = handle_look(manager, None) # Argument is ignored by handle_look
    return (look_message, llm_prompt_data)


# --- Import handle_look at the end to avoid circular dependency issues ---
# If handle_look were needed by other functions in this file, imports might need restructuring.
try:
    from .observation import handle_look
except ImportError:
    print("ERROR: Failed to import handle_look from observation.py in movement.py")
    # Define a dummy if import fails, so the 'go' command doesn't crash
    def handle_look(manager, argument):
        return ("You arrive at the new location.", None)

# --- Add other movement-related handlers here later (e.g., enter, climb) ---

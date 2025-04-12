# game_logic/actions/observation.py
# Updated handle_look to add a <br> after the location header.

from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import issues
if TYPE_CHECKING:
    # Assumes GameManager is in the parent directory (game_logic)
    from ..game_manager import GameManager # For type hinting

# Import QUESTS needed for handle_quests
try:
    # Assumes content.py is in the parent directory (game_logic)
    from ..content import QUESTS
except ImportError:
    print("ERROR: Could not import QUESTS from content in observation.py")
    QUESTS = {} # Provide default empty dict if import fails

def handle_look(manager: 'GameManager', argument: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'look' command. Returns the location header (with <br>) and full description.
    Argument is ignored.
    """
    llm_prompt_data = None # No LLM data needed
    if manager.current_location:
        location_name = manager.current_location.name
        description = manager.current_location.get_full_description() # This contains <br><br> internally now
        # Format the output string with header, HTML break, then description
        direct_message = f"<b>Current Location: {location_name}</b><br>\n\n{description}" # Added <br>
    else:
        direct_message = "You are lost in the void. No location data available."
    return (direct_message, llm_prompt_data)

def handle_inventory(manager: 'GameManager', argument: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'inventory' or 'inv' command. Returns a string listing inventory.
    Argument is ignored.
    """
    llm_prompt_data = None
    if not manager.character.inventory:
        direct_message = "Your inventory is empty."
    else:
        item_list_str = ", ".join(manager.character.inventory)
        direct_message = f"You are carrying: {item_list_str}."
    return (direct_message, llm_prompt_data)

def handle_status(manager: 'GameManager', argument: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'status' command. Returns character status summary.
    Argument is ignored.
    """
    llm_prompt_data = None
    xp_needed = manager.character.level * 100
    status_lines = [
        f"Name: {manager.character.name}",
        f"Level: {manager.character.level}",
        f"XP: {manager.character.xp} / {xp_needed}",
        f"HP: {manager.character.hp} / {manager.character.max_hp}",
        f"Skills: {manager.character.skills if manager.character.skills else 'None'}",
        f"Location: {manager.current_location.name if manager.current_location else 'Unknown'}"
    ]
    direct_message = "\n".join(status_lines) # Keep \n here as it's for console-like status block
    return (direct_message, llm_prompt_data)

def handle_quests(manager: 'GameManager', argument: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'quests' or 'journal' command. Returns list of active quests.
    Argument is ignored.
    """
    llm_prompt_data = None
    if not manager.character.active_quests:
        direct_message = "You have no active quests."
    else:
        quest_lines = ["Active Quests:"]
        for quest_id in manager.character.active_quests:
            quest_data = QUESTS.get(quest_id) # Use imported QUESTS
            if quest_data:
                quest_lines.append(f"- {quest_data.get('name', 'Unknown Quest')}: {quest_data.get('description', 'No description.')}")
            else:
                quest_lines.append(f"- Unknown Quest (ID: {quest_id})")
        direct_message = "\n".join(quest_lines) # Keep \n here for list formatting
    return (direct_message, llm_prompt_data)


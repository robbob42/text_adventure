# game_logic/actions/observation.py
# Handles looking, inventory, status, quests.
# Updated handle_look to add a <br> after the location header.
# Updated handle_look for Phase 3, Step 2: Add dynamic description based on tutorial state in entry_cave.

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
    Handles the 'look' command. Returns the location header and full description.
    Includes dynamic description logic for 'entry_cave' tutorial state.
    Argument is ignored for looking at the current location.
    """
    # TODO: Implement 'look [item/npc]' functionality if argument is provided.
    # For now, assume argument means look at the current location.

    llm_prompt_data = None # No LLM data needed for basic look

    if manager.current_location:
        location_name = manager.current_location.name
        # Get the base description, which includes item/NPC/exit lists formatted with <br>
        description = manager.current_location.get_full_description()

        # --- Tutorial Dynamic Description (Phase 3, Step 2) ---
        if manager.character.current_location_id == 'entry_cave':
            # Define the specific sentence we might replace or add hints about
            blockage_sentence = "A narrow passage leading east is blocked by a pile of <b>rubble</b>."

            if manager.tutorial_blockage_cleared:
                # If cleared, replace the blockage sentence in the description string
                # Ensure the replacement target string exactly matches the one in content.py
                description = description.replace(
                    blockage_sentence,
                    "The narrow passage leading east is now clear of <b>rubble</b>."
                )
                print("Dynamic Look: Rubble cleared.") # Log
            elif manager.tutorial_pickaxe_taken:
                 # If not cleared, but pickaxe is taken, append a hint (with HTML break)
                 description += "<br><i>Maybe the <b>pickaxe</b> could clear the <b>rubble</b>?</i>" # Hint in italics
                 print("Dynamic Look: Hint added (has pickaxe).") # Log
            # Else (not cleared, no pickaxe): Use original description from get_full_description()
            else:
                 print("Dynamic Look: Using standard description (no pickaxe/not cleared).") # Log
        # --- End Tutorial Dynamic Description ---

        # Format the final output string with header, HTML break, then potentially modified description
        direct_message = f"<b>Current Location: {location_name}</b><br>\n\n{description}"
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
    # Use <br> for HTML display in chat log instead of \n
    direct_message = "<br>".join(status_lines)
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
        quest_lines = ["<b>Active Quests:</b>"] # Add bold header
        for quest_id in manager.character.active_quests:
            quest_data = QUESTS.get(quest_id) # Use imported QUESTS
            if quest_data:
                # Add quest name and description
                quest_lines.append(f"- <b>{quest_data.get('name', 'Unknown Quest')}</b>: {quest_data.get('description', 'No description.')}")
            else:
                quest_lines.append(f"- Unknown Quest (ID: {quest_id})")
        # Use <br> for HTML display in chat log
        direct_message = "<br>".join(quest_lines)
    return (direct_message, llm_prompt_data)


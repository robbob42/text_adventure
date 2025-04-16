# game_logic/actions/interaction.py
# Contains action handlers related to interacting with items and NPCs.
# Updated: Added tutorial flag update to handle_get (Phase 1, Step 2).
# Updated: Added tutorial logic to handle_use for pickaxe on rubble (Phase 1, Step 3).
# Updated: Generalized check: require target for 'use [item]' command.
# Updated: Added specific feedback for using pickaxe on wrong target in entry_cave (Phase 3, Step 3).

from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import issues
if TYPE_CHECKING:
    from ..game_manager import GameManager # For type hinting

def handle_get(manager: 'GameManager', item_name: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'get' or 'take' command. Moves an item from the location to inventory.

    Args:
        manager: The GameManager instance.
        item_name: The name of the item to take.

    Returns:
        Tuple (direct_message, llm_prompt_data). llm_prompt_data is None.
    """
    llm_prompt_data = None # No LLM needed for simple get confirmation

    if not item_name:
        return ("Get what? Please specify an item.", llm_prompt_data)
    if not manager.current_location:
        return ("Cannot get items: Current location is unknown.", llm_prompt_data)

    # Find item in location (case-insensitive)
    item_dict = manager.current_location.find_item_by_name(item_name)

    if not item_dict:
        return (f"You don't see '{item_name}' here.", llm_prompt_data)

    # Check if the item is gettable
    if not item_dict.get('gettable', False):
        # Use description if available, else name
        item_desc = item_dict.get('description', item_dict.get('name', item_name))
        return (f"You can't take the {item_desc}.", llm_prompt_data)

    # Item found and is gettable, proceed to move it
    # Use the actual name from the dict for consistency
    actual_item_name = item_dict.get('name', item_name)

    # Remove from location first
    removed_item = manager.current_location.remove_item(actual_item_name)

    if removed_item:
        manager.character.add_item(actual_item_name) # Add to player inventory

        # --- Tutorial Check: Pickaxe Taken (Phase 1, Step 2) ---
        if actual_item_name.lower() == 'pickaxe' and manager.character.current_location_id == 'entry_cave':
            if not manager.tutorial_pickaxe_taken: # Check flag before setting
                manager.tutorial_pickaxe_taken = True
                print("Tutorial flag set: tutorial_pickaxe_taken = True") # Log for debugging
            else:
                print("Tutorial flag tutorial_pickaxe_taken was already True.") # Log
        # --- End Tutorial Check ---

        return (f"You take the {actual_item_name}.", llm_prompt_data)
    else:
        # This case should ideally not happen if find_item_by_name worked, but good to handle
        print(f"Error: Item '{actual_item_name}' found but failed to remove from location '{manager.current_location.id}'.")
        return ("[Error] Tried to take the item, but it seems stuck.", llm_prompt_data)


def handle_drop(manager: 'GameManager', item_name: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'drop' command. Moves an item from inventory to the location.

    Args:
        manager: The GameManager instance.
        item_name: The name of the item to drop.

    Returns:
        Tuple (direct_message, llm_prompt_data). llm_prompt_data is None.
    """
    llm_prompt_data = None # No LLM needed

    if not item_name:
        return ("Drop what? Please specify an item.", llm_prompt_data)
    if not manager.current_location:
        return ("Cannot drop items: Current location is unknown.", llm_prompt_data)

    # Check if player has the item (case-insensitive)
    item_to_drop = next((item for item in manager.character.inventory if item.lower() == item_name.lower()), None)

    if not item_to_drop:
        return (f"You don't have '{item_name}' to drop.", llm_prompt_data)

    # Remove from inventory
    if manager.character.remove_item(item_to_drop):
        # Add to location - need to reconstruct a basic item dict
        # For simplicity, just use name and a generic description
        # TODO: Could store original item dicts if needed for richer descriptions
        item_dict_to_add = {
            'name': item_to_drop,
            'description': f'{item_to_drop} lying on the ground',
            'gettable': True # Dropped items should be gettable
        }
        manager.current_location.add_item(item_dict_to_add)
        return (f"You drop the {item_to_drop}.", llm_prompt_data)
    else:
        # Should not happen if item_to_drop was found
        print(f"Error: Item '{item_to_drop}' found in inventory but failed to remove.")
        return ("[Error] Tried to drop the item, but couldn't.", llm_prompt_data)


def handle_use(manager: 'GameManager', argument: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'use' command. Requires 'use [item] on [target]' format.
    Includes specific logic for tutorial pickaxe use.

    Args:
        manager: The GameManager instance.
        argument: The full argument string (e.g., "pickaxe on rubble").

    Returns:
        Tuple (direct_message, llm_prompt_data).
    """
    llm_prompt_data = None # Default

    if not argument:
        return ("Use what? And on what?", llm_prompt_data)

    # Basic parsing: "use [item]" or "use [item] on [target]"
    parts = argument.lower().split(" on ", 1)
    item_name = parts[0].strip()
    target_name = parts[1].strip() if len(parts) > 1 else None

    # Check if player has the item
    if not manager.character.has_item(item_name):
        return (f"You don't have a {item_name}.", llm_prompt_data)

    # Check if target is missing for *any* item
    if target_name is None:
        # Use f-string to include the specific item name in the prompt
        return (f"Use {item_name} on what?", None) # Return specific message, no LLM needed

    # --- ADDED: Tutorial check for using pickaxe on wrong target in cave (Phase 3, Step 3) ---
    if manager.character.current_location_id == 'entry_cave' and item_name == 'pickaxe' and target_name != 'rubble':
        # Provide specific feedback for using pickaxe on wrong target in the tutorial room
        # Use target_name from the parsed input for the message
        return (f"Using the pickaxe on the {target_name} doesn't seem to do anything useful here.", None)
    # --- END ADDED CHECK ---

    # --- Tutorial: Use Pickaxe on Rubble (Phase 1, Step 3) ---
    # Define the specific conditions for the tutorial action
    is_entry_cave = manager.character.current_location_id == 'entry_cave'
    is_pickaxe = item_name == 'pickaxe'
    is_target_rubble = target_name == 'rubble' # Assuming 'rubble' is the target

    if is_entry_cave and is_pickaxe and is_target_rubble:
        if manager.tutorial_blockage_cleared:
            # Rubble already cleared
            return ("The rubble blocking the exit is already cleared.", None)
        else:
            # Clear the blockage
            manager.tutorial_blockage_cleared = True
            print("Tutorial flag set: tutorial_blockage_cleared = True") # Log for debugging
            # Return specific success message, no LLM needed
            return ("With a swing of the pickaxe, the rubble blocking the exit crumbles! The way is clear.", None)
    # --- End Tutorial Logic ---

    # --- Other Specific Use Cases ---
    # Example: Using a 'key' on a 'door' (if implemented later)
    # if item_name == 'key' and target_name == 'door':
    #     # Check location for a locked door, unlock it, etc.
    #     return ("You unlock the door.", None)

    # --- Default/Fallback ---
    # If no specific logic handled the use case (including tutorial failure), provide generic feedback.
    # We might want the LLM to narrate this attempt.
    direct_message = f"You try to use the {item_name}"
    if target_name: # This should always be true now if we reached here
        direct_message += f" on the {target_name}"
    direct_message += "."

    # Prepare data for LLM if we want it to narrate the attempt/failure
    llm_prompt_data = {
        'action': 'use',
        'item': item_name,
        'target': target_name,
        'success': False, # Assume failure unless specific logic handles it
        'message': f"{direct_message} Nothing seems to happen." # Context for LLM
    }

    # Return the generic message and the LLM data
    return (direct_message, llm_prompt_data)


def handle_talk(manager: 'GameManager', npc_name: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'talk' command. Initiates dialogue with an NPC.

    Args:
        manager: The GameManager instance.
        npc_name: The name of the NPC to talk to.

    Returns:
        Tuple (direct_message, llm_prompt_data). llm_prompt_data contains dialogue.
    """
    llm_prompt_data = None # Default

    if not npc_name:
        return ("Talk to whom?", llm_prompt_data)
    if not manager.current_location:
        return ("Cannot talk: Current location is unknown.", llm_prompt_data)

    # Find NPC (case-insensitive substring match)
    npc_dict = manager.current_location.find_npc_by_name(npc_name)

    if not npc_dict:
        return (f"You don't see anyone named '{npc_name}' here.", llm_prompt_data)

    # Get dialogue from NPC data (default if missing)
    dialogue = npc_dict.get('dialogue', '"..." (They don\'t seem talkative.)')
    actual_npc_name = npc_dict.get('name', npc_name) # Use actual name

    # Prepare data for LLM prompt
    llm_prompt_data = {
        'action': 'talk',
        'npc': actual_npc_name,
        'dialogue': dialogue,
        'message': f"You talk to the {actual_npc_name}." # Context for LLM
    }

    # Minimal direct message, let LLM present the dialogue
    direct_message = f"You approach the {actual_npc_name}..."

    print(f"Talk outcome generated: {llm_prompt_data}") # Server log
    return (direct_message, llm_prompt_data)

# --- Add other interaction handlers here later (e.g., give) ---

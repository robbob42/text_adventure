# game_logic/actions/interaction.py
# Contains action handlers related to interacting with items and NPCs.
# Updated: Added tutorial flag update to handle_get (Phase 1, Step 2).
# Updated: Added tutorial logic to handle_use for pickaxe on rubble (Phase 1, Step 3).
# Updated: Generalized check: require target for 'use [item]' command.
# Updated: Added specific feedback for using pickaxe on wrong target in entry_cave (Phase 3, Step 3).
# Updated: Call record_location_modification when rubble is cleared (Location Persistence Plan L3.2).

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

    if not item_name: return ("Get what? Please specify an item.", llm_prompt_data)
    if not manager.current_location: return ("Cannot get items: Current location is unknown.", llm_prompt_data)

    item_dict = manager.current_location.find_item_by_name(item_name)
    if not item_dict: return (f"You don't see '{item_name}' here.", llm_prompt_data)
    if not item_dict.get('gettable', False):
        item_desc = item_dict.get('description', item_dict.get('name', item_name))
        return (f"You can't take the {item_desc}.", llm_prompt_data)

    actual_item_name = item_dict.get('name', item_name)
    removed_item = manager.current_location.remove_item(actual_item_name)

    if removed_item:
        manager.character.add_item(actual_item_name)
        if actual_item_name.lower() == 'pickaxe' and manager.character.current_location_id == 'entry_cave':
            if not manager.tutorial_pickaxe_taken:
                manager.tutorial_pickaxe_taken = True
                print("Tutorial flag set: tutorial_pickaxe_taken = True")
            else: print("Tutorial flag tutorial_pickaxe_taken was already True.")
        return (f"You take the {actual_item_name}.", llm_prompt_data)
    else:
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

    if not item_name: return ("Drop what? Please specify an item.", llm_prompt_data)
    if not manager.current_location: return ("Cannot drop items: Current location is unknown.", llm_prompt_data)

    item_to_drop = next((item for item in manager.character.inventory if item.lower() == item_name.lower()), None)
    if not item_to_drop: return (f"You don't have '{item_name}' to drop.", llm_prompt_data)

    if manager.character.remove_item(item_to_drop):
        item_dict_to_add = { 'name': item_to_drop, 'description': f'{item_to_drop} lying on the ground', 'gettable': True }
        manager.current_location.add_item(item_dict_to_add)
        return (f"You drop the {item_to_drop}.", llm_prompt_data)
    else:
        print(f"Error: Item '{item_to_drop}' found in inventory but failed to remove.")
        return ("[Error] Tried to drop the item, but couldn't.", llm_prompt_data)


def handle_use(manager: 'GameManager', argument: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'use' command. Requires 'use [item] on [target]' format.
    Includes specific logic for tutorial pickaxe use and saving location mod.

    Args:
        manager: The GameManager instance.
        argument: The full argument string (e.g., "pickaxe on rubble").

    Returns:
        Tuple (direct_message, llm_prompt_data).
    """
    llm_prompt_data = None # Default

    if not argument: return ("Use what? And on what?", llm_prompt_data)

    parts = argument.lower().split(" on ", 1)
    item_name = parts[0].strip()
    target_name = parts[1].strip() if len(parts) > 1 else None

    if not manager.character.has_item(item_name): return (f"You don't have a {item_name}.", llm_prompt_data)
    if target_name is None: return (f"Use {item_name} on what?", None)

    # Tutorial check for using pickaxe on wrong target in cave
    if manager.character.current_location_id == 'entry_cave' and item_name == 'pickaxe' and target_name != 'rubble':
        return (f"Using the pickaxe on the {target_name} doesn't seem to do anything useful here.", None)

    # Tutorial: Use Pickaxe on Rubble
    is_entry_cave = manager.character.current_location_id == 'entry_cave'
    is_pickaxe = item_name == 'pickaxe'
    is_target_rubble = target_name == 'rubble'

    if is_entry_cave and is_pickaxe and is_target_rubble:
        if manager.tutorial_blockage_cleared:
            return ("The rubble blocking the exit is already cleared.", None)
        else:
            # Clear the blockage - Set flag first
            manager.tutorial_blockage_cleared = True
            print("Tutorial flag set: tutorial_blockage_cleared = True")

            # --- Record Location Modification (L3.2) ---
            # Define the new description that should persist
            new_description = "You stand just inside the mouth of a dark, damp cave. Water drips steadily from the ceiling. The air smells earthy and cold. The narrow passage leading east is now clear of <b>rubble</b>. A rusty <b>pickaxe</b> lies discarded in a corner near the entrance."
            # Call the GameManager method to save this change
            manager.record_location_modification(
                location_id='entry_cave',
                mod_type='CHANGE_DESC',
                mod_data=new_description
            )
            # --- End Record Modification ---

            # Return specific success message, no LLM needed
            return ("With a swing of the pickaxe, the rubble blocking the exit crumbles! The way is clear.", None)
    # --- End Tutorial Logic ---

    # --- Default/Fallback ---
    direct_message = f"You try to use the {item_name} on the {target_name}."
    llm_prompt_data = { 'action': 'use', 'item': item_name, 'target': target_name, 'success': False, 'message': f"{direct_message} Nothing seems to happen." }
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

    if not npc_name: return ("Talk to whom?", llm_prompt_data)
    if not manager.current_location: return ("Cannot talk: Current location is unknown.", llm_prompt_data)

    npc_dict = manager.current_location.find_npc_by_name(npc_name)
    if not npc_dict: return (f"You don't see anyone named '{npc_name}' here.", llm_prompt_data)

    dialogue = npc_dict.get('dialogue', '"..." (They don\'t seem talkative.)')
    actual_npc_name = npc_dict.get('name', npc_name)
    llm_prompt_data = { 'action': 'talk', 'npc': actual_npc_name, 'dialogue': dialogue, 'message': f"You talk to the {actual_npc_name}." }
    direct_message = f"You approach the {actual_npc_name}..."
    print(f"Talk outcome generated: {llm_prompt_data}")
    return (direct_message, llm_prompt_data)

# --- Add other interaction handlers here later (e.g., give) ---

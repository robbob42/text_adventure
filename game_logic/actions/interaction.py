# game_logic/actions/interaction.py
# Contains action handlers related to player interaction with items and NPCs.

from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import issues
if TYPE_CHECKING:
    from ..game_manager import GameManager # For type hinting

def handle_get(manager: 'GameManager', item_name: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Handles the 'get' or 'take' command."""
    llm_prompt_data = None # No LLM data needed for simple get

    if not item_name:
        return ("Get what? Please specify an item.", llm_prompt_data)
    if not manager.current_location:
        return ("Cannot get items: Location unknown.", llm_prompt_data)

    item_dict = manager.current_location.find_item_by_name(item_name)

    if not item_dict:
        return (f"You don't see '{item_name}' here.", llm_prompt_data)

    if not item_dict.get('gettable', False):
        return (f"You can't take the {item_name}.", llm_prompt_data)

    # Try removing from location (returns dict if successful)
    removed_item = manager.current_location.remove_item(item_name)
    if removed_item:
        # Add name to character inventory
        item_name_to_add = removed_item.get('name', item_name)
        manager.character.add_item(item_name_to_add)
        direct_message = f"You take the {item_name_to_add}."
        # --- Quest Check Trigger ---
        # We call check_quest_completion from process_turn, so no need here directly
        # But this is where the state change happens that the check looks for.
    else:
        print(f"Error: Found item '{item_name}' but failed to remove it from location.")
        direct_message = f"You try to take the {item_name}, but something prevents it."

    return (direct_message, llm_prompt_data)


def handle_drop(manager: 'GameManager', item_name: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Handles the 'drop' command."""
    llm_prompt_data = None # No LLM data needed

    if not item_name:
        return ("Drop what? Please specify an item from your inventory.", llm_prompt_data)
    if not manager.current_location:
        return ("Cannot drop items: Location unknown.", llm_prompt_data)

    # remove_item from character returns True/False
    if manager.character.remove_item(item_name):
        # Add item back to location as a simple dict
        dropped_item_dict = {'name': item_name, 'description': f'a dropped {item_name}', 'gettable': True}
        manager.current_location.add_item(dropped_item_dict)
        direct_message = f"You drop the {item_name}."
    else:
        # remove_item already printed failure, but return message for UI
        direct_message = f"You don't have '{item_name}' to drop."

    return (direct_message, llm_prompt_data)


def handle_use(manager: 'GameManager', item_name: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'use' command. Implements basic item effects.
    Returns outcome dict for LLM if effect needs narration.
    """
    direct_message = ""
    llm_prompt_data = None

    if not item_name:
        return ("Use what? Please specify an item from your inventory.", llm_prompt_data)

    if not manager.character.has_item(item_name):
        return (f"You don't have '{item_name}' to use.", llm_prompt_data)

    item_name_lower = item_name.lower()

    # --- Implement specific item effects ---
    if item_name_lower == 'potion': # Example: Healing Potion
        if manager.character.hp < manager.character.max_hp:
            manager.character.remove_item(item_name) # Consume
            heal_amount = 10
            manager.character.heal(heal_amount)
            # Prepare data for LLM narration
            llm_prompt_data = {
                'action': 'use_item', 'item': item_name,
                'effect': f'healed {heal_amount} HP', 'success': True,
                'message': f"You drink the {item_name}."
            }
            direct_message = f"You use the {item_name}." # Minimal direct message
        else:
            direct_message = "You are already at full health." # No LLM needed

    elif item_name_lower == 'pickaxe':
         # Using pickaxe might just need narrative flair from LLM
         llm_prompt_data = {
             'action': 'use_item', 'item': item_name, 'success': True,
             'message': f"You ready the {item_name}, looking around."
         }
         direct_message = f"You ready the {item_name}."

    # --- Default for other items ---
    else:
        direct_message = f"You can't figure out how to use the {item_name} right now."
        # No LLM needed if use fails simply

    return (direct_message, llm_prompt_data)


def handle_talk(manager: 'GameManager', npc_name: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Handles the 'talk' or 'ask' command. Returns predefined dialogue."""
    llm_prompt_data = None # Simple talk doesn't need LLM outcome data

    if not npc_name:
        return ("Talk to whom?", llm_prompt_data)
    if not manager.current_location:
        return ("Cannot talk: Location unknown.", llm_prompt_data)

    npc_dict = manager.current_location.find_npc_by_name(npc_name)

    if not npc_dict:
        return (f"There is no one called '{npc_name}' here to talk to.", llm_prompt_data)

    # Return the simple dialogue string from content.py
    dialogue = npc_dict.get('dialogue', f"The {npc_dict.get('name', npc_name)} doesn't seem responsive.")
    speaker = npc_dict.get('name', npc_name).capitalize()
    direct_message = f'{speaker} says: "{dialogue}"'

    # --- Quest Trigger Placeholder ---
    # Later, talking might trigger quests:
    # quest_id_triggered = npc_dict.get('starts_quest')
    # if quest_id_triggered: manager.character.add_quest(quest_id_triggered); direct_message += "\n(New quest added!)"

    return (direct_message, llm_prompt_data)


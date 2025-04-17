# game_logic/quest_logic.py
# Contains functions related to quest checking and logic.
# Created in Refactoring Phase 13.5

from typing import Optional

# Import necessary components
try:
    from .models import Character
    from .content import QUESTS
except ImportError as e:
    print(f"ERROR importing modules in quest_logic.py: {e}")
    # Define dummies for robustness
    class Character:
        active_quests: list = []
        current_location_id: str = ""
        level: int = 0
        def has_item(self, item_name: str) -> bool: return False
        def remove_quest(self, quest_id: str): pass
        def add_xp(self, amount: int) -> bool: return False
    QUESTS = {}
    raise RuntimeError(f"Failed imports in quest_logic: {e}") from e


def check_quest_completion(character: Character) -> Optional[str]:
    """
    Checks if any active quests for the given character are completed based on
    their current state (inventory, location).

    Args:
        character: The Character object whose quests should be checked.

    Returns:
        A string message describing the completed quest and reward,
        or None if no quests were completed this check.
    """
    if not character:
        return None # Cannot check without a character

    completed_quest_id = None
    quest_details = None

    # Iterate through a copy of the list to allow safe removal
    for quest_id in character.active_quests[:]:
        quest_data = QUESTS.get(quest_id)
        if not quest_data:
            print(f"Warning: Quest data not found for active quest ID: {quest_id}")
            continue # Skip if quest data missing

        criteria = quest_data.get('completion_criteria', {})
        criteria_type = criteria.get('type')

        # Check criteria based on type
        if criteria_type == 'has_item':
            item_name = criteria.get('item_name')
            if item_name and character.has_item(item_name):
                completed_quest_id = quest_id
                quest_details = quest_data
                break # Complete one quest per turn
        elif criteria_type == 'reach_location':
            target_loc_id_str = criteria.get('location_id')
            # Use the character's current location ID for the check
            if target_loc_id_str and character.current_location_id == target_loc_id_str:
                completed_quest_id = quest_id
                quest_details = quest_data
                break # Complete one quest per turn
        # --- Add other criteria checks here later ---
        # elif criteria_type == 'defeat_npc':
        #    npc_name = criteria.get('npc_name')
        #    # Requires tracking defeated NPCs, perhaps in Character or GameManager state
        #    if npc_name and character.has_defeated(npc_name): # Hypothetical method
        #        completed_quest_id = quest_id; quest_details = quest_data; break

    # Process completion if found
    if completed_quest_id and quest_details:
        print(f"Quest '{completed_quest_id}' completed!")
        character.remove_quest(completed_quest_id) # Modify character directly
        xp_reward = quest_details.get('xp_reward', 0)
        leveled_up = character.add_xp(xp_reward) # Modify character directly

        msg = f"Quest Completed: {quest_details.get('name', '?')}! (+ {xp_reward} XP)"
        if leveled_up:
            msg += f"\n*** You reached Level {character.level}! ***"
        return msg # Return the completion message

    return None # No quest completed this check


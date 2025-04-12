# game_logic/actions/skills.py
# Contains action handlers related to character skills.

import random
from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import issues
if TYPE_CHECKING:
    from ..game_manager import GameManager # For type hinting

def handle_skill_check(manager: 'GameManager', skill_name: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handles the 'check [skill]' command. Performs a simple skill check.

    Args:
        manager: The GameManager instance containing the game state.
        skill_name: The name of the skill to check (e.g., 'perception').

    Returns:
        A tuple: (direct_message, llm_prompt_data).
                 llm_prompt_data contains the outcome dict for the LLM.
                 direct_message contains minimal confirmation text.
    """
    llm_prompt_data = None # Default

    if not skill_name:
        return ("Check what skill? Please specify a skill name.", llm_prompt_data)

    # Get skill value from character, defaulting to 0 if unknown
    skill_value = manager.character.get_skill(skill_name)

    # Simple check: Roll 1d10 + skill value vs a fixed DC (e.g., 7)
    roll = random.randint(1, 10)
    dc = 7 # Fixed Difficulty Class for MVP+
    success = (roll + skill_value) >= dc

    # Prepare outcome dictionary for the LLM prompt
    llm_prompt_data = {
        'action': 'skill_check',
        'skill': skill_name,
        'roll': roll,
        'value': skill_value,
        'dc': dc,
        'success': success,
        # Message provides context for the LLM
        'message': f"You attempt to use your {skill_name} skill (Roll: {roll} + Skill: {skill_value} vs DC: {dc})..."
    }

    # Provide minimal direct feedback, let the LLM describe success/failure
    direct_message = f"You focus, attempting a {skill_name} check..."

    print(f"Skill Check outcome generated: {llm_prompt_data}") # Server log
    return (direct_message, llm_prompt_data)

# --- Add other skill-related handlers here later ---


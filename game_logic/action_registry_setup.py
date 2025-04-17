# game_logic/action_registry_setup.py
# Defines the function to build the action registry for the game.
# Fixed: Added missing 'Optional' import from typing.

from typing import Dict, Any, Callable, Union, Tuple, Optional # Added Optional

# --- Import Action Handlers ---
# Use try-except for robustness during development/import path issues
try:
    from .actions.movement import handle_go
    from .actions.observation import handle_look, handle_inventory, handle_status, handle_quests
    from .actions.interaction import handle_get, handle_drop, handle_use, handle_talk
    from .actions.combat import handle_attack
    from .actions.skills import handle_skill_check
    from .actions.misc import handle_llm_only_action
    HANDLERS_LOADED = True
except ImportError as e:
    print(f"ERROR importing action handlers in action_registry_setup.py: {e}")
    # Define dummy functions if import fails to allow registry build attempt
    def handle_go(*args): return ("Error: Movement actions not loaded.", None)
    def handle_look(*args): return ("Error: Observation actions not loaded.", None)
    def handle_inventory(*args): return ("Error: Observation actions not loaded.", None)
    def handle_status(*args): return ("Error: Observation actions not loaded.", None)
    def handle_quests(*args): return ("Error: Observation actions not loaded.", None)
    def handle_get(*args): return ("Error: Interaction actions not loaded.", None)
    def handle_drop(*args): return ("Error: Interaction actions not loaded.", None)
    def handle_use(*args): return ("Error: Interaction actions not loaded.", None)
    def handle_talk(*args): return ("Error: Interaction actions not loaded.", None)
    def handle_attack(*args): return ("Error: Combat actions not loaded.", None)
    def handle_skill_check(*args): return ("Error: Skill actions not loaded.", None)
    def handle_llm_only_action(*args): return ("Attempting action...", {'action': 'narrative_action', 'command': 'unknown', 'argument': None, 'success': True, 'message': 'Trying something...'})
    HANDLERS_LOADED = False


# --- Import LLM Command List ---
try:
    from .llm_commands import LLM_ONLY_COMMANDS
except ImportError:
    print("ERROR importing LLM_ONLY_COMMANDS in action_registry_setup.py. Using empty list.")
    LLM_ONLY_COMMANDS = []

# --- Type Aliases (can be defined here or imported if shared) ---
# Forward reference for GameManager might be needed if type hint is used directly
# ActionHandler = Callable[['GameManager', Optional[str]], Tuple[str, Optional[Dict[str, Any]]]]
# Using Any for now to simplify, or import GameManager under TYPE_CHECKING if needed elsewhere
ActionHandler = Callable[[Any, Optional[str]], Tuple[str, Optional[Dict[str, Any]]]]
RegistryValue = Union[ActionHandler, str]

# --- Constants ---
LLM_ONLY = "LLM_ONLY" # Marker for LLM handled commands

def build_action_registry() -> Tuple[Dict[str, RegistryValue], Dict[str, str], Dict[str, str]]:
    """
    Builds the action registry dictionary mapping command verbs/aliases
    to handler functions or the LLM_ONLY marker. Also builds helper maps.

    Returns:
        A tuple containing:
        - action_registry (Dict[str, RegistryValue]): The main command registry.
        - ALIAS_MAP (Dict[str, str]): Map of aliases to canonical verbs.
        - DIRECTION_NAMES (Dict[str, str]): Map of direction aliases/names to full names.
    """
    action_registry: Dict[str, RegistryValue] = {}

    if HANDLERS_LOADED:
        # 1. Define canonical verbs mapped to handlers
        action_registry = {
            # Movement
            "go": handle_go,
            # Observation
            "look": handle_look,
            "inventory": handle_inventory,
            "status": handle_status,
            "quests": handle_quests,
            # Interaction
            "get": handle_get,
            "drop": handle_drop,
            "use": handle_use,
            "talk": handle_talk,
            # Combat
            "attack": handle_attack,
            # Skills
            "check": handle_skill_check,
        }
        print(f"Initialized registry with {len(action_registry)} canonical handlers.")

        # 2. Add LLM_ONLY commands from the imported list
        llm_added_count = 0
        for command in LLM_ONLY_COMMANDS:
            if command not in action_registry: # Avoid overwriting canonical verbs
                action_registry[command] = LLM_ONLY
                llm_added_count += 1
            else:
                print(f"Warning: LLM_ONLY command '{command}' conflicts with canonical/alias and was NOT added.")
        print(f"Added {llm_added_count} LLM_ONLY commands.")

        # 3. Define and add aliases
        aliases = {
            "north": handle_go, "n": handle_go, "south": handle_go, "s": handle_go,
            "east": handle_go, "e": handle_go, "west": handle_go, "w": handle_go,
            "up": handle_go, "u": handle_go, "down": handle_go, "d": handle_go,
            "l": handle_look, "examine": handle_look,
            "inv": handle_inventory, "i": handle_inventory,
            "stats": handle_status, "score": handle_status,
            "journal": handle_quests, "q": handle_quests,
            "take": handle_get,
            "ask": handle_talk,
            "hit": handle_attack, "fight": handle_attack,
        }
        # Add aliases, potentially overwriting LLM_ONLY commands if conflict exists (aliases take precedence)
        alias_added_count = 0
        for alias, handler in aliases.items():
             if alias in action_registry and action_registry[alias] != handler:
                 print(f"Warning: Alias '{alias}' overwrites existing registry entry '{action_registry[alias]}'.")
             action_registry[alias] = handler
             alias_added_count +=1
        print(f"Added {alias_added_count} aliases.")

    else:
        print("ERROR: Action handlers not loaded. Registry will be empty.")

    # 4. Define helper maps needed by process_turn
    ALIAS_MAP = {
        "north": "go", "n": "go", "south": "go", "s": "go", "east": "go", "e": "go",
        "west": "go", "w": "go", "up": "go", "u": "go", "down": "go", "d": "go",
        "l": "look", "examine": "look",
        "inv": "inventory", "i": "inventory",
        "stats": "status", "score": "status",
        "journal": "quests", "q": "quests",
        "take": "get",
        "ask": "talk",
        "hit": "attack", "fight": "attack",
    }
    DIRECTION_NAMES = {
        "north": "north", "n": "north", "south": "south", "s": "south",
        "east": "east", "e": "east", "west": "west", "w": "west",
        "up": "up", "u": "up", "down": "down", "d": "down"
    }

    print(f"Action registry build complete. Total entries: {len(action_registry)}")
    return action_registry, ALIAS_MAP, DIRECTION_NAMES


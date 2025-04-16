# game_logic/game_manager.py
# Contains the main GameManager class responsible for handling game state and logic.
# Refactored: Removed ALL multi-statement lines using semicolons.
# Updated: Added tutorial state flags (Phase 1, Step 1).

import random
import traceback # Import traceback for error logging
from typing import Optional, Tuple, Dict, Any, Callable, Union, TYPE_CHECKING

# Use relative imports
from .models import Character, Location
from .content import PLAYER_START, LOCATIONS, QUESTS

# --- Imports for Action Handlers ---
HANDLERS_LOADED = False
try:
    from .actions.movement import handle_go
    from .actions.observation import handle_look, handle_inventory, handle_status, handle_quests
    from .actions.interaction import handle_get, handle_drop, handle_use, handle_talk
    from .actions.combat import handle_attack
    from .actions.skills import handle_skill_check
    from .actions.misc import handle_llm_only_action
    HANDLERS_LOADED = True
    print("Action handlers imported successfully.")
except ImportError as e:
    print(f"ERROR: Failed to import action handlers: {e}")
    # Define dummy functions if import fails
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
# --- End Action Handler Imports ---

# --- Type Aliases ---
ActionHandler = Callable[['GameManager', Optional[str]], Tuple[str, Optional[Dict[str, Any]]]]
RegistryValue = Union[ActionHandler, str]
# --- End Type Aliases ---

if TYPE_CHECKING:
    pass # Class defined below

class GameManager:
    """Manages game state and processes commands via action registry."""
    def __init__(self):
        """Initializes game state using string location IDs."""
        print("Initializing GameManager...")

        # --- Load Locations ---
        self.locations: dict[str, Location] = {}
        for loc_id, loc_data in LOCATIONS.items():
            if loc_id != loc_data.get('id'):
                 print(f"Warning: Loc ID mismatch for '{loc_id}'. Using key.")
                 loc_data['id'] = loc_id # Correct data
            try:
                self.locations[loc_id] = Location(**loc_data)
            except TypeError as e:
                print(f"Error creating Loc '{loc_id}': {e}\nData: {loc_data}")
        print(f"Loaded {len(self.locations)} locations.")

        # --- Load Character ---
        try:
            self.character = Character(**PLAYER_START)
            print(f"Character created: {self.character}")
        except TypeError as e:
            print(f"Error creating Character: {e}\nData: {PLAYER_START}")
            # Re-raise after logging
            raise ValueError("Failed init char.") from e

        # --- Set Initial Location ---
        self.current_location: Location | None = self.locations.get(self.character.current_location_id)
        if self.current_location is None:
            raise ValueError(f"Invalid start loc ID: '{self.character.current_location_id}'")
        else:
            print(f"Game started at: {self.current_location.name} (ID: '{self.current_location.id}')")

        # --- Tutorial State Flags (Phase 1, Step 1) ---
        self.tutorial_pickaxe_taken: bool = False
        self.tutorial_blockage_cleared: bool = False
        print("Tutorial flags initialized.")
        # --- End Tutorial State Flags ---

        # --- Action Registry ---
        self.action_registry: Dict[str, RegistryValue] = {}
        LLM_ONLY = "LLM_ONLY"
        if HANDLERS_LOADED:
            self.action_registry = {
                "go": handle_go, "north": handle_go, "n": handle_go, "south": handle_go, "s": handle_go, "east": handle_go, "e": handle_go, "west": handle_go, "w": handle_go, "up": handle_go, "u": handle_go, "down": handle_go, "d": handle_go,
                "look": handle_look, "l": handle_look, "examine": handle_look,
                "inv": handle_inventory, "inventory": handle_inventory, "i": handle_inventory,
                "status": handle_status, "stats": handle_status, "score": handle_status,
                "quests": handle_quests, "journal": handle_quests, "q": handle_quests,
                "get": handle_get, "take": handle_get, "drop": handle_drop, "use": handle_use, "talk": handle_talk, "ask": handle_talk,
                "attack": handle_attack, "hit": handle_attack, "fight": handle_attack,
                "check": handle_skill_check,
                "dance": LLM_ONLY, "sing": LLM_ONLY, "ponder": LLM_ONLY, "xyzzy": LLM_ONLY, "scream": LLM_ONLY, "laugh": LLM_ONLY, "cry": LLM_ONLY, "wave": LLM_ONLY, "sleep": LLM_ONLY,
            }
            print(f"Action registry populated with {len(self.action_registry)} commands/aliases.")
        else:
            print("ERROR: Action registry could not be populated.")
        print("GameManager initialized successfully.")

    # --- Command Parser (Simplified - Step R4.2) ---
    def parse_command(self, user_input: str) -> Optional[Tuple[str, Optional[str]]]:
        """Parses input into verb and argument string."""
        if not user_input:
            return None
        parts = user_input.lower().strip().split()
        if not parts:
            return None
        verb = parts[0]
        argument_string = " ".join(parts[1:]) if len(parts) > 1 else None
        return (verb, argument_string)

    # --- Quest Completion Check ---
    def check_quest_completion(self) -> Optional[str]:
        """Checks if any active quests are completed."""
        completed_quest_id = None
        quest_details = None
        for quest_id in self.character.active_quests[:]:
            quest_data = QUESTS.get(quest_id)
            if not quest_data:
                continue # Skip if quest data missing

            criteria = quest_data.get('completion_criteria', {})
            criteria_type = criteria.get('type')

            if criteria_type == 'has_item':
                item_name = criteria.get('item_name')
                if item_name and self.character.has_item(item_name):
                    completed_quest_id = quest_id
                    quest_details = quest_data
                    break # Complete one quest per turn
            elif criteria_type == 'reach_location':
                target_loc_id_str = criteria.get('location_id')
                if target_loc_id_str and self.character.current_location_id == target_loc_id_str:
                    completed_quest_id = quest_id
                    quest_details = quest_data
                    break # Complete one quest per turn
            # Add other criteria checks here

        if completed_quest_id and quest_details:
            print(f"Quest '{completed_quest_id}' completed!")
            self.character.remove_quest(completed_quest_id)
            xp_reward = quest_details.get('xp_reward', 0)
            leveled_up = self.character.add_xp(xp_reward)
            msg = f"Quest Completed: {quest_details.get('name', '?')}! (+{xp_reward} XP)"
            if leveled_up:
                # Append level up message on a new line
                msg += f"\n*** You reached Level {self.character.level}! ***"
            return msg
        return None

    # --- Main Processing Method (Refactored - Step R4.3) ---
    def process_turn(self, player_input: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Processes turn using action registry."""
        print(f"Processing turn for input: '{player_input}'")
        direct_message = ""
        llm_prompt_data = None
        quest_completion_message = None
        LLM_ONLY = "LLM_ONLY" # Marker defined in __init__

        parsed_command = self.parse_command(player_input)

        if parsed_command is None:
            direct_message = "Please enter a command."
        else:
            verb, argument_string = parsed_command
            DIRECTION_ALIASES = {"n":"north","north":"north","s":"south","south":"south","e":"east","east":"east","w":"west","west":"west","u":"up","up":"up","d":"down","down":"down"}

            # Handle direction aliases before registry lookup
            if verb in DIRECTION_ALIASES:
                 argument_string = DIRECTION_ALIASES[verb]
                 verb = "go" # Use canonical verb

            print(f"Processed command: Verb='{verb}', Argument='{argument_string}'")
            handler_or_marker = self.action_registry.get(verb)

            if handler_or_marker is None:
                # Command verb not found in the registry
                direct_message = f"Sorry, I don't know how to '{verb}'."
                llm_prompt_data = None
                print(f"Command '{verb}' not found in registry.")

            elif handler_or_marker == LLM_ONLY:
                # Command is marked for LLM-only handling
                print(f"Dispatching '{verb}' to LLM-only handler.")
                if HANDLERS_LOADED:
                    # Pass original verb and argument string
                    direct_message, llm_prompt_data = handle_llm_only_action(self, verb, argument_string)
                else:
                    # Ensure llm_prompt_data is None if handler not loaded
                    direct_message = "[Game Error: LLM-only handler not loaded]"
                    llm_prompt_data = None

            elif callable(handler_or_marker):
                # Command maps to a specific handler function
                handler_func = handler_or_marker
                print(f"Dispatching '{verb}' to handler: {handler_func.__name__}")
                try:
                    # Call the specific handler function from the actions package
                    direct_message, llm_prompt_data = handler_func(self, argument_string)
                except Exception as e:
                    # Catch errors within specific action handlers
                    print(f"ERROR executing handler {handler_func.__name__} for '{verb}': {e}")
                    traceback.print_exc() # Print full traceback for debugging
                    direct_message = "[Game Error: An internal error occurred performing that action.]"
                    llm_prompt_data = None
            else:
                # Invalid value in registry (should not happen if __init__ is correct)
                print(f"ERROR: Invalid value found in action registry for verb '{verb}': {handler_or_marker}")
                direct_message = "[Game Error: Internal configuration error for command.]"
                llm_prompt_data = None


        # --- Check for quest completion AFTER action is processed ---
        # Avoid checking if the command itself failed parsing or was unknown
        if parsed_command and parsed_command[0] not in ['error', 'unknown']:
             # Also skip check for purely informational commands
             # Updated list to match registry keys more closely
             if verb not in ['status', 'stats', 'score', 'quests', 'journal', 'q', 'look', 'l', 'examine', 'inventory', 'inv', 'i']:
                 quest_completion_message = self.check_quest_completion()

        # Append quest completion message if applicable
        if quest_completion_message:
             # Ensure separation from previous message
             if direct_message and not direct_message.endswith('\n'):
                 direct_message += "\n" # Add newline if needed
             elif not direct_message:
                 direct_message = "" # Ensure not None

             direct_message += f"\n{quest_completion_message}" # Append quest message

        return direct_message, llm_prompt_data

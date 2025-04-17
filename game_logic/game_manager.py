# game_logic/game_manager.py
# Contains the main GameManager class responsible for handling game state and logic.
# Refactored: Removed ALL multi-statement lines using semicolons.
# Updated: Added tutorial state flags (Phase 1, Step 1).
# Updated: Added Actions Discovered state variables (Phase 4, Step 4.1).
# Updated: Added calculation for total_actions (Phase 4, Step 4.2).
# Fixed: Corrected alias handling in process_turn to pass full direction name to handle_go.
# Updated: Modified process_turn return value to include discovery flag (Phase 5, Step 5.1).
# Updated: Modified process_turn return value AGAIN to include discovered verb (Phase 5.1 Revised).
# Updated: Added discovered_llm_actions state variable (Phase 8, Step 8.1).

import random
import traceback # Import traceback for error logging
from typing import Optional, Tuple, Dict, Any, Callable, Union, TYPE_CHECKING, Set

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

        # --- Actions Discovered State (Phase 4, Step 4.1) ---
        self.discovered_actions: Set[str] = set() # Stores canonical verbs used successfully
        self.total_actions: int = 0 # Will store total count of unique actions
        print("Actions Discovered state initialized.")
        # --- End Actions Discovered State ---

        # --- LLM Actions Discovered State (Phase 8, Step 8.1) ---
        self.discovered_llm_actions: Set[str] = set() # Stores LLM Only verbs used successfully
        print("LLM Actions Discovered state initialized.")
        # --- End LLM Actions Discovered State ---

        # --- Action Registry ---
        self.action_registry: Dict[str, RegistryValue] = {}
        LLM_ONLY = "LLM_ONLY" # Define marker here for use in total actions calculation
        if HANDLERS_LOADED:
            # Define canonical verbs first for clarity
            self.action_registry = {
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
                # LLM Only (These won't be counted in total_actions)
                "dance": LLM_ONLY, "sing": LLM_ONLY, "ponder": LLM_ONLY,
                "xyzzy": LLM_ONLY, "scream": LLM_ONLY, "laugh": LLM_ONLY,
                "cry": LLM_ONLY, "wave": LLM_ONLY, "sleep": LLM_ONLY,
            }
            # Add aliases, mapping them to the same handler functions
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
            self.action_registry.update(aliases)
            print(f"Action registry populated with {len(self.action_registry)} commands/aliases.")
        else:
            print("ERROR: Action registry could not be populated.")

        # --- Calculate Total Discoverable Actions (Phase 4, Step 4.2) ---
        unique_handlers = set()
        for handler_or_marker in self.action_registry.values():
            # Check if the value is a callable function (i.e., an action handler)
            if callable(handler_or_marker):
                unique_handlers.add(handler_or_marker)
            # We ignore non-callable values like the LLM_ONLY string marker
        self.total_actions = len(unique_handlers)
        print(f"Calculated total discoverable actions: {self.total_actions}")
        # --- End Total Actions Calculation ---

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
            msg = f"Quest Completed: {quest_details.get('name', '?')}! (+ {xp_reward} XP)" # Added space before XP
            if leveled_up:
                # Append level up message on a new line
                msg += f"\n*** You reached Level {self.character.level}! ***"
            return msg
        return None

    # --- Main Processing Method ---
    def process_turn(self, player_input: str) -> Tuple[str, Optional[Dict[str, Any]], bool, Optional[str]]:
        """
        Processes a player's turn using the action registry.

        Args:
            player_input: The raw input string from the player.

        Returns:
            A tuple containing:
            - direct_message (str): Text to display directly to the player.
            - llm_prompt_data (Optional[Dict[str, Any]]): Data for the LLM prompt, or None.
            - action_was_newly_discovered (bool): True if a canonical action was successfully
                                                  used for the first time this turn.
            - discovered_verb (Optional[str]): The canonical verb discovered, if any.
        """
        print(f"Processing turn for input: '{player_input}'")
        direct_message = ""
        llm_prompt_data = None
        quest_completion_message = None
        LLM_ONLY = "LLM_ONLY" # Marker defined in __init__
        canonical_verb = None # To store the canonical verb for discovery tracking
        action_was_newly_discovered = False # Flag for discovery
        discovered_verb_this_turn = None # Store the verb discovered in this turn
        llm_action_verb = None # Store the original verb if it's an LLM_ONLY action

        parsed_command = self.parse_command(player_input)

        if parsed_command is None:
            direct_message = "Please enter a command."
        else:
            verb, argument_string = parsed_command
            llm_action_verb = verb # Store original verb in case it's LLM_ONLY

            # --- Map aliases to canonical verbs ---
            CANONICAL_VERBS = {
                "go", "look", "inventory", "status", "quests",
                "get", "drop", "use", "talk", "attack", "check"
            }
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

            effective_verb = verb
            handler_argument = argument_string

            if verb in ALIAS_MAP:
                canonical_verb = ALIAS_MAP[verb]
                effective_verb = canonical_verb
                if canonical_verb == 'go':
                    full_direction = DIRECTION_NAMES.get(verb)
                    if full_direction:
                        handler_argument = full_direction
                    else:
                        handler_argument = verb
            elif verb in CANONICAL_VERBS:
                 canonical_verb = verb
                 effective_verb = verb

            print(f"Processed command: Verb='{verb}', Effective='{effective_verb}', Canonical='{canonical_verb}', HandlerArg='{handler_argument}'")

            handler_or_marker = self.action_registry.get(effective_verb)

            if handler_or_marker is None:
                direct_message = f"Sorry, I don't know how to '{verb}'."
                llm_prompt_data = None
                print(f"Command '{verb}' not found in registry.")

            elif handler_or_marker == LLM_ONLY:
                print(f"Dispatching '{verb}' to LLM-only handler.")
                if HANDLERS_LOADED:
                    direct_message, llm_prompt_data = handle_llm_only_action(self, verb, argument_string)
                    # --- LLM Action Discovery Check (Phase 8, Step 8.2) ---
                    # Check if the LLM action verb is new
                    # Ensure llm_action_verb is not None and the action didn't immediately error
                    if llm_action_verb and not direct_message.startswith("[Error"):
                         if llm_action_verb not in self.discovered_llm_actions:
                              self.discovered_llm_actions.add(llm_action_verb)
                              print(f"LLM Action Discovered: '{llm_action_verb}' added. Total: {len(self.discovered_llm_actions)}")
                    # --- End LLM Discovery Check ---
                else:
                    direct_message = "[Game Error: LLM-only handler not loaded]"
                    llm_prompt_data = None

            elif callable(handler_or_marker):
                handler_func = handler_or_marker
                print(f"Dispatching '{effective_verb}' to handler: {handler_func.__name__}")
                try:
                    direct_message, llm_prompt_data = handler_func(self, handler_argument)

                    # --- Action Discovery Check (Phase 4, Step 4.3) ---
                    if canonical_verb and not direct_message.startswith("[Error"):
                        if canonical_verb not in self.discovered_actions:
                            self.discovered_actions.add(canonical_verb)
                            action_was_newly_discovered = True # Set the flag here
                            discovered_verb_this_turn = canonical_verb # Store the verb
                            print(f"Action Discovered: '{canonical_verb}' added. Total: {len(self.discovered_actions)} / {self.total_actions}")
                    # --- End Discovery Check ---

                except Exception as e:
                    print(f"ERROR executing handler {handler_func.__name__} for '{effective_verb}': {e}")
                    traceback.print_exc()
                    direct_message = "[Game Error: An internal error occurred performing that action.]"
                    llm_prompt_data = None
            else:
                print(f"ERROR: Invalid value found in action registry for verb '{effective_verb}': {handler_or_marker}")
                direct_message = "[Game Error: Internal configuration error for command.]"
                llm_prompt_data = None


        # --- Check for quest completion AFTER action is processed ---
        if parsed_command and parsed_command[0] not in ['error', 'unknown']:
             if effective_verb not in ['status', 'inventory', 'quests', 'look']:
                 quest_completion_message = self.check_quest_completion()

        # Append quest completion message if applicable
        if quest_completion_message:
             if direct_message and not direct_message.endswith('\n'):
                 direct_message += "\n"
             elif not direct_message:
                 direct_message = ""
             direct_message += f"\n{quest_completion_message}"

        # --- Return updated tuple including the discovery flag and discovered verb ---
        return direct_message, llm_prompt_data, action_was_newly_discovered, discovered_verb_this_turn

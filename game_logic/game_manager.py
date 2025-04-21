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
# Updated: Added classic text adventure LLM_ONLY commands (User Request).
# Updated: Added 80s pop culture LLM_ONLY commands (User Request).
# Refactored: Moved LLM_ONLY command list to llm_commands.py and import it.
# Refactored: Removed inline action registry creation (Phase 13.1). Alias maps removed from process_turn.
# Refactored: Import and call build_action_registry in __init__ (Phase 13.2).
# Refactored: Calculate total_actions after registry build (Phase 13.3).
# Refactored: Moved parse_command method to parser.py (Phase 13.4).
# Refactored: Moved check_quest_completion method to quest_logic.py (Phase 13.5).
# Updated: Modified __init__ to accept loaded character and persistence state (P3.3).

import random
import traceback # Import traceback for error logging
from typing import Optional, Tuple, Dict, Any, Callable, Union, TYPE_CHECKING, Set

# Use relative imports
from .models import Character, Location
from .content import PLAYER_START, LOCATIONS # PLAYER_START might still be needed for fallback
from .parser import parse_command # Import the parser function (Phase 13.4)
from .quest_logic import check_quest_completion # Import quest checker (Phase 13.5)

# Action handlers are no longer directly needed here for registry setup
# They will be imported by action_registry_setup.py
# --- Imports for Action Handlers ---
# Keep imports if methods *other* than __init__ call handlers directly
try:
    from .actions.misc import handle_llm_only_action
except ImportError as e:
    print(f"ERROR: Failed to import specific action handlers needed by GameManager methods: {e}")
    def handle_llm_only_action(*args): return ("Attempting action...", {'action': 'narrative_action', 'command': 'unknown', 'argument': None, 'success': True, 'message': 'Trying something...'})

# --- Type Aliases ---
ActionHandler = Callable[['GameManager', Optional[str]], Tuple[str, Optional[Dict[str, Any]]]]
RegistryValue = Union[ActionHandler, str]
# --- End Type Aliases ---

if TYPE_CHECKING:
    pass # Class defined below

class GameManager:
    """Manages game state and processes commands via action registry."""
    # Class attribute to store maps after initialization
    ALIAS_MAP: Dict[str, str] = {}
    DIRECTION_NAMES: Dict[str, str] = {}

    # --- Updated __init__ Signature (P3.3) ---
    def __init__(self,
                 initial_character: Optional[Character] = None,
                 initial_discovered_actions: Optional[Set[str]] = None,
                 initial_discovered_llm_actions: Optional[Set[str]] = None,
                 initial_tutorial_pickaxe_taken: Optional[bool] = None,
                 initial_tutorial_blockage_cleared: Optional[bool] = None):
        """
        Initializes game state, accepting loaded character and persistence data.
        """
        print("Initializing GameManager...")

        # --- Load Locations (Remains the same) ---
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

        # --- Load Character (Updated P3.3) ---
        if initial_character is not None:
            self.character = initial_character
            print(f"Character loaded from initial_character: {self.character}")
        else:
            # Fallback or error? Raise error as initialize_game should provide it.
            print("ERROR: GameManager initialized without initial_character!")
            # Optionally load from PLAYER_START as a last resort, but indicates an issue.
            # self.character = Character(**PLAYER_START)
            # print(f"WARNING: Falling back to PLAYER_START for character.")
            raise ValueError("GameManager requires an initial_character to be provided.")

        # --- Set Initial Location (Updated P3.3) ---
        self.current_location: Location | None = self.locations.get(self.character.current_location_id)
        if self.current_location is None:
            print(f"ERROR: Loaded character's location ID '{self.character.current_location_id}' not found in locations.")
            # Fallback to PLAYER_START location ID if possible
            fallback_loc_id = PLAYER_START.get('current_location_id', 'entry_cave')
            self.current_location = self.locations.get(fallback_loc_id)
            if self.current_location:
                 print(f"WARNING: Falling back to location ID '{fallback_loc_id}'.")
                 self.character.current_location_id = fallback_loc_id # Correct character state
            else:
                 # This is a critical error - cannot find even the default start location
                 raise ValueError(f"Invalid start location ID '{self.character.current_location_id}' and fallback '{fallback_loc_id}' also not found.")
        else:
            print(f"Game started at: {self.current_location.name} (ID: '{self.current_location.id}')")


        # --- Tutorial State Flags (Updated P3.3) ---
        self.tutorial_pickaxe_taken: bool = initial_tutorial_pickaxe_taken if initial_tutorial_pickaxe_taken is not None else False
        self.tutorial_blockage_cleared: bool = initial_tutorial_blockage_cleared if initial_tutorial_blockage_cleared is not None else False
        print(f"Tutorial flags initialized (loaded): Pickaxe={self.tutorial_pickaxe_taken}, Blockage={self.tutorial_blockage_cleared}")

        # --- Actions Discovered State (Updated P3.3) ---
        self.discovered_actions: Set[str] = initial_discovered_actions if initial_discovered_actions is not None else set()
        self.total_actions: int = 0 # Initialize before calculation
        print(f"Actions Discovered state initialized (loaded): Count={len(self.discovered_actions)}")

        # --- LLM Actions Discovered State (Updated P3.3) ---
        self.discovered_llm_actions: Set[str] = initial_discovered_llm_actions if initial_discovered_llm_actions is not None else set()
        print(f"LLM Actions Discovered state initialized (loaded): Count={len(self.discovered_llm_actions)}")

        # --- Build Action Registry (Remains the same) ---
        try:
            # Import and call the external builder function
            from .action_registry_setup import build_action_registry
            self.action_registry, GameManager.ALIAS_MAP, GameManager.DIRECTION_NAMES = build_action_registry()
            print("Action registry built successfully.")
            if not self.action_registry:
                 print("WARNING: Action registry is empty. Check handler imports in action_registry_setup.py.")
        except ImportError as e:
            print(f"ERROR: Failed to import or call build_action_registry: {e}")
            traceback.print_exc()
            self.action_registry = {}
            GameManager.ALIAS_MAP = {}
            GameManager.DIRECTION_NAMES = {}
        # --- End Registry Build ---

        # --- Calculate Total Discoverable Actions (Remains the same) ---
        unique_handlers = set()
        for handler_or_marker in self.action_registry.values():
            if callable(handler_or_marker):
                unique_handlers.add(handler_or_marker)
        self.total_actions = len(unique_handlers)
        print(f"Calculated total discoverable canonical actions: {self.total_actions}")
        # --- End Total Actions Calculation ---

        print("GameManager initialization complete.") # Final message

    # --- Command Parser Method Removed (Phase 13.4) ---

    # --- Quest Completion Check Method Removed (Phase 13.5) ---
    # Logic moved to game_logic/quest_logic.py

    # --- Main Processing Method (Remains the same) ---
    def process_turn(self, player_input: str) -> Tuple[str, Optional[Dict[str, Any]], bool, Optional[str]]:
        """Processes a player's turn using the action registry."""
        print(f"Processing turn for input: '{player_input}'")
        direct_message = ""
        llm_prompt_data = None
        quest_completion_message = None
        LLM_ONLY = "LLM_ONLY" # Marker string (ensure consistent casing)
        canonical_verb = None
        action_was_newly_discovered = False
        discovered_verb_this_turn = None
        llm_action_verb = None

        # Use the imported parser function (Phase 13.4)
        parsed_command = parse_command(player_input)

        if parsed_command is None:
            direct_message = "Please enter a command."
        else:
            verb, argument_string = parsed_command
            llm_action_verb = verb # Store original verb

            # --- Alias Mapping ---
            effective_verb = verb
            handler_argument = argument_string

            if verb in GameManager.ALIAS_MAP: # Use class attribute ALIAS_MAP
                canonical_verb = GameManager.ALIAS_MAP[verb]
                effective_verb = canonical_verb
                if canonical_verb == 'go':
                    full_direction = GameManager.DIRECTION_NAMES.get(verb)
                    handler_argument = full_direction if full_direction else verb
            # Determine canonical verb if no alias was used
            temp_handler = self.action_registry.get(effective_verb)
            if callable(temp_handler):
                 if canonical_verb is None:
                      canonical_verb = effective_verb

            print(f"Processed command: Verb='{verb}', Effective='{effective_verb}', Canonical='{canonical_verb}', HandlerArg='{handler_argument}'")

            # Use the effective_verb for registry lookup first
            handler_or_marker = self.action_registry.get(effective_verb)

            # If not found, try original verb (for LLM_ONLY commands not in ALIAS_MAP)
            if handler_or_marker is None and effective_verb != verb:
                 handler_or_marker = self.action_registry.get(verb)
                 if handler_or_marker:
                      effective_verb = verb

            # --- Dispatch Logic ---
            if handler_or_marker is None:
                direct_message = f"Sorry, I don't know how to '{verb}'."
                llm_prompt_data = None
                print(f"Command '{verb}' not found in registry.")

            elif handler_or_marker == LLM_ONLY:
                print(f"Dispatching '{llm_action_verb}' to LLM-only handler.")
                try:
                    direct_message, llm_prompt_data = handle_llm_only_action(self, llm_action_verb, argument_string)
                    # --- LLM Action Discovery Check ---
                    if llm_action_verb and not direct_message.startswith("[Error"):
                         if llm_action_verb not in self.discovered_llm_actions:
                              self.discovered_llm_actions.add(llm_action_verb)
                              print(f"LLM Action Discovered: '{llm_action_verb}' added. Total: {len(self.discovered_llm_actions)}")
                    # --- End LLM Discovery Check ---
                except NameError:
                     direct_message = "[Game Error: LLM-only handler not loaded]"
                     llm_prompt_data = None

            elif callable(handler_or_marker):
                handler_func = handler_or_marker
                print(f"Dispatching '{effective_verb}' to handler: {handler_func.__name__}")
                try:
                    direct_message, llm_prompt_data = handler_func(self, handler_argument)

                    # --- Action Discovery Check ---
                    if canonical_verb and not direct_message.startswith("[Error"):
                        if canonical_verb not in self.discovered_actions:
                            self.discovered_actions.add(canonical_verb)
                            action_was_newly_discovered = True
                            discovered_verb_this_turn = canonical_verb
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


        # --- Check for quest completion ---
        if parsed_command and parsed_command[0] not in ['error', 'unknown']:
             check_verb = effective_verb if canonical_verb is None else canonical_verb
             # Use imported quest checker function (Phase 13.5)
             if check_verb not in ['status', 'inventory', 'quests', 'look']:
                 quest_completion_message = check_quest_completion(self.character) # Pass character object

        # Append quest completion message
        if quest_completion_message:
             if direct_message and not direct_message.endswith('\n'): direct_message += "\n"
             elif not direct_message: direct_message = ""
             direct_message += f"\n{quest_completion_message}"

        # Return updated tuple
        return direct_message, llm_prompt_data, action_was_newly_discovered, discovered_verb_this_turn


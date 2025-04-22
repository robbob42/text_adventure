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
# Updated: Added apply_modifications method (Location Persistence Plan L2.2).
# Fixed: Added missing 'import json' (User Report).
# Updated: Implemented record_location_modification method (Location Persistence Plan L3.1).

import random
import traceback # Import traceback for error logging
import json
from typing import Optional, Tuple, Dict, Any, Callable, Union, TYPE_CHECKING, Set, List # Added List

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

# --- Imports for Database Interaction (L3.1) ---
try:
    from database.db_setup import get_db_connection
    from database.crud import save_location_modification
except ImportError as e:
    print(f"ERROR importing DB components in game_manager.py: {e}")
    def get_db_connection(): return None
    def save_location_modification(*args): return False
    # Consider raising error if DB interaction is critical
# --- End DB Imports ---


# --- Type Aliases ---
ActionHandler = Callable[['GameManager', Optional[str]], Tuple[str, Optional[Dict[str, Any]]]]
RegistryValue = Union[ActionHandler, str]
ModListType = List[Tuple[str, str, str]] # Type hint for modifications list
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
                # Create Location objects from static data
                self.locations[loc_id] = Location(**loc_data)
            except TypeError as e:
                print(f"Error creating Loc '{loc_id}': {e}\nData: {loc_data}")
        print(f"Loaded {len(self.locations)} base locations from content.")

        # --- Load Character (Updated P3.3) ---
        if initial_character is not None:
            self.character = initial_character
            print(f"Character loaded from initial_character: {self.character.name}")
        else:
            print("ERROR: GameManager initialized without initial_character!")
            raise ValueError("GameManager requires an initial_character to be provided.")

        # --- Set Initial Location (Updated P3.3) ---
        self.current_location: Location | None = self.locations.get(self.character.current_location_id)
        if self.current_location is None:
            print(f"ERROR: Loaded character's location ID '{self.character.current_location_id}' not found in locations.")
            fallback_loc_id = PLAYER_START.get('current_location_id', 'entry_cave')
            self.current_location = self.locations.get(fallback_loc_id)
            if self.current_location:
                 print(f"WARNING: Falling back to location ID '{fallback_loc_id}'.")
                 self.character.current_location_id = fallback_loc_id # Correct character state
            else:
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
            from .action_registry_setup import build_action_registry
            self.action_registry, GameManager.ALIAS_MAP, GameManager.DIRECTION_NAMES = build_action_registry()
            print("Action registry built successfully.")
            if not self.action_registry: print("WARNING: Action registry is empty.")
        except ImportError as e:
            print(f"ERROR: Failed to import or call build_action_registry: {e}"); traceback.print_exc()
            self.action_registry = {}; GameManager.ALIAS_MAP = {}; GameManager.DIRECTION_NAMES = {}
        # --- End Registry Build ---

        # --- Calculate Total Discoverable Actions (Remains the same) ---
        unique_handlers = set(h for h in self.action_registry.values() if callable(h))
        self.total_actions = len(unique_handlers)
        print(f"Calculated total discoverable canonical actions: {self.total_actions}")
        # --- End Total Actions Calculation ---

        print("GameManager initialization complete.") # Final message

    # --- Apply Modifications Method (Added L2.2) ---
    def apply_modifications(self, modifications: 'ModListType'):
        """
        Applies a list of loaded location modifications to the in-memory location objects.

        Args:
            modifications: A list of tuples, where each tuple is
                           (location_id, mod_type, mod_data).
        """
        if not modifications:
            print("No location modifications to apply.")
            return

        print(f"Applying {len(modifications)} location modifications...")
        applied_count = 0
        for loc_id, mod_type, mod_data in modifications:
            location = self.locations.get(loc_id)
            if not location:
                print(f"Warning: Cannot apply modification - Location ID '{loc_id}' not found.")
                continue

            print(f"  Applying Mod: Loc='{loc_id}', Type='{mod_type}', Data='{mod_data[:50]}...'")
            try:
                if mod_type == 'CHANGE_DESC':
                    location.description = mod_data # Directly replace description
                    print(f"    -> Changed description for '{loc_id}'.")
                    applied_count += 1
                elif mod_type == 'REMOVE_ITEM':
                    item_name = mod_data
                    removed = location.remove_item(item_name)
                    if removed: print(f"    -> Removed item '{item_name}' from '{loc_id}'."); applied_count += 1
                    else: print(f"    -> Warning: Item '{item_name}' not found to remove from '{loc_id}' during mod application.")
                elif mod_type == 'ADD_ITEM':
                    try:
                        item_dict = json.loads(mod_data)
                        if isinstance(item_dict, dict) and 'name' in item_dict:
                            location.add_item(item_dict); print(f"    -> Added item '{item_dict['name']}' to '{loc_id}'."); applied_count += 1
                        else: print(f"    -> Error: Invalid item dictionary format in mod_data for ADD_ITEM: {mod_data}")
                    except json.JSONDecodeError: print(f"    -> Error: Failed to parse JSON mod_data for ADD_ITEM: {mod_data}")
                elif mod_type == 'UNBLOCK_EXIT': print(f"    -> Mod Type '{mod_type}' not fully implemented yet.")
                elif mod_type == 'BLOCK_EXIT': print(f"    -> Mod Type '{mod_type}' not fully implemented yet.")
                elif mod_type == 'REMOVE_NPC': print(f"    -> Mod Type '{mod_type}' not fully implemented yet.")
                elif mod_type == 'ADD_NPC': print(f"    -> Mod Type '{mod_type}' not fully implemented yet.")
                else: print(f"    -> Warning: Unknown modification type '{mod_type}' encountered.")
            except Exception as apply_err:
                print(f"    -> ERROR applying modification ({loc_id}, {mod_type}): {apply_err}"); traceback.print_exc()
        print(f"Finished applying modifications. Successfully applied: {applied_count}/{len(modifications)}")
    # --- End Apply Modifications Method ---


    # --- Record Modification Method (Implemented L3.1) ---
    def record_location_modification(self, location_id: str, mod_type: str, mod_data: str):
        """
        Saves a single location modification to the database via crud function.
        Uses character_id = 1 for now.
        """
        print(f"Attempting to record location modification: Loc='{location_id}', Type='{mod_type}', Data='{mod_data[:50]}...'")
        db_conn = None
        success = False
        # Assuming character_id is always 1 for the single-player MVP
        # If Character model gets an ID attribute later, use self.character.id
        character_id_to_save = 1

        try:
            db_conn = get_db_connection()
            if db_conn:
                success = save_location_modification(
                    conn=db_conn,
                    character_id=character_id_to_save,
                    location_id=location_id,
                    mod_type=mod_type,
                    mod_data=mod_data
                )
                if success:
                    print("Modification recorded successfully in DB.")
                else:
                    print("Modification record failed (crud function returned False).")
            else:
                print("ERROR: Could not get DB connection to record modification.")
        except Exception as e:
            print(f"ERROR during record_location_modification: {e}")
            traceback.print_exc()
        finally:
            if db_conn:
                db_conn.close()
                # print("DB connection closed after recording modification.") # Reduced verbosity
    # --- End Record Modification Method ---


    # --- Command Parser Method Removed (Phase 13.4) ---

    # --- Quest Completion Check Method Removed (Phase 13.5) ---

    # --- Main Processing Method (Remains the same) ---
    def process_turn(self, player_input: str) -> Tuple[str, Optional[Dict[str, Any]], bool, Optional[str]]:
        """Processes a player's turn using the action registry."""
        # print(f"Processing turn for input: '{player_input}'") # Reduced verbosity
        direct_message = ""
        llm_prompt_data = None
        quest_completion_message = None
        LLM_ONLY = "LLM_ONLY"
        canonical_verb = None
        action_was_newly_discovered = False
        discovered_verb_this_turn = None
        llm_action_verb = None

        parsed_command = parse_command(player_input)

        if parsed_command is None:
            direct_message = "Please enter a command."
        else:
            verb, argument_string = parsed_command
            llm_action_verb = verb
            effective_verb = verb
            handler_argument = argument_string

            if verb in GameManager.ALIAS_MAP:
                canonical_verb = GameManager.ALIAS_MAP[verb]
                effective_verb = canonical_verb
                if canonical_verb == 'go':
                    full_direction = GameManager.DIRECTION_NAMES.get(verb)
                    handler_argument = full_direction if full_direction else verb
            temp_handler = self.action_registry.get(effective_verb)
            if callable(temp_handler):
                 if canonical_verb is None: canonical_verb = effective_verb

            # print(f"Processed command: Verb='{verb}', Effective='{effective_verb}', Canonical='{canonical_verb}', HandlerArg='{handler_argument}'") # Reduced verbosity

            handler_or_marker = self.action_registry.get(effective_verb)
            if handler_or_marker is None and effective_verb != verb:
                 handler_or_marker = self.action_registry.get(verb)
                 if handler_or_marker: effective_verb = verb

            if handler_or_marker is None:
                direct_message = f"Sorry, I don't know how to '{verb}'."
                llm_prompt_data = None
                # print(f"Command '{verb}' not found in registry.") # Reduced verbosity

            elif handler_or_marker == LLM_ONLY:
                # print(f"Dispatching '{llm_action_verb}' to LLM-only handler.") # Reduced verbosity
                try:
                    direct_message, llm_prompt_data = handle_llm_only_action(self, llm_action_verb, argument_string)
                    if llm_action_verb and not direct_message.startswith("[Error"):
                         if llm_action_verb not in self.discovered_llm_actions:
                              self.discovered_llm_actions.add(llm_action_verb)
                              print(f"LLM Action Discovered: '{llm_action_verb}' added. Total: {len(self.discovered_llm_actions)}")
                except NameError: direct_message = "[Game Error: LLM-only handler not loaded]"; llm_prompt_data = None

            elif callable(handler_or_marker):
                handler_func = handler_or_marker
                # print(f"Dispatching '{effective_verb}' to handler: {handler_func.__name__}") # Reduced verbosity
                try:
                    direct_message, llm_prompt_data = handler_func(self, handler_argument)
                    if canonical_verb and not direct_message.startswith("[Error"):
                        if canonical_verb not in self.discovered_actions:
                            self.discovered_actions.add(canonical_verb)
                            action_was_newly_discovered = True
                            discovered_verb_this_turn = canonical_verb
                            print(f"Action Discovered: '{canonical_verb}' added. Total: {len(self.discovered_actions)} / {self.total_actions}")
                except Exception as e:
                    print(f"ERROR executing handler {handler_func.__name__} for '{effective_verb}': {e}"); traceback.print_exc()
                    direct_message = "[Game Error: An internal error occurred performing that action.]"; llm_prompt_data = None
            else:
                print(f"ERROR: Invalid value found in action registry for verb '{effective_verb}': {handler_or_marker}")
                direct_message = "[Game Error: Internal configuration error for command.]"; llm_prompt_data = None

        if parsed_command and parsed_command[0] not in ['error', 'unknown']:
             check_verb = effective_verb if canonical_verb is None else canonical_verb
             if check_verb not in ['status', 'inventory', 'quests', 'look']:
                 quest_completion_message = check_quest_completion(self.character)

        if quest_completion_message:
             if direct_message and not direct_message.endswith('\n'): direct_message += "\n"
             elif not direct_message: direct_message = ""
             direct_message += f"\n{quest_completion_message}"

        return direct_message, llm_prompt_data, action_was_newly_discovered, discovered_verb_this_turn


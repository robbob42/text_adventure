# game_logic/parser.py
# Contains functions related to parsing player input.
# Created in Refactoring Phase 13.4

from typing import Optional, Tuple

def parse_command(user_input: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Parses raw user input into a verb and an optional argument string.

    Handles basic splitting and lowercasing. Specific command logic (like
    treating 'open sesame' as 'sesame') is currently handled within this parser.

    Args:
        user_input: The raw string typed by the player.

    Returns:
        A tuple containing (verb, argument_string) if input is valid,
        otherwise None. Argument_string is None if no arguments were given.
    """
    if not user_input:
        return None

    # Convert to lowercase and remove leading/trailing whitespace
    cleaned_input = user_input.lower().strip()
    if not cleaned_input:
        return None

    # Split into potential verb and the rest of the string
    parts = cleaned_input.split(None, 1) # Split only on the first whitespace
    verb = parts[0]
    argument_string = parts[1] if len(parts) > 1 else None

    # --- Special command parsing adjustments ---
    # Handle specific multi-word commands that should map to a different verb
    # or where the argument needs preservation despite the first word being the key.
    # Example: Treat 'open sesame' as the verb 'sesame' with no arguments.
    if verb == "open" and argument_string == "sesame":
        verb = "sesame"
        argument_string = None
    # Example: Keep 'hello sailor' arguments separate for LLM context,
    # even though 'hello' is the trigger verb in the registry.
    elif verb == "hello" and argument_string == "sailor":
        pass # Keep verb='hello', argument_string='sailor'
    # Example: Keep 'flux capacitor' arguments separate for LLM context.
    elif verb == "flux" and argument_string == "capacitor":
        pass # Keep verb='flux', argument_string='capacitor'
    # --- End special adjustments ---

    return (verb, argument_string)


# game_logic/llm_interface.py
# Handles setting up and interacting with the LangChain components for the LLM.
# Updated for Phase 12: Added level, xp, and active quests to prompt context.

import sys
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import Dict, Any, Optional

# --- Load API Key & Content ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from config import GOOGLE_API_KEY
    # Use relative import for content within game_logic package
    from .content import SYSTEM_PROMPT
    # sys.path.pop(0) # Clean up path only if needed
except ImportError as e:
    print(f"ERROR: Could not import from config.py or game_logic/content.py: {e}")
    GOOGLE_API_KEY = None
    SYSTEM_PROMPT = "SYSTEM PROMPT FAILED TO LOAD. You are a helpful assistant."
except Exception as e:
    print(f"ERROR: An unexpected error occurred during import: {e}")
    GOOGLE_API_KEY = None
    SYSTEM_PROMPT = "SYSTEM PROMPT FAILED TO LOAD. You are a helpful assistant."

# --- Basic Validation ---
if not GOOGLE_API_KEY:
    print("CRITICAL ERROR: GOOGLE_API_KEY is not set. LLM functionality will be disabled.")

# --- Initialize LLM ---
llm: Optional[ChatGoogleGenerativeAI] = None
if GOOGLE_API_KEY:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7,
        )
        print("Google Gemini LLM client initialized successfully.")
    except Exception as e:
        print(f"ERROR: Failed to initialize Google Gemini LLM: {e}")
        llm = None
else:
    print("LLM client cannot be initialized because GOOGLE_API_KEY is missing.")

# --- Initialize Memory ---
memory = ConversationBufferWindowMemory(
    k=4,
    memory_key="chat_history",
    input_key="player_input",
    return_messages=True
)
print(f"Conversation memory initialized (type: {type(memory).__name__}, k={memory.k}).")


# --- Define Prompt Template String (Updated for Step 12.5) ---
template_string = """
{system_prompt}

--- Current State ---
Location: {location_name} (ID: {location_id})
Character: {char_name} (Level: {level} XP: {xp} | HP: {char_hp}/{max_hp}) # <-- Added Level/XP
Inventory: {inventory_list_str}
Skills: {skills_dict_str}
Active Quests: {active_quests_str} # <-- Added Active Quests
Location Description: {location_description}

--- Last Action Outcome (if any) ---
{action_outcome}

--- Conversation History ---
{chat_history}

--- Player Input ---
Player: {player_input}

--- Response ---
DM:"""

# --- Define Input Variables for the Template (Updated for Step 12.5) ---
input_variables = [
    "system_prompt",
    "location_name",
    "location_id",
    "char_name",
    "char_hp",
    "max_hp",
    "level", # <-- Added level
    "xp",    # <-- Added xp
    "inventory_list_str",
    "skills_dict_str",
    "active_quests_str", # <-- Added active quests string
    "location_description",
    "action_outcome",
    "chat_history",
    "player_input"
]

# --- Create Prompt Template Object ---
llm_prompt_template: Optional[PromptTemplate] = None
if SYSTEM_PROMPT:
    try:
        llm_prompt_template = PromptTemplate(
            template=template_string,
            input_variables=input_variables
        )
        print("PromptTemplate created successfully.")
    except Exception as e:
        print(f"Error creating PromptTemplate: {e}")
        llm_prompt_template = None
else:
     print("PromptTemplate not created because SYSTEM_PROMPT failed to load.")


# --- Create LLM Chain ---
llm_chain: Optional[LLMChain] = None
if llm and llm_prompt_template:
    try:
        llm_chain = LLMChain(
            llm=llm,
            prompt=llm_prompt_template,
            memory=memory,
            verbose=True
        )
        print("LLMChain created successfully.")
    except Exception as e:
        print(f"Error creating LLMChain: {e}")
        llm_chain = None
else:
    print("LLMChain not created because LLM or PromptTemplate is missing/invalid.")


# --- Function to Get Narration (Updated Docstring for Step 12.5) ---
def get_llm_narration(game_state: Dict[str, Any]) -> str:
    """
    Gets narrative text from the LLM based on the current game state.

    Args:
        game_state: A dictionary containing all the necessary input variables
                    for the prompt template (excluding 'chat_history', but
                    including 'player_input' and all custom state variables like
                    'system_prompt', 'char_hp', 'level', 'xp', 'inventory_list_str',
                    'skills_dict_str', 'active_quests_str', etc.).

    Returns:
        The narrative string response from the LLM, or an error message string.
    """
    print(f"Attempting to call LLM with game state keys: {list(game_state.keys())}")

    if not llm_chain:
        print("ERROR: llm_chain is not available for get_llm_narration.")
        return "[LLM Narration Error - LLM Chain not initialized]"

    # Check for required keys (now includes level, xp, active_quests_str)
    # Memory handles chat_history and player_input implicitly via invoke keys
    required_keys = [k for k in input_variables if k not in memory.memory_variables]
    missing_keys = [key for key in required_keys if key not in game_state]

    # Provide defaults for potentially missing non-critical keys before failing
    if missing_keys:
         print(f"Warning: Missing keys in game_state for LLM prompt: {missing_keys}")
         if 'inventory_list_str' not in game_state: game_state['inventory_list_str'] = "Unknown"
         if 'skills_dict_str' not in game_state: game_state['skills_dict_str'] = "Unknown"
         if 'active_quests_str' not in game_state: game_state['active_quests_str'] = "None"
         if 'action_outcome' not in game_state: game_state['action_outcome'] = ""
         if 'level' not in game_state: game_state['level'] = "?" # Indicate missing required info
         if 'xp' not in game_state: game_state['xp'] = "?"

         # Re-check after adding defaults
         missing_keys = [key for key in required_keys if key not in game_state]
         if missing_keys:
              print(f"ERROR: Still missing critical keys after defaults: {missing_keys}")
              return f"[LLM Narration Error - Missing critical state variables: {missing_keys}]"

    try:
        # Ensure system prompt is included if not already in game_state
        if 'system_prompt' not in game_state:
            game_state['system_prompt'] = SYSTEM_PROMPT or "Default System Prompt"

        # Invoke the chain
        response = llm_chain.invoke(game_state)
        result_text = response.get('text', None)

        if result_text is None:
             print(f"ERROR: LLM response dictionary did not contain 'text' key. Response: {response}")
             return "[LLM Narration Error - Unexpected response format]"

        print(f"LLM Raw Response: {result_text}")
        return result_text.strip()

    except Exception as e:
        print(f"ERROR: Exception during LLM chain invocation: {e}")
        import traceback
        traceback.print_exc()
        return "[Error communicating with the LLM DM. Please try again.]"


# --- Optional: Basic test block ---
if __name__ == '__main__':
    print("\n--- LLM Interface Test (Phase 12 Update) ---")
    # ... (Initialization checks remain the same) ...

    if llm_chain:
        print("LLM Chain Object:", llm_chain)
        print("\n--- Test get_llm_narration with Quests/XP/Level ---")
        test_state = {
                "system_prompt": SYSTEM_PROMPT or "Default System Prompt",
                "location_name": "Test Location", "location_id": 0,
                "char_name": "Tester", "char_hp": 10, "max_hp": 10,
                "level": 1, # Added
                "xp": 25,   # Added
                "inventory_list_str": "torch, rusty dagger",
                "skills_dict_str": "{'perception': 1, 'strength': 0}",
                "active_quests_str": "- Retrieve the Tool: Find the pickaxe.", # Added
                "location_description": "A test room. Now includes quest context.",
                "action_outcome": "You just tested the updated interface again.",
                "player_input": "Check prompt context again"
        }
        print(f"Calling get_llm_narration with state: {test_state}")
        narration = get_llm_narration(test_state)
        print(f"\nReturned Narration:\n{narration}")
    else:
        print("LLM Chain object is None. Cannot test get_llm_narration.")

    print("------------------------")

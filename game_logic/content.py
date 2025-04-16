# game_logic/content.py
# Defines the static content for the MVP game.
# Updated for Phase C3.2: Added new quest definitions and updated starting quests.
# Updated for Phase 3, Step 1: Modified entry_cave description for tutorial clarity.
# Updated: Changed emphasis from Markdown (**) to HTML (<b>) tags in entry_cave description.
# Uses STRING IDs for locations.

# --- Player Character ---
PLAYER_START = {
    'name': 'Hero',
    'hp': 20,
    'max_hp': 20,
    'current_location_id': 'entry_cave', # String ID
    'inventory': [],
    'skills': {'perception': 1},
    # --- Updated active_quests (Step C3.2) ---
    'active_quests': [
        'get_pickaxe',
        'find_button',
        'get_chieftains_key',
        'scout_trash_pit'
        ]
    # --- End update ---
}

# --- Locations ---
# Using descriptive strings as keys and for internal 'id' field.
LOCATIONS = {
    'entry_cave': {
        'id': 'entry_cave', 'name': 'Cave Entrance',
        # --- Updated Description (Phase 3, Step 1 - HTML Emphasis) ---
        'description': 'You stand just inside the mouth of a dark, damp cave. Water drips steadily from the ceiling. The air smells earthy and cold. A narrow passage leading east is blocked by a pile of <b>rubble</b>. A rusty <b>pickaxe</b> lies discarded in a corner near the entrance.',
        # --- End Update ---
        'exits': {'east': 'narrow_corridor'}, # Exit still defined, but blocked by logic in handle_go initially
        'npcs': [],
        'items': [ { 'name': 'pickaxe', 'description': 'a rusty pickaxe leaning against the wall', 'gettable': True },
                   { 'name': 'rubble', 'description': 'a pile of rubble blocking the east passage', 'gettable': False } # Added rubble as non-gettable item for 'look rubble'
                 ]
    },
    'narrow_corridor': {
        'id': 'narrow_corridor', 'name': 'Narrow Corridor',
        'description': 'The passage is tight, forcing you to squeeze through. The rough stone walls are slick with moisture. You can hear faint scratching sounds coming from the east. The cave entrance is back to the west.',
        'exits': {'east': 'goblin_chamber', 'west': 'entry_cave'}, 'npcs': [], 'items': []
    },
    'goblin_chamber': {
        'id': 'goblin_chamber', 'name': 'Small Chamber',
        'description': 'This small chamber opens up slightly. Filthy rags form a makeshift bed in one corner. A single, mean-looking goblin glares at you, wielding a crude spear! The only way out seems to be back west. A rough opening leads further east.',
        'exits': {'west': 'narrow_corridor', 'east': 'guard_room'},
        'npcs': [ { 'name': 'goblin', 'description': 'a mean-looking goblin', 'dialogue': '"Get out! This my cave!"' } ],
        'items': [ { 'name': 'rags', 'description': 'filthy rags', 'gettable': False }, { 'name': 'bone', 'description': 'a discarded bone', 'gettable': False } ]
    },
    'guard_room': {
        'id': 'guard_room', 'name': 'Guard Room',
        'description': 'This rough-hewn chamber was clearly used as a guard post. A crude wooden table sits overturned against one wall, and the floor is littered with gnawed bones. Passages lead north, south, and east. The way back west leads to the first goblin chamber.',
        'exits': {'north': 'sleeping_quarters', 'south': 'mess_hall', 'east': 'trash_pit', 'west': 'goblin_chamber'},
        'npcs': [ { 'name': 'sleepy goblin', 'description': 'a goblin guard dozing lightly by the north passage', 'dialogue': "\"Zzz... huh? Wha? Go 'way...\""} ],
        'items': [ { 'name': 'club', 'description': 'a crude wooden club lying near the overturned table', 'gettable': True }, { 'name': 'helmet', 'description': 'a dented goblin helmet on the floor', 'gettable': True } ]
    },
    'mess_hall': {
        'id': 'mess_hall', 'name': 'Mess Hall',
        'description': 'The smell of stale food and unwashed goblin hangs heavy in the air. Greasy, makeshift tables and benches are scattered haphazardly. A large, unpleasant cooking pot sits cold in a hearth.',
        'exits': {'north': 'guard_room'},
        'npcs': [ { 'name': 'cook', 'description': 'a fat goblin stirring the empty cooking pot', 'dialogue': '"No food for you! Only for goblins!"'} ],
        'items': [ { 'name': 'dirty plate', 'description': 'a greasy wooden plate with scraps', 'gettable': False }, { 'name': 'ladle', 'description': 'a bent ladle resting against the pot', 'gettable': True } ]
    },
    'trash_pit': {
        'id': 'trash_pit', 'name': 'Trash Pit',
        'description': 'This area serves as a dumping ground. Piles of refuse, broken pottery, and more bones are scattered around a dark, foul-smelling pit in the center. It looks hazardous. A passage leads back west.',
        'exits': {'west': 'guard_room'}, 'npcs': [],
        'items': [ { 'name': 'broken bottle', 'description': 'shards of a broken bottle', 'gettable': False }, { 'name': 'shiny button', 'description': 'a small, shiny button half-buried in the muck', 'gettable': True} ]
    },
    'sleeping_quarters': {
        'id': 'sleeping_quarters', 'name': 'Sleeping Quarters',
        'description': 'Several disgusting piles of furs and dirty straw serve as communal beds. The air is thick with the stench of sleeping goblins (though none are here now). An exit leads south, and another passage continues east.',
        'exits': {'south': 'guard_room', 'east': 'chieftains_room'}, 'npcs': [],
        'items': [ { 'name': 'straw pile', 'description': 'a pile of dirty straw', 'gettable': False }, { 'name': 'torn pouch', 'description': 'a small, torn pouch tucked under some straw', 'gettable': True } ]
    },
    'chieftains_room': {
        'id': 'chieftains_room', 'name': "Chieftain's Room",
        'description': "This chamber is slightly larger and marginally cleaner than the others. A large, crude throne made of wood and skulls sits against the far wall. A thick, flea-ridden fur pelt lies on the floor. The only exit is back to the west.",
        'exits': {'west': 'sleeping_quarters'},
        'npcs': [ { 'name': 'chieftain', 'description': 'a particularly large and ugly goblin wearing a necklace of teeth, sitting on the throne', 'dialogue': '"WHO DARES ENTER MY CHAMBER?!"'} ],
        'items': [ { 'name': 'throne', 'description': 'a crude throne of wood and skulls', 'gettable': False }, { 'name': 'fur pelt', 'description': 'a thick, flea-ridden fur pelt', 'gettable': False }, { 'name': 'iron key', 'description': 'a heavy iron key hanging on a hook behind the throne', 'gettable': True } ]
    },
}

# --- Quests (Updated Step C3.2) ---
QUESTS = {
    'get_pickaxe': {
        'id': 'get_pickaxe', 'name': 'Retrieve the Tool',
        'description': 'Find and retrieve the rusty pickaxe near the cave entrance.',
        'completion_criteria': {'type': 'has_item', 'item_name': 'pickaxe'},
        'xp_reward': 25
    },
    # --- Added Quests ---
    'find_button': {
        'id': 'find_button', 'name': "A Glimmer in the Filth",
        'description': "Something shiny was lost in the trash pit. Maybe it's valuable?",
        'completion_criteria': {'type': 'has_item', 'item_name': 'shiny button'},
        'xp_reward': 20
    },
    'get_chieftains_key': {
        'id': 'get_chieftains_key', 'name': "The Chieftain's Key",
        'description': "That large goblin chieftain likely keeps valuables locked away. Secure the key from his chamber.",
        'completion_criteria': {'type': 'has_item', 'item_name': 'iron key'},
        'xp_reward': 35
    },
    'scout_trash_pit': {
        'id': 'scout_trash_pit', 'name': "Hazardous Reconnaissance",
        'description': "Find out what lies in the trash pit area of the goblin warren.",
        'completion_criteria': {'type': 'reach_location', 'location_id': 'trash_pit'}, # Uses new criteria type
        'xp_reward': 20
    }
    # --- End Added Quests ---
}


# --- LLM System Prompt ---
# (Using light-hearted prompt)
SYSTEM_PROMPT = """You are a Dungeon Master (DM) running a fun, **light-hearted** fantasy adventure game for your friends. You are fair and impartial, but also **clever and funny**.
**Your Role:** Describe locations, objects, NPCs, and action results based *only* on provided context. Use descriptive, engaging, concise language (2-4 sentences). Maintain a light-hearted, witty tone. Refer to player as 'you'.
**Constraints:** Be fair. Do NOT decide player actions/feelings. Do NOT invent rules/items/NPCs/locations. Base narration *strictly* on 'Last Action Outcome' (hit/miss, success/fail). Do NOT repeat location descriptions unless player uses 'look'. Do NOT ask "What do you do next?".
**Response Format:** Only the DM's narrative description.
Current Situation:"""

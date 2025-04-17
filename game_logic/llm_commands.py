# game_logic/llm_commands.py
# Stores the list of commands that are handled directly by the LLM
# for narrative flavor, without specific game logic changes.
# Updated: Added 200+ commands based on US subcultures/groups from the last 50 years.
# Updated: Added category for "Brain Rot" / Modern Slang terms.
# Updated: Added category for "Musical Lovers".
# Updated: Added category for "Game Noobs / Common Verbs".
# Updated: Removed 'status' command to resolve conflict with canonical action.

# List of verbs that map to the LLM_ONLY marker in the action registry
LLM_ONLY_COMMANDS = [
    # --- Generic Flavor Actions ---
    "dance", "sing", "ponder", "scream", "laugh", "cry", "wave", "sleep",
    "jump", "listen", "smell", # Added earlier

    # --- Classic Text Adventure Commands ---
    "xyzzy", "plugh", "frobozz", "zork", "diagnose", "hello", "sailor", "sesame",

    # --- 80s Pop Culture Commands ---
    "flux", "ghostbusters", "macgyver", "grayskull", "thriller", "pacman",
    "radical", "gnarly", "bodacious",

    # --- Subculture Categories ---

    # Category: Hippies (Late 60s/70s)
    "peace", "love", "groovy", "incense", "tie-dye", "meditate", "protest", "commune", "tune-in", "drop-out",

    # Category: Punks (70s/80s)
    "pogo", "rebel", "safety-pin", "mohawk", "thrash", "sneer", "spit", "anarchy", "diy", "slam",

    # Category: Disco Dancers (70s)
    "boogie", "hustle", "strut", "funk", "groove", "spin", "pose", "shimmer", "platform", "leisure", # 'leisure' for leisure suit

    # Category: Yuppies (80s)
    "network", "power-lunch", "suspenders", "briefcase", "merger", "acquire", "cellphone", #"status", # Removed - Conflicts with canonical command
    "uptown", "schmooze",

    # Category: New Wavers (80s)
    "synthesizer", "angular", "quirky", "keytar", "skinny-tie", "gel", # "pose", # Duplicate
    "ironic", "devo", "bleep",

    # Category: Metalheads (80s/90s)
    "headbang", "shred", "riff", "metal", "leather", "denim", "horns", # 'horns' for devil horns sign
    "moshing", "solo", "amp",

    # Category: Grunge Fans (90s)
    "flannel", "angst", "slouch", "feedback", # guitar feedback
    "seattle", "mumble", "unplugged", "thrift", "overcast", "brood",

    # Category: Riot Grrrls (90s)
    "zine", "feminist", "shout", "marker", "manifesto", "empower", "underground", "kathleen", "bikini-kill", "fierce", # kathleen for Kathleen Hanna

    # Category: Dot-com Entrepreneurs (90s/00s)
    "ipo", "bubble", "burn-rate", "ping-pong", "stock-options", "disrupt", "synergy", "vaporware", "clickthrough", "iterate",

    # Category: Skaters (80s/90s/00s)
    "ollie", "kickflip", "grind", "shove-it", "vert", "ramp", "deck", "trucks", "bail", # "gnarly", # Duplicate

    # Category: Ravers (90s/00s)
    "glowstick", "trance", "techno", "plur", # Peace Love Unity Respect
    "warehouse", "sunrise", "hydrate", "kandi", "shuffle", "bass",

    # Category: Hip Hop Heads (80s-Present)
    "beatbox", "breakdance", "graffiti", "sample", "cypher", "freestyle", "turntable", "mic", "flow", "rhyme",

    # Category: Emo Kids (00s)
    "myspace", "sideswept", "tight-jeans", "heartache", "confessional", "acoustic", "journal", "eyeliner", "sensitive", "rawr",

    # Category: Hipsters (00s/10s)
    "irony", "fixed-gear", "vinyl", "artisan", "mustache", "obscure", "craft-beer", "fedora", "curated", "portland",

    # Category: Silicon Valley Techies (00s-Present)
    "agile", "scrum", "standup", #"disrupt", # Duplicate
    "unicorn", "ping", "server", "code", "deploy", "optimize",

    # Category: Preppers (Various)
    "bunker", "stockpile", "shtf", # S*** Hits The Fan
    "survival", "canned-goods", "generator", "off-grid", "barter", "bug-out", "cache",

    # Category: Foodies (00s-Present)
    "gourmet", "farm-to-table", "fusion", "umami", "deconstructed", "food-truck", "gastropub", "blog", "forage", "organic",

    # Category: Gamers (80s-Present)
    "level-up", "pwn", "noob", "respawn", "lag", #"grind", # Duplicate
    "cheat-code", "easter-egg", "console", "joystick",

    # Category: Environmentalists (70s-Present)
    "recycle", "conserve", "earth", "solar", "wind-power", "sustainable", "activism", "green", "carbon-footprint", "native",

    # Category: Cosplayers (00s-Present)
    "costume", "convention", "wig", "craft-foam", "worbla", "anime", "manga", "panel", "autograph", "transform",

    # Category: Brain Rot / Modern Slang (20s)
    "rizz", "gyat", "skibidi", "fanumtax", "sigma", "ohio", "delulu", "bet", "cap", "nocap",
    "sus", "bussin", "slay", "periodt", "giving", "ick", "simp", "yeet", "pog", "based",
    "mid", "glowup", "cook", "aura", "mog", "mewing", "brainrot", "goated", "touchgrass", "ate",
    "fr", "ngl", "ngl", "tbh", "iykyk", "stan", "shook", "basic", "bougie", # tbh, shook, stan, basic, bougie may be older but still used
    "cringe", "extra", "vibe", "yass", "zesty",

    # Category: Musical Lovers
    "encore", "intermission", "ovation", "spotlight", "chorus", "ballad", "showstopper", "matinee", "belt", "jazzhands",

    # Category: Game Noobs / Common Verbs
    "walk", "run", "move", "step", "crawl", "climb", "push", "pull", "touch", "open",
    "close", "read", "write", "eat", "drink", "throw", "wait", "help", "sit", "stand",

]

# Ensure all commands are lowercase and potentially remove duplicates from the whole list
# Using a set preserves uniqueness naturally if we load from it.
# For now, just ensure lowercase during list comprehension.
_unique_commands = set()
_final_list = []
for cmd in LLM_ONLY_COMMANDS:
    cmd_lower = cmd.lower()
    if cmd_lower not in _unique_commands:
        _unique_commands.add(cmd_lower)
        _final_list.append(cmd_lower)

LLM_ONLY_COMMANDS = _final_list
print(f"Loaded {len(LLM_ONLY_COMMANDS)} unique LLM_ONLY commands.")


# Optional: Convert to a set for faster lookups if needed elsewhere,
# but a list is fine for iterating during registry creation.
# LLM_ONLY_COMMANDS_SET = set(LLM_ONLY_COMMANDS)


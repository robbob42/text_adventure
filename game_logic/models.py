# game_logic/models.py
# Refactored for improved readability using standard Python indentation.
# Functionality remains identical. Uses STRING IDs for locations.

from typing import Dict, List, Optional, Any

# Expected Quest Dictionary Structure (defined in content.py, used by GameManager)
# { 'id': str, 'name': str, 'description': str, 'completion_criteria': Dict[str, Any], 'xp_reward': int }


class Character:
    """Represents the player character."""
    def __init__(self,
                 name: str,
                 hp: int,
                 max_hp: int,
                 current_location_id: str, # String ID
                 inventory: Optional[List[str]] = None,
                 skills: Optional[Dict[str, int]] = None,
                 xp: int = 0,
                 level: int = 1,
                 active_quests: Optional[List[str]] = None
                 ):
        """
        Initializes a Character instance.

        Args:
            name: The character's name.
            hp: The character's current health points.
            max_hp: The character's maximum health points.
            current_location_id: The string ID of the location the character is currently in.
            inventory: A list of item names the character is carrying. Defaults to empty list.
            skills: A dictionary mapping skill names (str) to values (int). Defaults to empty dict.
            xp: Current experience points. Defaults to 0.
            level: Current character level. Defaults to 1.
            active_quests: A list of IDs for currently active quests. Defaults to empty list.
        """
        self.name: str = name
        self.hp: int = hp
        self.max_hp: int = max_hp
        self.current_location_id: str = current_location_id
        self.inventory: List[str] = inventory if inventory is not None else []
        self.skills: Dict[str, int] = skills if skills is not None else {}
        self.xp: int = xp
        self.level: int = level
        self.active_quests: List[str] = active_quests if active_quests is not None else []

    def take_damage(self, damage: int):
        """Reduces character's HP by the damage amount, ensuring HP doesn't go below 0."""
        self.hp = max(0, self.hp - damage)

    def heal(self, amount: int):
        """Increases character's HP by the heal amount, ensuring HP doesn't exceed max_hp."""
        self.hp = min(self.max_hp, self.hp + amount)

    def is_alive(self) -> bool:
        """Checks if the character's HP is above 0."""
        return self.hp > 0

    def add_item(self, item_name: str):
        """Adds an item name to the character's inventory."""
        # Check case-insensitively if item already exists to avoid duplicates like 'Key' and 'key'
        if not self.has_item(item_name):
            self.inventory.append(item_name) # Add the item with its original casing
            print(f"Added '{item_name}' to inventory.") # Log for debugging
        else:
            print(f"'{item_name}' is already in inventory.") # Log for debugging

    def remove_item(self, item_name: str) -> bool:
        """Removes an item name from the character's inventory (case-insensitive). Returns True if successful."""
        item_to_remove = next((item for item in self.inventory if item.lower() == item_name.lower()), None)
        if item_to_remove:
            self.inventory.remove(item_to_remove)
            print(f"Removed '{item_to_remove}' from inventory.") # Log for debugging
            return True
        else:
            print(f"'{item_name}' not found in inventory.") # Log for debugging
            return False

    def has_item(self, item_name: str) -> bool:
        """Checks if the character has a specific item (case-insensitive)."""
        return any(item.lower() == item_name.lower() for item in self.inventory)

    def get_skill(self, skill_name: str) -> int:
        """Gets the value of a specific skill (case-insensitive), returning 0 if skill not possessed."""
        return self.skills.get(skill_name.lower(), 0)

    def add_xp(self, amount: int) -> bool:
        """Adds XP to the character and checks for level up. Returns True if leveled up."""
        needed_xp = 0 # Init fix
        if amount <= 0:
            return False # No XP gained, no level up possible

        self.xp += amount
        print(f"Gained {amount} XP. Total XP: {self.xp}")

        # Calculate XP needed for the *current* level before checking loop
        needed_xp = self.level * 100
        leveled_up = False

        # Check if current XP meets or exceeds threshold for *next* level
        # Use while loop to handle multiple level ups from one XP gain
        while self.xp >= needed_xp:
            self.level += 1
            # Option: Reset XP needed for level? self.xp -= needed_xp
            # Option: Keep cumulative XP? (Current implementation)
            print(f"*** Level Up! Reached Level {self.level}! ***")

            # Example level up benefits
            self.max_hp += 5
            self.hp = self.max_hp # Fully heal
            print(f"Max HP increased to {self.max_hp}. HP fully restored.")
            leveled_up = True

            # Recalculate needed_xp for the *new* level for the next loop check
            needed_xp = self.level * 100

        return leveled_up

    def add_quest(self, quest_id: str):
        """Adds a quest ID to the active quests if not already present."""
        # Check case-insensitively? Assuming quest IDs are consistent case.
        if quest_id not in self.active_quests:
            self.active_quests.append(quest_id)
            print(f"Quest added: '{quest_id}'")
        else:
            print(f"Quest '{quest_id}' is already active.")

    def remove_quest(self, quest_id: str):
        """Removes a quest ID from the active quests."""
        # Case-insensitive removal attempt? Assuming consistent case for IDs.
        if quest_id in self.active_quests:
            self.active_quests.remove(quest_id)
            print(f"Quest completed/removed: '{quest_id}'")
        else:
             print(f"Quest '{quest_id}' not found in active quests.")

    def has_quest(self, quest_id: str) -> bool:
        """Checks if a specific quest ID is active."""
        # Case-insensitive check? Assuming consistent case for IDs.
        return quest_id in self.active_quests

    def __str__(self) -> str:
        """String representation of the character's status."""
        inv_str = f"Inv: {self.inventory}" if self.inventory else "Inv: Empty"
        skills_str = f"Skills: {self.skills}" if self.skills else "Skills: None"
        quest_str = f"Quests: {len(self.active_quests)} active"
        xp_needed_display = self.level * 100
        # Format for better readability
        return (
            f"{self.name} (Lvl:{self.level} XP:{self.xp}/{xp_needed_display} | HP:{self.hp}/{self.max_hp})\n"
            f"  Location: '{self.current_location_id}'\n"
            f"  {inv_str}\n"
            f"  {skills_str}\n"
            f"  {quest_str}"
        )


class Location:
    """Represents a single location or room in the game."""
    def __init__(self,
                 id: str, # String ID
                 name: str,
                 description: str,
                 exits: Dict[str, str], # String ID values
                 npcs: List[Dict[str, Any]],
                 items: List[Dict[str, Any]]
                 ):
        """Initializes a Location instance using string IDs."""
        self.id: str = id
        self.name: str = name
        self.description: str = description
        self.exits: Dict[str, str] = exits if exits is not None else {} # Default to empty dict
        self.npcs: List[Dict[str, Any]] = npcs if npcs is not None else [] # Default to empty list
        self.items: List[Dict[str, Any]] = items if items is not None else [] # Default to empty list

    # --- Updated get_full_description (Using <br>) ---
    def get_full_description(self) -> str:
        """Returns a formatted description including NPCs, items, and exits with HTML line breaks."""
        full_desc = self.description # Start with the base room description

        # Add NPC info with preceding line breaks if NPCs exist
        if self.npcs:
            npc_descs = [npc.get('description', npc.get('name', 'an unknown figure')) for npc in self.npcs]
            # Use <br><br> for paragraph break in HTML
            full_desc += "<br><br>Present here: " + ", ".join(npc_descs) + "."

        # Add Item info with preceding line breaks if items exist
        if self.items:
            item_descs = [item.get('description', item.get('name', 'an unknown item')) for item in self.items]
             # Use <br><br> for paragraph break
            full_desc += "<br><br>You see here: " + ", ".join(item_descs) + "."
        else:
             # Use <br><br> for paragraph break
             full_desc += "<br><br>You don't see any loose items here."

        # Add Exits info with a preceding line break
        if self.exits:
            possible_exits = ", ".join(self.exits.keys())
             # Use <br><br> for paragraph break
            full_desc += f"<br><br>Exits are: {possible_exits}."
        else:
             # Use <br><br> for paragraph break
            full_desc += "<br><br>There are no obvious exits."
        # No need to strip here, browser handles extra whitespace around <br>
        return full_desc
    # --- End Update ---

    def get_exit(self, direction: str) -> Optional[str]:
        """Returns the string location ID for a given exit direction (case-insensitive), or None."""
        return self.exits.get(direction.lower())

    def add_item(self, item_dict: Dict[str, Any]):
        """Adds an item dictionary to the location's item list."""
        self.items.append(item_dict)
        print(f"Added item '{item_dict.get('name', 'unknown')}' to location {self.id}") # Log for debugging

    def remove_item(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Removes item dictionary by name (case-insensitive). Returns removed dict or None."""
        item_to_remove = next((item for item in self.items if item.get('name','').lower() == item_name.lower()), None)
        if item_to_remove:
            self.items.remove(item_to_remove)
            print(f"Removed '{item_to_remove.get('name')}' from location {self.id}") # Log for debugging
            return item_to_remove
        return None

    def find_item_by_name(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Finds item dictionary by name (case-insensitive)."""
        # Use a generator expression with next to find the first match or None
        return next((item for item in self.items if item.get('name','').lower() == item_name.lower()), None)

    def find_npc_by_name(self, npc_name: str) -> Optional[Dict[str, Any]]:
        """Finds NPC dictionary by name (case-insensitive substring match)."""
         # Use a generator expression with next to find the first match or None
        return next((npc for npc in self.npcs if npc_name.lower() in npc.get('name','').lower()), None)

    def __str__(self) -> str:
        """Simple string representation of the location."""
        return f"Location: {self.name} (ID: {self.id})"


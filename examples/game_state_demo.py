#!/usr/bin/env python3
"""Game State Management with MultiState Framework.

Demonstrates:
- Multiple active states (inventory, map, combat simultaneously)
- Hidden states (fog of war, menu occlusion)
- Dynamic transitions (discovered abilities, quest unlocks)
- Multi-target objectives (collect all gems, defeat all bosses)
- Temporal transitions (buff durations, cooldowns)
"""

import sys
import os
import time
import random
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Set, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multistate.manager import StateManager, StateManagerConfig
from multistate.dynamics.hidden_states import HiddenStateManager, OcclusionType
from multistate.pathfinding.multi_target import SearchStrategy


class GameElement(Enum):
    """Types of game elements."""
    MENU = "menu"
    WORLD = "world"
    COMBAT = "combat"
    INVENTORY = "inventory"
    QUEST = "quest"
    UI = "ui"
    

@dataclass
class GameContext:
    """Runtime game context."""
    player_level: int = 1
    discovered_areas: Set[str] = None
    active_quests: Set[str] = None
    inventory_items: Set[str] = None
    buffs: Dict[str, float] = None  # buff -> expiration time
    cooldowns: Dict[str, float] = None  # ability -> ready time
    
    def __post_init__(self):
        if self.discovered_areas is None:
            self.discovered_areas = set()
        if self.active_quests is None:
            self.active_quests = set()
        if self.inventory_items is None:
            self.inventory_items = set()
        if self.buffs is None:
            self.buffs = {}
        if self.cooldowns is None:
            self.cooldowns = {}


class RPGGameDemo:
    """Demonstrates MultiState in an RPG game context."""
    
    def __init__(self):
        """Initialize the game state system."""
        config = StateManagerConfig(
            default_search_strategy=SearchStrategy.DIJKSTRA,
            log_transitions=False
        )
        self.manager = StateManager(config)
        self.hidden_manager = HiddenStateManager()
        self.context = GameContext()
        self.current_time = 0.0
        
        self._setup_states()
        self._setup_static_transitions()
        
    def _setup_states(self):
        """Define all game states."""
        # Main game states
        self.manager.add_state("main_menu", "Main Menu", group="menu_screens")
        self.manager.add_state("settings", "Settings", group="menu_screens")
        self.manager.add_state("pause_menu", "Pause Menu", blocking=True)
        
        # World exploration states
        self.manager.add_state("overworld", "Overworld Map")
        self.manager.add_state("town", "Town")
        self.manager.add_state("dungeon", "Dungeon")
        self.manager.add_state("boss_room", "Boss Room")
        
        # Combat states
        self.manager.add_state("combat", "Combat Mode", blocking=True)
        self.manager.add_state("victory", "Victory Screen")
        self.manager.add_state("defeat", "Defeat Screen")
        
        # UI overlay states (can be active simultaneously)
        self.manager.add_state("inventory", "Inventory", group="ui_overlay")
        self.manager.add_state("map", "Map", group="ui_overlay")
        self.manager.add_state("quest_log", "Quest Log", group="ui_overlay")
        self.manager.add_state("character_stats", "Character Stats", group="ui_overlay")
        
        # Special states
        self.manager.add_state("dialogue", "NPC Dialogue", blocking=True)
        self.manager.add_state("cutscene", "Cutscene", blocking=True)
        self.manager.add_state("loading", "Loading Screen", blocking=True)
        
        # Hidden areas (discovered dynamically)
        self.manager.add_state("secret_room", "Secret Room")
        self.manager.add_state("treasure_vault", "Treasure Vault")
        
        # Status effect states
        self.manager.add_state("poisoned", "Poisoned Status")
        self.manager.add_state("buffed", "Buffed Status")
        self.manager.add_state("stealth", "Stealth Mode")
        
    def _setup_static_transitions(self):
        """Define compile-time known transitions."""
        # Menu transitions
        self.manager.add_transition(
            "start_game",
            from_states=["main_menu"],
            activate_states=["overworld"],
            exit_states=["main_menu"]
        )
        
        # Movement transitions
        self.manager.add_transition(
            "enter_town",
            from_states=["overworld"],
            activate_states=["town"],
            exit_states=["overworld"]
        )
        
        self.manager.add_transition(
            "enter_dungeon",
            from_states=["overworld"],
            activate_states=["dungeon"],
            exit_states=["overworld"]
        )
        
        self.manager.add_transition(
            "return_to_overworld",
            from_states=["town", "dungeon"],
            activate_states=["overworld"],
            exit_states=["town", "dungeon"]
        )
        
        # Combat transitions
        self.manager.add_transition(
            "enter_combat",
            from_states=["dungeon", "overworld"],
            activate_states=["combat"],
            path_cost=0.1  # Combat is forced, low cost
        )
        
        self.manager.add_transition(
            "win_combat",
            from_states=["combat"],
            activate_states=["victory"],
            exit_states=["combat"]
        )
        
        # UI toggles (can open multiple)
        for ui_state in ["inventory", "map", "quest_log", "character_stats"]:
            self.manager.add_transition(
                f"toggle_{ui_state}",
                from_states=["overworld", "town", "dungeon"],
                activate_states=[ui_state],
                path_cost=0.1
            )
            
            # Self-transition to close
            self.hidden_manager.register_self_transition(
                self.manager.get_state(ui_state),
                "close"
            )
    
    def discover_area(self, area: str):
        """Dynamically discover a new area."""
        if area not in self.context.discovered_areas:
            self.context.discovered_areas.add(area)
            
            # Generate dynamic transition to the discovered area
            if area == "secret_room":
                # Secret room discovered in dungeon
                self.manager.add_transition(
                    f"enter_{area}",
                    from_states=["dungeon"],
                    activate_states=[area],
                    path_cost=1.0
                )
                print(f"🗝️ Discovered {area}! New path available from dungeon.")
                
            elif area == "treasure_vault":
                # Treasure vault discovered after boss
                self.manager.add_transition(
                    f"enter_{area}",
                    from_states=["boss_room"],
                    activate_states=[area],
                    path_cost=0.5
                )
                print(f"💎 Discovered {area}! Accessible after defeating boss.")
    
    def add_temporal_buff(self, buff_name: str, duration: float):
        """Add a temporary buff with expiration."""
        expire_time = self.current_time + duration
        self.context.buffs[buff_name] = expire_time
        
        # Create temporal transition for buff expiration
        buff_state = self.manager.get_state("buffed")
        from multistate.dynamics.hidden_states import DynamicTransition
        
        expire_transition = DynamicTransition(
            id=f"expire_{buff_name}",
            name=f"Buff {buff_name} expires",
            from_states={buff_state},
            activate_states=set(),
            exit_states={buff_state},
            created_at=self.current_time,
            expires_at=expire_time,
            trigger_condition=f"Buff duration ended"
        )
        
        self.hidden_manager.add_dynamic_transition(expire_transition)
        print(f"⚡ Buff '{buff_name}' active for {duration} seconds")
    
    def set_ability_cooldown(self, ability: str, cooldown: float):
        """Set ability on cooldown."""
        ready_time = self.current_time + cooldown
        self.context.cooldowns[ability] = ready_time
        print(f"⏱️ Ability '{ability}' on cooldown for {cooldown} seconds")
    
    def demonstrate_fog_of_war(self):
        """Demonstrate fog of war occlusion."""
        print("\n" + "="*60)
        print("FOG OF WAR DEMONSTRATION")
        print("="*60)
        
        # Player is in overworld, some areas are hidden
        self.manager.activate_states({"overworld"})
        
        # Dungeon and boss room are occluded by fog
        dungeon_state = self.manager.get_state("dungeon")
        boss_state = self.manager.get_state("boss_room")
        
        # Create fog of war occlusion
        from multistate.dynamics.hidden_states import OcclusionRelation
        fog_occlusion = OcclusionRelation(
            covering_state=self.manager.get_state("overworld"),
            hidden_state=boss_state,
            occlusion_type=OcclusionType.LOGICAL,
            confidence=0.9
        )
        
        self.hidden_manager.occlusions.add(fog_occlusion)
        print("🌫️ Boss room hidden by fog of war")
        
        # Discover dungeon, reveals boss room
        print("\n📍 Exploring dungeon...")
        self.discover_area("dungeon")
        
        # Generate reveal transition
        reveal_trans = self.hidden_manager.generate_reveal_transition(
            covering_state=self.manager.get_state("overworld"),
            hidden_states={boss_state},
            current_time=self.current_time
        )
        print(f"✨ {reveal_trans.name}")
    
    def demonstrate_multi_target_quest(self):
        """Demonstrate multi-target pathfinding for quest objectives."""
        print("\n" + "="*60)
        print("MULTI-TARGET QUEST: Collect the Three Sacred Gems")
        print("="*60)
        
        # Define quest objectives as target states
        quest_targets = [
            "town",           # Gem of Wisdom
            "dungeon",        # Gem of Courage  
            "boss_room"       # Gem of Power
        ]
        
        # Add boss room transition
        self.manager.add_transition(
            "challenge_boss",
            from_states=["dungeon"],
            activate_states=["boss_room"],
            path_cost=3.0  # Boss is challenging
        )
        
        # Current position: overworld
        self.manager.activate_states({"overworld"})
        
        print("Current location: Overworld")
        print(f"Quest objectives: Visit {quest_targets} to collect gems\n")
        
        # Find optimal path to all objectives
        path = self.manager.find_path_to(quest_targets)
        
        if path:
            print("Optimal quest path found:")
            for i, transition in enumerate(path.transitions_sequence):
                print(f"  {i+1}. {transition.name} (cost: {transition.path_cost})")
            
            print(f"\nTotal cost: {path.total_cost}")
            print("This is more efficient than visiting each location separately!")
        
        # Compare with sequential approach
        print("\nSequential approach comparison:")
        total_sequential = 0
        current = self.manager.get_active_states()
        
        for target in quest_targets:
            single_path = self.manager.find_path_to([target])
            if single_path:
                print(f"  To {target}: cost {single_path.total_cost}")
                total_sequential += single_path.total_cost
        
        print(f"\nSequential total: {total_sequential}")
        print(f"Multi-target saves: {total_sequential - path.total_cost:.1f} cost units")
    
    def demonstrate_combat_with_abilities(self):
        """Demonstrate combat with cooldowns and buffs."""
        print("\n" + "="*60)
        print("COMBAT SYSTEM WITH ABILITIES")
        print("="*60)
        
        # Enter combat from dungeon
        self.manager.activate_states({"dungeon"})
        self.manager.execute_transition("enter_combat")
        
        print("⚔️ Entered combat!")
        print("\nAvailable abilities:")
        
        abilities = [
            ("Fireball", 3.0, None),
            ("Heal", 5.0, "regeneration"),
            ("Power Strike", 8.0, "strength")
        ]
        
        for ability, cooldown, buff in abilities:
            print(f"  • {ability} (cooldown: {cooldown}s)")
            if buff:
                print(f"    Grants buff: {buff}")
        
        # Use abilities
        print("\n🎯 Using abilities...")
        
        for ability, cooldown, buff in abilities:
            print(f"\nCasting {ability}!")
            self.set_ability_cooldown(ability, cooldown)
            
            if buff:
                self.add_temporal_buff(buff, cooldown * 0.75)
                self.manager.activate_states({"buffed"})
            
            # Simulate time passing
            self.current_time += 1.0
        
        # Check expired buffs
        print("\n⏰ Checking buff status...")
        for buff_name, expire_time in list(self.context.buffs.items()):
            if self.current_time >= expire_time:
                print(f"  {buff_name} has expired")
                del self.context.buffs[buff_name]
            else:
                remaining = expire_time - self.current_time
                print(f"  {buff_name} active for {remaining:.1f}s more")
    
    def demonstrate_menu_occlusion(self):
        """Demonstrate pause menu occluding game world."""
        print("\n" + "="*60)
        print("MENU OCCLUSION DEMONSTRATION")
        print("="*60)
        
        # Active game with multiple UI elements
        self.manager.activate_states({
            "overworld",
            "inventory",
            "map",
            "quest_log"
        })
        
        print("Active states before pause:")
        for state_id in sorted(self.manager.get_active_states()):
            print(f"  • {state_id}")
        
        # Open pause menu (blocking)
        print("\n⏸️ Opening pause menu...")
        self.manager.activate_states({"pause_menu"})
        
        # Detect occlusions
        active_states = self.manager.active_states
        occlusions = self.hidden_manager.detect_occlusion(active_states)
        
        print("\nOccluded states:")
        for occ in occlusions:
            if occ.covering_state.id == "pause_menu":
                print(f"  • {occ.hidden_state.id} (hidden by pause menu)")
        
        # Generate reveal transition for when pause closes
        hidden_states = {occ.hidden_state for occ in occlusions}
        if hidden_states:
            reveal = self.hidden_manager.generate_reveal_transition(
                covering_state=self.manager.get_state("pause_menu"),
                hidden_states=hidden_states,
                current_time=self.current_time
            )
            print(f"\n📋 Prepared: {reveal.name}")
    
    def run_full_demo(self):
        """Run complete game demo."""
        print("#"*60)
        print("# RPG GAME STATE MANAGEMENT DEMO")
        print("#"*60)
        
        # Start at main menu
        self.manager.activate_states({"main_menu"})
        print("\n🎮 Game started at main menu")
        
        # Start game
        self.manager.execute_transition("start_game")
        print("🌍 Entered game world")
        
        # Run demonstrations
        self.demonstrate_fog_of_war()
        self.demonstrate_multi_target_quest()
        self.demonstrate_combat_with_abilities()
        self.demonstrate_menu_occlusion()
        
        # Show final statistics
        print("\n" + "="*60)
        print("GAME STATE STATISTICS")
        print("="*60)
        
        complexity = self.manager.analyze_complexity()
        print(f"Total states: {complexity['num_states']}")
        print(f"Total transitions: {complexity['num_transitions']}")
        print(f"Dynamic transitions: {len(self.hidden_manager.dynamic_transitions)}")
        print(f"Active states: {complexity['active_states']}")
        print(f"Discovered areas: {len(self.context.discovered_areas)}")
        
        print("\n" + "#"*60)
        print("# KEY GAME CONCEPTS DEMONSTRATED")
        print("#"*60)
        print("""
1. FOG OF WAR: Areas hidden until discovered
2. MULTI-TARGET QUESTS: Optimal path to all objectives  
3. TEMPORAL ABILITIES: Cooldowns and buff durations
4. MENU OCCLUSION: Pause menu hides game world
5. DYNAMIC DISCOVERY: New areas create transitions
6. SIMULTANEOUS STATES: Inventory + map + combat
7. GROUP TRANSITIONS: UI overlays activate together
        """)


def main():
    """Run the game demo."""
    demo = RPGGameDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    main()
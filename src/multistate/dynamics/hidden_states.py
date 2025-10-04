"""Hidden states and dynamic transitions.

Implements Brobot's concept of hidden states where:
1. States can be covered/occluded by others at runtime
2. Closing the covering state reveals the hidden state
3. Transitions are created dynamically based on runtime state

This extends the formal model with:
- Occlusion relation: ω: S × S → {0,1} (state s1 occludes s2)
- Dynamic transition generation: f_dyn: Ξ → P(T)
- Self-transitions: t_self where from_states = activate_states
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum

from multistate.core.state import State
from multistate.transitions.transition import Transition


class OcclusionType(Enum):
    """Types of state occlusion."""
    
    MODAL = "modal"  # Fully blocks interaction (dialog)
    OVERLAY = "overlay"  # Partial occlusion (tooltip, dropdown)
    SPATIAL = "spatial"  # Physical overlap in UI
    LOGICAL = "logical"  # Application-defined precedence


@dataclass
class OcclusionRelation:
    """Represents one state occluding another.
    
    In the formal model: ω(s_covering, s_hidden) = 1
    """
    
    covering_state: State
    hidden_state: State
    occlusion_type: OcclusionType
    timestamp: float = 0.0  # When occlusion was detected
    confidence: float = 1.0  # For probabilistic occlusion
    
    def __hash__(self) -> int:
        return hash((self.covering_state.id, self.hidden_state.id))


@dataclass 
class DynamicTransition(Transition):
    """A transition created dynamically at runtime.
    
    Extends Transition with:
    - Runtime creation timestamp
    - Conditions that triggered creation
    - Lifetime (can expire)
    """
    
    created_at: float = 0.0
    expires_at: Optional[float] = None
    trigger_condition: str = ""  # What caused this transition to be created
    is_self_transition: bool = False  # Returns to same state
    
    def is_expired(self, current_time: float) -> bool:
        """Check if this dynamic transition has expired."""
        if self.expires_at is None:
            return False
        return current_time > self.expires_at


class HiddenStateManager:
    """Manages hidden states and dynamic transitions.
    
    This implements the theoretical extensions:
    1. Occlusion detection and tracking
    2. Dynamic transition generation
    3. Reveal transitions when covering states close
    """
    
    def __init__(self):
        """Initialize the hidden state manager."""
        # Track current occlusions: ω(s1, s2) = 1
        self.occlusions: Set[OcclusionRelation] = set()
        
        # Map from hidden state to its covering states
        self.hidden_to_covering: Dict[str, Set[str]] = {}
        
        # Map from covering state to hidden states it covers
        self.covering_to_hidden: Dict[str, Set[str]] = {}
        
        # Dynamic transitions created at runtime
        self.dynamic_transitions: Dict[str, DynamicTransition] = {}
        
        # Self-transition registry
        self.self_transitions: Dict[str, DynamicTransition] = {}
    
    def detect_occlusion(
        self,
        active_states: Set[State],
        spatial_info: Optional[Dict] = None
    ) -> Set[OcclusionRelation]:
        """Detect which states are occluded by others.
        
        This implements occlusion detection ω: S × S → {0,1}
        
        Args:
            active_states: Currently active states
            spatial_info: Optional spatial/z-order information
            
        Returns:
            Set of occlusion relations
        """
        new_occlusions = set()
        
        for s1 in active_states:
            for s2 in active_states:
                if s1 == s2:
                    continue
                
                # Check different types of occlusion
                if self._is_modal_occlusion(s1, s2):
                    new_occlusions.add(OcclusionRelation(
                        covering_state=s1,
                        hidden_state=s2,
                        occlusion_type=OcclusionType.MODAL
                    ))
                
                elif spatial_info and self._is_spatial_occlusion(s1, s2, spatial_info):
                    new_occlusions.add(OcclusionRelation(
                        covering_state=s1,
                        hidden_state=s2,
                        occlusion_type=OcclusionType.SPATIAL
                    ))
        
        return new_occlusions
    
    def _is_modal_occlusion(self, s1: State, s2: State) -> bool:
        """Check if s1 modally occludes s2.
        
        Modal states (like dialogs) occlude everything except:
        - Other modal states at same level
        - States explicitly marked as non-occludable
        """
        if not s1.blocking:  # Only blocking states can modally occlude
            return False
        
        # Check if s2 is in the blocks set of s1
        if s2.id in s1.blocks:
            return True
        
        # If s1 has no specific blocks, it blocks everything
        if not s1.blocks:
            return not s2.blocking  # Don't block other blocking states
        
        return False
    
    def _is_spatial_occlusion(
        self,
        s1: State,
        s2: State,
        spatial_info: Dict
    ) -> bool:
        """Check if s1 spatially occludes s2.
        
        Uses spatial information like:
        - Bounding boxes
        - Z-order/layer information
        - Overlap percentages
        """
        # Get spatial data
        s1_info = spatial_info.get(s1.id, {})
        s2_info = spatial_info.get(s2.id, {})
        
        # Check z-order
        z1 = s1_info.get('z_order', 0)
        z2 = s2_info.get('z_order', 0)
        
        if z1 <= z2:
            return False  # s1 is behind or at same level
        
        # Check bounding box overlap
        box1 = s1_info.get('bounds')
        box2 = s2_info.get('bounds')
        
        if box1 and box2:
            overlap = self._calculate_overlap(box1, box2)
            if overlap > 0.8:  # >80% overlap means occlusion
                return True
        
        return False
    
    def _calculate_overlap(self, box1: Dict, box2: Dict) -> float:
        """Calculate overlap percentage between two bounding boxes."""
        # Simple rectangle overlap calculation
        x_overlap = max(0, min(box1['right'], box2['right']) - max(box1['left'], box2['left']))
        y_overlap = max(0, min(box1['bottom'], box2['bottom']) - max(box1['top'], box2['top']))
        
        overlap_area = x_overlap * y_overlap
        box2_area = (box2['right'] - box2['left']) * (box2['bottom'] - box2['top'])
        
        if box2_area == 0:
            return 0
        
        return overlap_area / box2_area
    
    def update_occlusions(
        self,
        active_states: Set[State],
        spatial_info: Optional[Dict] = None
    ) -> Tuple[Set[OcclusionRelation], Set[OcclusionRelation]]:
        """Update occlusion tracking based on current state.
        
        Returns:
            (newly_occluded, newly_revealed) relations
        """
        # Detect current occlusions
        current_occlusions = self.detect_occlusion(active_states, spatial_info)
        
        # Find changes
        newly_occluded = current_occlusions - self.occlusions
        newly_revealed = self.occlusions - current_occlusions
        
        # Update tracking
        self.occlusions = current_occlusions
        
        # Update indices
        self.hidden_to_covering.clear()
        self.covering_to_hidden.clear()
        
        for occlusion in current_occlusions:
            hidden_id = occlusion.hidden_state.id
            covering_id = occlusion.covering_state.id
            
            if hidden_id not in self.hidden_to_covering:
                self.hidden_to_covering[hidden_id] = set()
            self.hidden_to_covering[hidden_id].add(covering_id)
            
            if covering_id not in self.covering_to_hidden:
                self.covering_to_hidden[covering_id] = set()
            self.covering_to_hidden[covering_id].add(hidden_id)
        
        return newly_occluded, newly_revealed
    
    def generate_reveal_transition(
        self,
        covering_state: State,
        hidden_states: Set[State],
        current_time: float = 0.0
    ) -> DynamicTransition:
        """Generate a transition to reveal hidden states.
        
        When a covering state is closed, this creates a transition
        to activate the previously hidden states.
        
        This implements: f_dyn(Ξ) → T_reveal
        """
        transition_id = f"reveal_{covering_state.id}_to_{'_'.join(s.id for s in hidden_states)}"
        
        return DynamicTransition(
            id=transition_id,
            name=f"Reveal hidden states under {covering_state.name}",
            from_states={covering_state},
            activate_states=hidden_states,
            exit_states={covering_state},
            path_cost=0.1,  # Reveal is nearly free
            created_at=current_time,
            trigger_condition=f"Closing {covering_state.id} reveals hidden states",
            is_self_transition=False
        )
    
    def generate_self_transition(
        self,
        state: State,
        action: str,
        current_time: float = 0.0
    ) -> DynamicTransition:
        """Generate a self-transition that returns to the same state.
        
        Self-transitions are useful for:
        - Refresh/reload actions
        - Retry operations
        - State validation
        - Clearing temporary UI elements
        
        Formally: t_self where from_states = activate_states = {s}
        """
        transition_id = f"self_{state.id}_{action}"
        
        return DynamicTransition(
            id=transition_id,
            name=f"{action} on {state.name}",
            from_states={state},
            activate_states={state},  # Return to same state
            exit_states=set(),  # Don't exit (or exit then re-enter)
            path_cost=0.5,  # Self-transitions are cheap
            created_at=current_time,
            trigger_condition=f"Self-transition for {action}",
            is_self_transition=True
        )
    
    def get_dynamic_transitions(
        self,
        active_states: Set[State],
        current_time: float = 0.0
    ) -> List[DynamicTransition]:
        """Get all currently valid dynamic transitions.
        
        This implements: f_dyn(Ξ) → P(T)
        
        Args:
            active_states: Current active states
            current_time: Current time for expiration checks
            
        Returns:
            List of valid dynamic transitions
        """
        valid_transitions = []
        
        # Check for reveal transitions
        for state in active_states:
            if state.id in self.covering_to_hidden:
                hidden_ids = self.covering_to_hidden[state.id]
                hidden_states = {s for s in active_states if s.id in hidden_ids}
                if hidden_states:
                    reveal = self.generate_reveal_transition(
                        state, hidden_states, current_time
                    )
                    valid_transitions.append(reveal)
        
        # Add non-expired dynamic transitions
        for trans in self.dynamic_transitions.values():
            if not trans.is_expired(current_time):
                valid_transitions.append(trans)
        
        # Add self-transitions
        valid_transitions.extend(self.self_transitions.values())
        
        return valid_transitions
    
    def register_self_transition(
        self,
        state: State,
        action: str,
        current_time: float = 0.0
    ) -> DynamicTransition:
        """Register a persistent self-transition for a state.
        
        Args:
            state: State that has the self-transition
            action: Action that triggers self-transition
            current_time: When this was registered
            
        Returns:
            The created self-transition
        """
        trans = self.generate_self_transition(state, action, current_time)
        self.self_transitions[trans.id] = trans
        return trans
    
    def add_dynamic_transition(
        self,
        transition: DynamicTransition
    ) -> None:
        """Add a dynamic transition.
        
        Args:
            transition: Dynamic transition to add
        """
        self.dynamic_transitions[transition.id] = transition
    
    def cleanup_expired(
        self,
        current_time: float
    ) -> int:
        """Remove expired dynamic transitions.
        
        Args:
            current_time: Current time for expiration checks
            
        Returns:
            Number of transitions removed
        """
        to_remove = []
        for tid, trans in self.dynamic_transitions.items():
            if trans.is_expired(current_time):
                to_remove.append(tid)
        
        for tid in to_remove:
            del self.dynamic_transitions[tid]
        
        return len(to_remove)
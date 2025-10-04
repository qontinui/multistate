"""Callback management for transitions."""

from typing import Callable, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class TransitionCallbacks:
    """Manages callbacks for transition phases.
    
    Callbacks are functions that get called during specific
    phases of transition execution.
    """
    
    # Outgoing callbacks: transition_id -> callback
    outgoing_callbacks: Dict[str, Callable] = field(default_factory=dict)
    
    # Incoming callbacks: (transition_id, state_id) -> callback  
    incoming_callbacks: Dict[tuple[str, str], Callable] = field(default_factory=dict)
    
    # Validation callbacks: transition_id -> callback
    validation_callbacks: Dict[str, Callable] = field(default_factory=dict)
    
    # Exit callbacks: (transition_id, state_id) -> callback
    exit_callbacks: Dict[tuple[str, str], Callable] = field(default_factory=dict)
    
    def register_outgoing(self, transition_id: str, callback: Callable) -> None:
        """Register outgoing phase callback.
        
        Args:
            transition_id: Transition to attach callback to
            callback: Function to call, should return bool
        """
        self.outgoing_callbacks[transition_id] = callback
    
    def register_incoming(self, transition_id: str, state_id: str, callback: Callable) -> None:
        """Register incoming phase callback for specific state.
        
        Args:
            transition_id: Transition to attach callback to
            state_id: State that will be activated
            callback: Function to call, should return bool
        """
        self.incoming_callbacks[(transition_id, state_id)] = callback
    
    def register_validation(self, transition_id: str, callback: Callable) -> None:
        """Register validation phase callback.
        
        Args:
            transition_id: Transition to attach callback to
            callback: Function to call, should return bool
        """
        self.validation_callbacks[transition_id] = callback
    
    def register_exit(self, transition_id: str, state_id: str, callback: Callable) -> None:
        """Register exit phase callback for specific state.
        
        Args:
            transition_id: Transition to attach callback to
            state_id: State that will be exited
            callback: Function to call, should return bool
        """
        self.exit_callbacks[(transition_id, state_id)] = callback
    
    def get_outgoing(self, transition_id: str) -> Optional[Callable]:
        """Get outgoing callback for transition."""
        return self.outgoing_callbacks.get(transition_id)
    
    def get_incoming(self, transition_id: str, state_id: str) -> Optional[Callable]:
        """Get incoming callback for state activation."""
        return self.incoming_callbacks.get((transition_id, state_id))
    
    def get_validation(self, transition_id: str) -> Optional[Callable]:
        """Get validation callback for transition."""
        return self.validation_callbacks.get(transition_id)
    
    def get_exit(self, transition_id: str, state_id: str) -> Optional[Callable]:
        """Get exit callback for state deactivation."""
        return self.exit_callbacks.get((transition_id, state_id))
    
    def execute_outgoing(self, transition_id: str, **kwargs) -> bool:
        """Execute outgoing callback if registered.
        
        Returns:
            True if callback succeeded or no callback
        """
        callback = self.get_outgoing(transition_id)
        if callback:
            try:
                return callback(**kwargs) is not False
            except Exception:
                return False
        return True
    
    def execute_incoming(self, transition_id: str, state_id: str, **kwargs) -> bool:
        """Execute incoming callback if registered.
        
        Returns:
            True if callback succeeded or no callback
        """
        callback = self.get_incoming(transition_id, state_id)
        if callback:
            try:
                return callback(**kwargs) is not False
            except Exception:
                return False
        return True
    
    def execute_validation(self, transition_id: str, **kwargs) -> bool:
        """Execute validation callback if registered.
        
        Returns:
            True if validation passed or no callback
        """
        callback = self.get_validation(transition_id)
        if callback:
            try:
                return callback(**kwargs) is not False
            except Exception:
                return False
        return True
    
    def execute_exit(self, transition_id: str, state_id: str, **kwargs) -> bool:
        """Execute exit callback if registered.
        
        Returns:
            True if callback succeeded or no callback
        """
        callback = self.get_exit(transition_id, state_id)
        if callback:
            try:
                return callback(**kwargs) is not False
            except Exception:
                return False
        return True
    
    def clear(self):
        """Clear all callbacks."""
        self.outgoing_callbacks.clear()
        self.incoming_callbacks.clear()
        self.validation_callbacks.clear()
        self.exit_callbacks.clear()
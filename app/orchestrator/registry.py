from abc import ABC, abstractmethod
from typing import Dict, List, Any, Type, Optional

class BaseAction(ABC):
    """
    Abstract base class for all Orchestrator Actions.
    """
    inputs: List[str] = []
    outputs: List[str] = []

    @abstractmethod
    async def run(self, ctx: Any) -> Dict[str, Any]:
        """
        Execute the action logic.
        """
        pass

class ActionRegistry:
    """
    Registry for Orchestrator Actions.
    """
    _registry: Dict[str, Type[BaseAction]] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(action_class: Type[BaseAction]):
            cls._registry[name] = action_class
            return action_class
        return decorator

    @classmethod
    def get_action(cls, name: str) -> Optional[Type[BaseAction]]:
        return cls._registry.get(name)

    @classmethod
    def list_actions(cls) -> List[str]:
        return list(cls._registry.keys())

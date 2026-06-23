import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, PrivateAttr, ConfigDict
from copy import deepcopy

class UserContext(BaseModel):
    """
    Titan-Lite User Context: Encapsulates user identity and environment.
    """
    user_id: str
    role: str = "BASIC" # BASIC, PRO, ADMIN
    storage_root: str = "docs/projects/titan-lite" # Default relative to project root

class ActionContext(BaseModel):
    """
    Titan-Lite ActionContext: The 'Truth Source' for Orchestrator execution.
    Provides namespace isolation and concurrency safety, now with User awareness.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    job_id: str
    ticker: str
    user: UserContext = Field(default_factory=lambda: UserContext(user_id="default_user"))
    payload_by_action: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Internal lock for thread-safe updates (Pydantic V2 Private Attribute)
    _lock: asyncio.Lock = PrivateAttr(default_factory=asyncio.Lock)

    async def write_output(self, action_name: str, outputs: Dict[str, Any]):
        """
        Writes Action outputs to the context with namespace isolation.
        """
        async with self._lock:
            # Physical isolation via deepcopy
            self.payload_by_action[action_name] = deepcopy(outputs)

    def get_output(self, action_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves output for a specific action.
        """
        return self.payload_by_action.get(action_name)

    def get_merged_payload(self) -> Dict[str, Any]:
        """
        Flattens all action outputs into a single dictionary (for legacy or downstream consumption).
        Note: Conflicts are resolved by the last action added, though Namespace isolation is preferred.
        """
        merged = {"symbol": self.ticker}
        for payload in self.payload_by_action.values():
            merged.update(payload)
        return merged

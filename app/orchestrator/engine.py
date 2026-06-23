import asyncio
import logging
from typing import Dict, Any, List
from orchestrator.registry import ActionRegistry
from orchestrator.context import ActionContext
from orchestrator.validator import WorkflowValidator
from orchestrator import actions  # Ensure actions are registered

logger = logging.getLogger("TitanOrchestrator")

class ShardLockManager:
    """
    Manages mutual exclusion for resources (e.g., tickers).
    """
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def get_lock(self, resource_id: str) -> asyncio.Lock:
        async with self._global_lock:
            if resource_id not in self._locks:
                self._locks[resource_id] = asyncio.Lock()
            return self._locks[resource_id]

class TitanWorkflowEngine:
    """
    Core execution engine for Orchestrator Tasks.
    Handles shard locking, context management, and step-by-step execution.
    """
    def __init__(self):
        self.lock_manager = ShardLockManager()

    async def execute(self, job_id: str, ticker: str, workflow_dsl: Dict[str, Any], user_ctx: Any = None, initial_payload: Dict[str, Any] = None) -> ActionContext:
        """
        Executes a workflow for a specific ticker.
        """
        # 1. Acquire Shard Lock for the ticker
        lock = await self.lock_manager.get_lock(ticker)
        
        async with lock:
            logger.info(f"[{job_id}] Starting workflow for {ticker}")
            
            # 2. Validate and Compile Workflow
            step_order = WorkflowValidator.validate_and_compile(workflow_dsl)
            steps_map = {step["id"]: step for step in workflow_dsl["steps"]}
            
            # 3. Initialize Context
            context = ActionContext(job_id=job_id, ticker=ticker, user=user_ctx) if user_ctx else ActionContext(job_id=job_id, ticker=ticker)
            
            # Inject initial payload if provided (accessible via ctx.get_output("input"))
            if initial_payload:
                await context.write_output("input", initial_payload)
            
            # 4. Sequential Step Execution
            try:
                for step_id in step_order:
                    step = steps_map[step_id]
                    mode = step.get("mode", "SEQUENTIAL")
                    actions_list = step.get("actions", [])
                    
                    logger.info(f"[{job_id}] Executing Step: {step_id} ({mode})")
                    
                    if mode == "PARALLEL":
                        # Parallel execution within a step
                        tasks = [self._run_action(act_name, context) for act_name in actions_list]
                        await asyncio.gather(*tasks)
                    else:
                        # Sequential execution within a step
                        for act_name in actions_list:
                            await self._run_action(act_name, context)
                
                logger.info(f"[{job_id}] Workflow completed successfully.")
                return context
                
            except Exception as e:
                logger.error(f"[{job_id}] Workflow failed at step {step_id}: {str(e)}")
                raise e

    async def _run_action(self, action_name: str, context: ActionContext):
        """
        Instantiates and runs a single action, then persists output to context.
        """
        action_cls = ActionRegistry.get_action(action_name)
        if not action_cls:
            raise ValueError(f"Action {action_name} not found in registry.")
        
        action_instance = action_cls()
        logger.debug(f"[{context.job_id}] Running action: {action_name}")
        
        # In a real scenario, we'd check cache here (Phase 2 optimization)
        outputs = await action_instance.run(context)
        
        # Persist to context with namespace isolation
        await context.write_output(action_name, outputs)

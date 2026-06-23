from typing import List, Dict, Set, Any
from collections import deque
from .registry import ActionRegistry

class InvalidWorkflowError(Exception):
    """Raised when a workflow fails validation."""
    pass

class WorkflowValidator:
    """
    Kahn's algorithm-based DAG validator and Data Pipeline contract checker.
    """
    
    @staticmethod
    def validate_and_compile(workflow_dsl: Dict[str, Any]) -> List[str]:
        """
        Validates the Workflow DSL for cycles and data contract closure.
        Returns a topologically sorted list of step IDs.
        """
        steps = workflow_dsl.get("steps", [])
        if not steps:
            raise InvalidWorkflowError("Workflow DSL has no steps.")

        defined_steps = {step["id"]: step for step in steps}
        
        # 1. Build Dependency Graph (Adjacency List) and In-Degree count
        graph: Dict[str, List[str]] = {step["id"]: [] for step in steps}
        in_degree: Dict[str, int] = {step["id"]: 0 for step in steps}
        
        for step in steps:
            depends_on = step.get("depends_on")
            if depends_on:
                if depends_on not in defined_steps:
                    raise InvalidWorkflowError(f"Step '{step['id']}' depends on non-existent step '{depends_on}'")
                graph[depends_on].append(step["id"])
                in_degree[step["id"]] += 1

        # 2. Topological Sort (Kahn's Algorithm) to detect cycles
        queue = deque([node for node, deg in in_degree.items() if deg == 0])
        order = []
        
        while queue:
            curr = queue.popleft()
            order.append(curr)
            for neighbor in graph[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
        if len(order) != len(steps):
            raise InvalidWorkflowError("Workflow contains a cycle (Circular Dependency detected)!")

        # 3. Data Pipeline Contract Check
        # Tracks available data assets in the pipeline at each stage
        provided_assets: Set[str] = {"symbol"} # Initial input
        
        for step_id in order:
            step = defined_steps[step_id]
            for action_name in step["actions"]:
                action_cls = ActionRegistry.get_action(action_name)
                if not action_cls:
                    raise InvalidWorkflowError(f"Action '{action_name}' is not registered.")
                
                # Static Check: Ensure all required inputs are present
                for req in action_cls.inputs:
                    if req not in provided_assets:
                        raise InvalidWorkflowError(
                            f"Step '{step_id}' Action [{action_name}] is missing required input: '{req}'"
                        )
                
                # Inject Action's produced outputs into the pipeline
                for out in action_cls.outputs:
                    provided_assets.add(out)
                    
        return order

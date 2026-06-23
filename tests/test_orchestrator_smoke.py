import asyncio
import pytest
from orchestrator.registry import ActionRegistry, BaseAction
from orchestrator.engine import TitanWorkflowEngine
from orchestrator.validator import InvalidWorkflowError

# --- Mock Actions ---

@ActionRegistry.register("FETCH_PRICE")
class FetchPriceAction(BaseAction):
    inputs = ["symbol"]
    outputs = ["price"]
    async def run(self, ctx):
        return {"price": 150.0}

@ActionRegistry.register("CALC_VOL")
class CalcVolAction(BaseAction):
    inputs = ["price"]
    outputs = ["volatility"]
    async def run(self, ctx):
        return {"volatility": 0.25}

@ActionRegistry.register("GENERATE_SIGNAL")
class GenerateSignalAction(BaseAction):
    inputs = ["price", "volatility"]
    outputs = ["signal"]
    async def run(self, ctx):
        return {"signal": "BUY"}

# --- Tests ---

@pytest.mark.asyncio
async def test_workflow_execution_success():
    engine = TitanWorkflowEngine()
    dsl = {
        "task_id": "SMOKE_TEST",
        "steps": [
            {"id": "s1", "actions": ["FETCH_PRICE"]},
            {"id": "s2", "actions": ["CALC_VOL"], "depends_on": "s1"},
            {"id": "s3", "actions": ["GENERATE_SIGNAL"], "depends_on": "s2"}
        ]
    }
    
    ctx = await engine.execute("job_001", "AAPL", dsl)
    
    assert ctx.ticker == "AAPL"
    assert ctx.get_output("FETCH_PRICE") == {"price": 150.0}
    assert ctx.get_output("CALC_VOL") == {"volatility": 0.25}
    assert ctx.get_output("GENERATE_SIGNAL") == {"signal": "BUY"}
    
    merged = ctx.get_merged_payload()
    assert merged["symbol"] == "AAPL"
    assert merged["price"] == 150.0
    assert merged["signal"] == "BUY"

@pytest.mark.asyncio
async def test_workflow_validation_cycle():
    engine = TitanWorkflowEngine()
    dsl = {
        "task_id": "CYCLE_TEST",
        "steps": [
            {"id": "s1", "actions": ["FETCH_PRICE"], "depends_on": "s2"},
            {"id": "s2", "actions": ["CALC_VOL"], "depends_on": "s1"}
        ]
    }
    with pytest.raises(InvalidWorkflowError, match="Circular Dependency detected"):
        await engine.execute("job_002", "TSLA", dsl)

@pytest.mark.asyncio
async def test_workflow_contract_failure():
    engine = TitanWorkflowEngine()
    dsl = {
        "task_id": "CONTRACT_TEST",
        "steps": [
            {"id": "s1", "actions": ["CALC_VOL"]} # Missing 'price' input
        ]
    }
    with pytest.raises(InvalidWorkflowError, match="missing required input: 'price'"):
        await engine.execute("job_003", "MSFT", dsl)

@pytest.mark.asyncio
async def test_parallel_execution():
    engine = TitanWorkflowEngine()
    dsl = {
        "task_id": "PARALLEL_TEST",
        "steps": [
            {"id": "s1", "actions": ["FETCH_PRICE", "CALC_VOL"], "mode": "PARALLEL"},
            {"id": "s2", "actions": ["GENERATE_SIGNAL"], "depends_on": "s1"}
        ]
    }
    # Note: CALC_VOL usually needs price, but for this mock test we'll allow it if price was in 'symbol'
    # Actually, let's fix the mock to use 'symbol' for CalcVol to make it valid
    @ActionRegistry.register("CALC_VOL_ASYNC")
    class CalcVolAsyncAction(BaseAction):
        inputs = ["symbol"]
        outputs = ["volatility"]
        async def run(self, ctx):
            await asyncio.sleep(0.1)
            return {"volatility": 0.30}

    dsl["steps"][0]["actions"] = ["FETCH_PRICE", "CALC_VOL_ASYNC"]
    
    ctx = await engine.execute("job_004", "GOOGL", dsl)
    assert ctx.get_output("CALC_VOL_ASYNC")["volatility"] == 0.30
